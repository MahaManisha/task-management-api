# Task Management API

## Project Description
Task Management API is a lightweight, scalable FastAPI application created as part of the Triton Internship project. This repository provides a modern Python backend structure for task management operations.

## Current Objective
Demonstrate production-ready modular Python software architecture by separating application logic into distinct, single-responsibility modules (models, schemas, services, utilities, and tests) while keeping `main.py` lightweight.

## Technologies Used
- **Language**: Python 3.13+
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (v0.141.1)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/) (v0.52.4)
- **Configuration**: `pydantic-settings` & `python-dotenv`

## Project Structure
```text
task-management-api/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── task.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── task.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── user_service.py
│   │   └── task_service.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py
│       └── helpers.py
│
├── tests/
│   ├── __init__.py
│   ├── test_users.py
│   ├── test_tasks.py
│   └── test_validators.py
│
├── requirements.txt
├── .gitignore
├── README.md
└── .env.example
```

## Modular Python Architecture

### Why Divide into Modules?
Monolithic single-file applications become difficult to test, maintain, and scale as team size and codebase complexity grow. Dividing code into modular Python components enforces the **Single Responsibility Principle (SRP)**, improves code readability, prevents code duplication, and enables independent unit testing of business logic.

### Module Responsibilities

1. **User Management**:
   - `app/models/user.py`: Internal `User` data structure entity.
   - `app/schemas/user.py`: Pydantic request/response schemas (`UserCreate`, `UserResponse`).
   - `app/services/user_service.py`: Core user business logic and in-memory persistence (`create_user`, `get_user`, `get_users`).
   - `tests/test_users.py`: Unit tests for user service operations.

2. **Task Management**:
   - `app/models/task.py`: Internal `Task` data structure entity.
   - `app/schemas/task.py`: Pydantic request/response schemas (`TaskCreate`, `TaskUpdate`, `TaskResponse`).
   - `app/services/task_service.py`: Core task business logic and in-memory persistence (`create_task`, `get_task`, `get_tasks`, `update_task_completion`).
   - `tests/test_tasks.py`: Unit tests for task service operations.

3. **Validation**:
   - `app/utils/validators.py`: Reusable validation functions for email format (`validate_email`) and task titles (`validate_task_title`).
   - `tests/test_validators.py`: Unit tests verifying validation logic.

4. **Utility Functions**:
   - `app/utils/helpers.py`: Reusable generic helpers (ISO timestamp generation via `get_current_timestamp` and sequential ID generation via `generate_id`).

5. **Lightweight Entry Point (`app/main.py`)**:
   - `app/main.py` serves strictly as the HTTP routing layer. It defines FastAPI endpoints, parses HTTP request payloads, delegates business logic directly to `user_service` and `task_service`, and maps exceptions to HTTP error status codes. Keeping `main.py` lightweight ensures that business logic remains decoupled from HTTP framework specifics.

## Setup & Installation

### 1. Prerequisites
Ensure Python 3.13 or higher is installed on your system.

### 2. Virtual Environment Setup
Create and activate a virtual environment:

- **Windows (PowerShell)**:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```

- **Linux / macOS**:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Install Dependencies
Install all required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```

## Running Tests

Run the unit test suite:
```bash
python -m unittest discover tests
```

## Running the Application

Start the local development server:
```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

### Key Endpoints
- **API Root**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Users Endpoints**:
  - `POST /users`: Create user
  - `GET /users`: List users
  - `GET /users/{user_id}`: Retrieve user
- **Tasks Endpoints**:
  - `POST /tasks`: Create task
  - `GET /tasks`: List tasks
  - `GET /tasks/{task_id}`: Retrieve task
  - `PATCH /tasks/{task_id}/complete`: Update task completion
- **Interactive Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Environment Variables

Environment settings are managed via `pydantic-settings` in `app/config.py`.

Copy `.env.example` to `.env` to configure local variables:
```bash
cp .env.example .env
```

### Security Warning
> **IMPORTANT**: Never commit real secrets, API keys, passwords, or `.env` files to Git repositories. Ensure `.env` remains listed in `.gitignore` at all times.
