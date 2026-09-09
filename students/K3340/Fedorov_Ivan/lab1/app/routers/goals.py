"""Финансовые цели пользователя (накопить N к дате)."""

from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlmodel import Session, select

from app.auth.dependencies import get_current_user
from app.models import Goal, GoalStatus, User
from app.schemas import GoalCreate, GoalRead, GoalUpdate
from db import get_session

router = APIRouter(prefix="/goals", tags=["Goals"])


def _get_own_goal(goal_id: int, session: Session, current_user: User) -> Goal:
    goal = session.get(Goal, goal_id)
    if goal is None or goal.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Цель не найдена")
    return goal


@router.get("/", response_model=List[GoalRead])
def list_goals(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> List[Goal]:
    return list(
        session.exec(select(Goal).where(Goal.user_id == current_user.id)).all()
    )


@router.get("/{goal_id}", response_model=GoalRead)
def get_goal(
    goal_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Goal:
    return _get_own_goal(goal_id, session, current_user)


@router.post("/", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def create_goal(
    data: GoalCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Goal:
    goal = Goal(**data.model_dump(), user_id=current_user.id)
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


@router.patch("/{goal_id}", response_model=GoalRead)
def update_goal(
    goal_id: int,
    data: GoalUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Goal:
    goal = _get_own_goal(goal_id, session, current_user)
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(goal, field, value)
    if "status" not in updates:
        goal.status = (
            GoalStatus.reached
            if goal.current_amount >= goal.target_amount
            else GoalStatus.active
        )
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


@router.post("/{goal_id}/deposit", response_model=GoalRead)
def deposit_to_goal(
    goal_id: int,
    amount: float = Body(..., embed=True, gt=0),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Goal:
    """Положить сумму в цель; при достижении цели статус меняется автоматически."""
    goal = _get_own_goal(goal_id, session, current_user)
    goal.current_amount += amount
    if goal.current_amount >= goal.target_amount:
        goal.status = GoalStatus.reached
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    goal = _get_own_goal(goal_id, session, current_user)
    session.delete(goal)
    session.commit()
