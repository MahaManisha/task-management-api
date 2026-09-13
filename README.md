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
│       ├── helpers.py
│       └── file_iterator.py
│
├── tests/
│   ├── __init__.py
│   ├── test_users.py
│   ├── test_tasks.py
│   ├── test_validators.py
│   └── test_file_iterator.py
│
├── scripts/
│   └── memory_benchmark.py
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

6. **D2 — Iterators, Generators & Lazy Evaluation (`app/utils/file_iterator.py`)**:
   - `FileBatchIterator`: Custom class implementing `__iter__` and `__next__` to stream folder file batches lazily.
   - `read_files_in_batches`: Generator function using `yield` for lazy batch retrieval.
   - `scripts/memory_benchmark.py`: Benchmark script measuring memory using `tracemalloc`.

## D2 — Iterators, Generators & Memory-Efficient Data Handling

### Overview
D2 introduces custom Python iterators and generator functions designed for memory-efficient batch processing of large dataset folders. Instead of loading an entire dataset into RAM at once, data is fetched lazily batch by batch.

### Key Concepts

1. **What is an Iterator?**
   An iterator in Python is an object that represents a stream of data. It implements Python's **Iterator Protocol**, producing one item at a time when requested, thereby enabling memory-efficient data processing over large datasets.

2. **Usage of `__iter__` and `__next__`**:
   - `__iter__(self)` returns the iterator object itself (`self`). It allows the class instance to be used directly in `for` loops or passed to `iter()`.
   - `__next__(self)` fetches the next batch of items. When no items remain, it raises the standard `StopIteration` exception to gracefully signal the end of iteration.

3. **Why the Implementation is Lazy**:
   - **Eager Evaluation** (`load_all_files`): Reads every file in a target directory into memory upfront in a single list, causing memory consumption to grow linearly $O(N)$ with dataset size.
   - **Lazy Evaluation** (`FileBatchIterator` & `read_files_in_batches`): Utilizes `os.scandir` to traverse directory entries without loading file contents into RAM upfront. File contents are read only when a batch is requested, keeping peak memory usage bounded $O(B)$ by the batch size $B$.

4. **How Batch Processing Works**:
   - The user initializes `FileBatchIterator(folder_path, batch_size=100)`.
   - During each iteration step (`next()`), up to `batch_size` files are opened and read.
   - The batch list `[(filename, content), ...]` is yielded/returned to the caller.
   - Once the caller finishes processing a batch, Python's garbage collector frees the memory allocated for that batch before the next batch is fetched.

5. **Memory Usage Measurement Methodology**:
   Memory usage was measured using Python's standard library `tracemalloc` module (`scripts/memory_benchmark.py`). For each dataset size (100, 1,000, and 10,000 files of 1 KB each), `tracemalloc.start()` and `tracemalloc.get_traced_memory()` recorded the peak memory allocated during processing.

### Measured Memory Benchmark Results

The benchmark was executed using `python scripts/memory_benchmark.py` with a fixed batch size of 100 files (~1 KB per file):

| Dataset Size (Files) | Eager Peak Memory (KB) | Lazy Iterator Peak Memory (KB) | Generator Peak Memory (KB) | Memory Saving |
| :--- | :--- | :--- | :--- | :--- |
| **100** | 130.67 KB | 127.11 KB | 126.09 KB | ~3% |
| **1,000** | 1,193.15 KB | 246.03 KB | 236.27 KB | ~79% |
| **10,000** | 11,566.73 KB (~11.57 MB) | 247.35 KB (~0.25 MB) | 244.17 KB (~0.24 MB) | **~97.9%** |

**Observation**: As the dataset size increased from 100 to 10,000 files, eager loading memory consumption grew linearly $O(N)$ by over 88x. In contrast, lazy iterator and generator memory usage remained flat and bounded at ~245 KB $O(B)$, confirming memory stability regardless of dataset size.

### Running the Memory Benchmark

To run the memory benchmark script:
```bash
python scripts/memory_benchmark.py
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
