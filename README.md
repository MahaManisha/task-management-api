# Task Management API

## Project Description
Task Management API is a lightweight, scalable FastAPI application created as part of the Triton Internship project. This repository provides a modern Python backend structure for task management operations.

> **Note**: This repository currently represents the initial project setup and baseline application foundation. Core task management features (models, schemas, and endpoints) will be implemented in upcoming development phases.

## Current Objective
The goal of this phase is to establish a verified, modular Python package structure with ASGI application setup (`FastAPI` + `Uvicorn`), configuration management via `pydantic-settings`, environment isolation, and version control configuration (`.gitignore`).

## Technologies Used
- **Language**: Python 3.13+
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (v0.141.1)
- **ASGI Server**: [Uvicorn](https://www.uvicorn.org/) (v0.52.4)
- **Configuration**: `pydantic-settings` & `python-dotenv`

## Project Structure
```text
task-management-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   └── __init__.py
│   ├── schemas/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   └── utils/
│       └── __init__.py
├── tests/
│   └── __init__.py
├── requirements.txt
├── .gitignore
├── README.md
└── .env.example
```

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

## Running the Application

Start the local development server with auto-reloading enabled:
```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

### Key Endpoints
- **API Root**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) - Basic welcome and health check response.
- **Interactive API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative API Docs (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Environment Variables

Environment settings are loaded via `pydantic-settings` in `app/config.py`.

To set custom environment settings:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Adjust environment settings in `.env` as needed.

### Security Warning
> **IMPORTANT**: Never commit real secrets, API keys, passwords, or `.env` files to Git repositories. Ensure `.env` remains listed in `.gitignore` at all times.

## Git Workflow
1. Development should take place on dedicated feature branches (e.g., `feature/project-setup`).
2. Verify that untracked secrets or `.venv/` directories are not staged prior to committing:
   ```bash
   git status
   ```
3. Commit clean code changes with descriptive messages:
   ```bash
   git add .
   git commit -m "feat: initial project setup and FastAPI ASGI configuration"
   ```
