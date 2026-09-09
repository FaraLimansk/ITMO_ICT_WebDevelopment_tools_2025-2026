# Лабораторная работа 1 — сервис управления личными финансами

Серверное приложение на **FastAPI + SQLModel + PostgreSQL + Alembic** с JWT-аутентификацией. Проект покрывает требования практик 1.1–1.3 и задания на 9 баллов.

## Реализовано

- 8 ORM-таблиц: `users`, `accounts`, `categories`, `transactions`, `budgets`, `goals`, `tags`, `transaction_tag`;
- one-to-many: пользователь → счета/категории/транзакции/бюджеты/цели/теги, счёт → транзакции, категория → транзакции/бюджеты;
- many-to-many: транзакции ↔ теги;
- ассоциативная сущность `transaction_tag` с полями `note` и `added_at`;
- типизированные CRUD API, вложенные ответы, фильтры и пагинация;
- JWT-аутентификация и изоляция данных пользователей;
- пересчёт баланса, контроль бюджета, финансовые цели и отчёт по периоду;
- миграции Alembic с `upgrade` и `downgrade`;
- интеграционные тесты;
- запуск PostgreSQL и API через Docker Compose.

Подробное соответствие заданиям: [PRACTICES.md](PRACTICES.md).

## Структура

```text
lab1/
├── app/
│   ├── auth/                  # JWT, пароли, зависимости
│   ├── routers/               # роутеры предметных областей
│   ├── models.py              # ORM-модели SQLModel
│   └── schemas.py             # схемы запросов и ответов
├── migrations/
│   ├── versions/              # миграции Alembic
│   └── env.py
├── tests/                     # интеграционные API-тесты
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── db.py
├── main.py
└── requirements.txt
```

## Быстрый запуск через Docker

Требуются Docker Desktop и Docker Compose.

```bash
cd lab1
cp .env.example .env
# Обязательно замените SECRET_KEY в .env

docker compose up --build
```

После запуска:

- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI: <http://127.0.0.1:8000/openapi.json>
- Health-check: <http://127.0.0.1:8000/health>

Контейнер API автоматически выполняет `alembic upgrade head` перед стартом.

Остановка:

```bash
docker compose down
# Удалить также данные PostgreSQL: docker compose down -v
```

## Локальный запуск в VS Code

### 1. Виртуальное окружение

```bash
cd lab1
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

### 2. PostgreSQL

Создайте БД `finance_db` и проверьте строку подключения в `.env`:

```dotenv
DB_ADMIN=postgresql+psycopg2://postgres:postgres@localhost:5432/finance_db
SECRET_KEY=replace-with-a-long-random-secret
SQL_ECHO=false
```

Можно запустить только БД в Docker, а API — из VS Code:

```bash
docker compose up -d db
alembic upgrade head
uvicorn main:app --reload
```

### 3. Миграции

```bash
alembic current
alembic history
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

Создание новой миграции после изменения моделей:

```bash
alembic revision --autogenerate -m "описание изменения"
alembic upgrade head
```

### 4. Тесты и статическая проверка

```bash
pytest
ruff check .
python -m compileall -q .
```

Тесты используют временную SQLite in-memory БД только для быстрого тестового прогона. Рабочее приложение и миграции настроены на PostgreSQL.

## Проверка API в Swagger

1. Выполните `POST /auth/register`.
2. Нажмите **Authorize** и введите `username` и `password` — Swagger отправит их на `/auth/token`.
3. Создайте счёт через `POST /accounts/`.
4. Создайте категорию или возьмите одну из базовых через `GET /categories/`.
5. Создайте транзакцию через `POST /transactions/`.
6. Создайте тег и привяжите его к транзакции.
7. Проверьте вложенные ответы `GET /accounts/{id}`, `GET /transactions/{id}`, `GET /tags/{id}`.
8. Создайте бюджет и откройте `GET /budgets/{id}/status`.
9. Получите отчёт через `GET /reports/summary`.

## Основные эндпоинты

- `/auth` — регистрация и вход;
- `/users` — профиль пользователя;
- `/accounts` — CRUD счетов;
- `/categories` — CRUD категорий;
- `/transactions` — CRUD транзакций, фильтры, вложенные связи;
- `/tags` — CRUD тегов и управление many-to-many связью;
- `/budgets` — CRUD бюджетов и контроль превышения;
- `/goals` — CRUD финансовых целей и пополнение;
- `/reports/summary` — агрегированный отчёт за период.

## Коммиты практик

```text
practice 1.1: add SQLModel domain models and relationships
practice 1.2: implement typed CRUD API and nested responses
practice 1.3: configure Alembic and PostgreSQL deployment
```

Ветка проекта: `lab1`.
