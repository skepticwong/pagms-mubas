from typing import Optional

from models import db, Task


class TaskRepository:
    """Persistence helpers for workflow tasks."""

    @staticmethod
    def find_by_id(task_id: int) -> Optional[Task]:
        return Task.query.get(task_id)

    @staticmethod
    def list_for_user(user_id: int) -> list[Task]:
        return Task.query.filter_by(assigned_to=user_id).all()

    @staticmethod
    def list_for_grant(grant_id: int) -> list[Task]:
        return Task.query.filter_by(grant_id=grant_id).all()

    @staticmethod
    def save(task: Task) -> Task:
        db.session.add(task)
        db.session.commit()
        return task
