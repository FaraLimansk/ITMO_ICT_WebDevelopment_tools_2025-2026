"""Интеграционные тесты основных пользовательских сценариев API."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

import db
from main import app

TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
db.engine = TEST_ENGINE


@pytest.fixture(autouse=True)
def clean_database() -> Generator[None, None, None]:
    SQLModel.metadata.drop_all(TEST_ENGINE)
    SQLModel.metadata.create_all(TEST_ENGINE)
    yield
    SQLModel.metadata.drop_all(TEST_ENGINE)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def register_and_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={
            "username": "student",
            "email": "student@example.com",
            "password": "secret123",
        },
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/auth/login",
        json={"username": "student", "password": "secret123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_and_auth(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "healthy"}
    headers = register_and_headers(client)
    profile = client.get("/users/me/full", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["username"] == "student"
    assert len(profile.json()["categories"]) == 4


def test_crud_nested_relations_and_reports(client: TestClient) -> None:
    headers = register_and_headers(client)

    account = client.post(
        "/accounts/",
        headers=headers,
        json={"name": "Карта", "currency": "rub", "balance": 1000},
    )
    assert account.status_code == 201, account.text
    account_id = account.json()["id"]
    assert account.json()["currency"] == "RUB"

    category = client.post(
        "/categories/",
        headers=headers,
        json={"name": "Книги", "kind": "expense"},
    )
    assert category.status_code == 201, category.text
    category_id = category.json()["id"]

    transaction = client.post(
        "/transactions/",
        headers=headers,
        json={
            "amount": 250,
            "type": "expense",
            "comment": "Учебник",
            "spent_at": "2026-09-09",
            "account_id": account_id,
            "category_id": category_id,
        },
    )
    assert transaction.status_code == 201, transaction.text
    transaction_id = transaction.json()["id"]

    tag = client.post("/tags/", headers=headers, json={"name": "Учёба"})
    assert tag.status_code == 201, tag.text
    tag_id = tag.json()["id"]

    link = client.post(
        f"/tags/transaction/{transaction_id}/tag/{tag_id}",
        headers=headers,
        json={"note": "Материалы к лабораторной"},
    )
    assert link.status_code == 201, link.text

    nested_tx = client.get(f"/transactions/{transaction_id}", headers=headers)
    assert nested_tx.status_code == 200
    assert nested_tx.json()["account"]["name"] == "Карта"
    assert nested_tx.json()["category"]["name"] == "Книги"
    assert nested_tx.json()["tags"][0]["name"] == "Учёба"

    nested_account = client.get(f"/accounts/{account_id}", headers=headers)
    assert len(nested_account.json()["transactions"]) == 1
    assert nested_account.json()["balance"] == 750

    budget = client.post(
        "/budgets/",
        headers=headers,
        json={
            "limit_amount": 200,
            "period_start": "2026-09-01",
            "period_end": "2026-09-30",
            "category_id": category_id,
        },
    )
    assert budget.status_code == 201, budget.text
    budget_id = budget.json()["id"]

    budget_status = client.get(f"/budgets/{budget_id}/status", headers=headers)
    assert budget_status.json()["is_exceeded"] is True
    assert budget_status.json()["spent_amount"] == 250

    report = client.get(
        "/reports/summary?date_from=2026-09-01&date_to=2026-09-30",
        headers=headers,
    )
    assert report.status_code == 200
    assert report.json()["total_expense"] == 250
    assert report.json()["by_category"][0]["category_name"] == "Книги"

    assert client.patch(
        f"/tags/{tag_id}", headers=headers, json={"name": "Образование"}
    ).status_code == 200
    assert client.delete(
        f"/tags/transaction/{transaction_id}/tag/{tag_id}", headers=headers
    ).status_code == 204
    assert client.delete(f"/transactions/{transaction_id}", headers=headers).status_code == 204


def test_rejects_foreign_objects_and_invalid_business_rules(client: TestClient) -> None:
    first_headers = register_and_headers(client)
    account_id = client.post(
        "/accounts/", headers=first_headers, json={"name": "Счёт"}
    ).json()["id"]

    register = client.post(
        "/auth/register",
        json={
            "username": "other",
            "email": "other@example.com",
            "password": "secret123",
        },
    )
    assert register.status_code == 201
    login = client.post(
        "/auth/login", json={"username": "other", "password": "secret123"}
    )
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    response = client.post(
        "/transactions/",
        headers=other_headers,
        json={"amount": 100, "type": "expense", "account_id": account_id},
    )
    assert response.status_code == 400

    income_category = next(
        item
        for item in client.get("/categories/", headers=first_headers).json()
        if item["kind"] == "income"
    )
    response = client.post(
        "/transactions/",
        headers=first_headers,
        json={
            "amount": 100,
            "type": "expense",
            "account_id": account_id,
            "category_id": income_category["id"],
        },
    )
    assert response.status_code == 400
