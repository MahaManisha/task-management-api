from typing import Dict, List, Optional
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.utils.validators import validate_task_title
from app.utils.helpers import generate_id

# In-memory task database
_tasks_db: Dict[int, Task] = {}


def create_task(task_in: TaskCreate) -> Task:
    """Create a new task after validating title."""
    if not validate_task_title(task_in.title):
        raise ValueError("Invalid task title. Title must be between 1 and 100 characters.")

    task_id = generate_id(_tasks_db)
    new_task = Task(
        id=task_id,
        title=task_in.title.strip(),
        description=task_in.description,
        completed=task_in.completed,
        user_id=task_in.user_id,
    )
    _tasks_db[task_id] = new_task
    return new_task


def get_task(task_id: int) -> Optional[Task]:
    """Retrieve a task by ID."""
    return _tasks_db.get(task_id)


def get_tasks() -> List[Task]:
    """Retrieve all tasks."""
    return list(_tasks_db.values())


def update_task_completion(task_id: int, completed: bool) -> Optional[Task]:
    """Update completion status of a task."""
    task = _tasks_db.get(task_id)
    if not task:
        return None
    task.completed = completed
    return task


def update_task(task_id: int, task_in: TaskUpdate) -> Optional[Task]:
    """Update task attributes."""
    task = _tasks_db.get(task_id)
    if not task:
        return None

    if task_in.title is not None:
        if not validate_task_title(task_in.title):
            raise ValueError("Invalid task title.")
        task.title = task_in.title.strip()

    if task_in.description is not None:
        task.description = task_in.description

    if task_in.completed is not None:
        task.completed = task_in.completed

    return task


def clear_tasks_db() -> None:
    """Clear in-memory task database."""
    _tasks_db.clear()
