from typing import List
from fastapi import FastAPI, HTTPException, status

from app.config import settings
from app.schemas.user import UserCreate, UserResponse
from app.schemas.task import TaskCreate, TaskResponse
from app.services import user_service, task_service

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
)


@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}


# --- User Endpoints ---

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(user_in: UserCreate):
    try:
        return user_service.create_user(user_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/users", response_model=List[UserResponse])
def get_users_endpoint():
    return user_service.get_users()


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user_endpoint(user_id: int):
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# --- Task Endpoints ---

@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task_endpoint(task_in: TaskCreate):
    try:
        return task_service.create_task(task_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.get("/tasks", response_model=List[TaskResponse])
def get_tasks_endpoint():
    return task_service.get_tasks()


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task_endpoint(task_id: int):
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}/complete", response_model=TaskResponse)
def update_task_completion_endpoint(task_id: int, completed: bool = True):
    task = task_service.update_task_completion(task_id, completed)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task