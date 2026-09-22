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
│   │   ├── task_service.py
│   │   ├── pipeline.py
│   │   └── pipeline_stages.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── validators.py
│       ├── helpers.py
│       ├── decorators.py
│       ├── context_managers.py
│       └── cache.py
│
├── scripts/
│   ├── config_validation_demo.py
│   └── decorators_demo.py
│
├── tests/
│   ├── __init__.py
│   ├── test_users.py
│   ├── test_tasks.py
│   ├── test_validators.py
│   ├── test_pipeline.py
│   ├── test_config.py
│   ├── test_decorators.py
│   ├── test_context_manager.py
│   └── test_cache.py
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

6. **D3 — Pipeline & Object-Oriented Architecture (`app/services/pipeline.py`, `app/services/pipeline_stages.py`)**:
   - `Step`: Abstract base class enforcing step processing contract (`process`).
   - `TaskValidationStep`, `TaskTransformationStep`, `TaskProcessingStep`: Concrete step implementations.
   - `Pipeline`: Sequential step execution engine using composition over inheritance.
   - `tests/test_pipeline.py`: Comprehensive test suite verifying step interchangeability, runtime swapping, and extensibility.

7. **D4 — Type Hints & Pydantic for Configuration (`app/config.py`, `scripts/config_validation_demo.py`, `tests/test_config.py`)**:
   - `PipelineConfig`: Pydantic `BaseModel` enforcing runtime validation for pipeline settings.
   - `ExecutionMode`, `ExecutionDevice`: Enums restricting execution choices.
   - `ImageSize`: Nested Pydantic model validating pixel dimensions.
   - `DataclassPipelineConfig`: Standard Python dataclass demonstrating the contrast between static types and Pydantic runtime validation.
   - `scripts/config_validation_demo.py`: Executable demo script showing valid vs invalid configuration validation errors.
   - `tests/test_config.py`: Unit test suite verifying runtime configuration validation.

8. **D5 — Decorators, Context Managers & Caching (`app/utils/decorators.py`, `app/utils/context_managers.py`, `app/utils/cache.py`)**:
   - `@timeit`, `@retry`: Reusable custom decorators for performance logging and automated failure retries.
   - `PipelineResourceContext`, `managed_pipeline_file`: Context managers ensuring guaranteed resource acquisition and cleanup.
   - `get_pipeline_step_config`: Deterministic pipeline configuration lookup with `functools.lru_cache`.
   - `scripts/decorators_demo.py`: Executable demonstration script.
   - `tests/test_decorators.py`, `tests/test_context_manager.py`, `tests/test_cache.py`: Comprehensive unit tests.

## D3 — OOP for Pipelines: Composition Over Inheritance

### Overview
D3 implements Object-Oriented Programming (OOP) principles to construct a flexible task processing pipeline (`app/services/pipeline.py` & `app/services/pipeline_stages.py`) using **Composition Over Inheritance**. The `Pipeline` class contains interchangeable `Step` objects that execute sequentially.

### Data Flow
Data flows sequentially through discrete steps, where the output of one step serves directly as input to the next:

```text
Task Input → Step 1 → Step 2 → Step 3 → Output
```

### Purpose of Step Interface & Task Steps
1. **`Step`**: Abstract base class (`abc.ABC`) defining the shared `process(data: Dict[str, Any]) -> Dict[str, Any]` interface with `@abstractmethod`. Direct instantiation is prevented.
2. **`TaskValidationStep`**: Validates task title presence and length (1–100 chars), reusing `validate_task_title`.
3. **`TaskTransformationStep`**: Normalizes task title whitespace and ensures default completion status (`completed=False`).
4. **`TaskProcessingStep`**: Enriches task data with processing metadata (`status="PROCESSED"`, `processed=True`).

### Composition Over Inheritance
- **Composition (`has-a`)**: The `Pipeline` class maintains a collection of `Step` objects (`self._steps`). It does not inherit from `Step` nor do steps inherit from `Pipeline`.
- **Why Avoid Deep Inheritance Chains?**: Deep inheritance hierarchies create tight coupling, brittle code, and unintended side-effects when parent classes change. Composition keeps steps decoupled and independent.
- **Runtime Step Swapping**: Because `Pipeline` interacts only with the abstract `Step` interface, any `Step` can be swapped for another at runtime without modifying the `Pipeline` class:
  ```python
  # Pipeline A uses TaskTransformationStep
  pipeline_a = Pipeline(validation_step, transform_step, process_step)
  
  # Pipeline B swaps transform_step with priority_step at runtime
  pipeline_b = Pipeline(validation_step, priority_step, process_step)
  ```
- **Extensibility Without Modification**: Adding a new step (e.g. `TaskTaggingStep` or `TaskPriorityStep`) requires creating a new subclass of `Step` and adding it to the pipeline using `pipeline.add_step(TaskTaggingStep())`. The `Pipeline` class implementation remains 100% untouched.

### OOP Concepts Demonstrated
- **Abstraction**: `Step` establishes a strict processing contract (`process`) without revealing execution details.
- **Encapsulation**: Steps encapsulate configuration via protected attributes (`_title_required`, `_default_completed`, `_status_label`) and maintain input immutability via `data.copy()`.
- **Inheritance**: Shallow inheritance tree where concrete steps inherit directly from `Step` without intermediate classes.
- **Polymorphism**: `Pipeline` invokes `.process()` uniformly on all step instances without type checks (`if isinstance(...)` is strictly avoided).

## D4 — Type Hints & Pydantic for Configuration

### Overview
D4 introduces runtime configuration validation using **Pydantic v2** (`app/config.py`), modern Python type hints, Enums, and a comparative demonstration against standard Python `@dataclass`.

### Static Type Hints vs Runtime Validation
- **Static Type Hints**: Tools like IDEs and `mypy` use type hints (`str`, `int`, `Optional[str]`, `list[str]`) during development for auto-completion and static analysis. However, standard Python type hints are **not** enforced at execution time.
- **Runtime Validation**: **Pydantic** evaluates data dynamic upon object instantiation (`PipelineConfig(**data)`). If input values break constraints (e.g. wrong type, out-of-range value, non-existent path), Pydantic immediately raises a detailed `ValidationError`.

### Dataclass vs Pydantic Runtime Validation
- **Python `@dataclass`**: Provides a concise way to create structured Python data containers. However, standard dataclasses **do not** validate field types or values when instantiated. Invalid parameters (e.g. `batch_size=-100`) pass silently.
- **Pydantic `BaseModel`**: Performs strict runtime type coercion and validator check evaluation (`@field_validator`) at creation time, rejecting invalid states immediately.

### Pipeline Configuration Fields & Rules
| Field | Type | Default | Validation Rules |
| :--- | :--- | :--- | :--- |
| `input_path` | `Path` | *Required* | Must exist on the filesystem (`Path.exists()`). |
| `batch_size` | `int` | `32` | Must be an integer greater than zero (`batch_size > 0`). |
| `image_size` | `ImageSize` | `224x224` | Width & height must be positive integers (`> 0`). |
| `feature_columns` | `list[str]` | `["title", "description", "status"]` | Must contain at least one column string. |
| `mode` | `ExecutionMode` (Enum) | `INFERENCE` | Must be one of `TRAIN`, `VALIDATE`, or `INFERENCE`. |
| `device` | `ExecutionDevice` (Enum) | `CPU` | Must be one of `CPU`, `CUDA`, or `MPS`. |
| `confidence_threshold` | `float` | `0.8` | Float value bounded strictly between `0.0` and `1.0`. |

### Deliberately Invalid Configuration Examples
Pydantic produces clear, specific validation error messages indicating **WHAT** is invalid, **WHERE** the problem is located, and **WHY** it was rejected:

1. **Non-existent Path**:
   - `WHERE`: Field `input_path`
   - `WHY`: `Value error, input_path does not exist: 'non_existent_folder_xyz'`
2. **Invalid Batch Size**:
   - `WHERE`: Field `batch_size`
   - `WHY`: `Value error, batch_size must be greater than 0`
3. **Out-of-Range Threshold**:
   - `WHERE`: Field `confidence_threshold`
   - `WHY`: `Value error, confidence_threshold must be between 0.0 and 1.0`
4. **Invalid Enum Choice**:
   - `WHERE`: Field `mode`
   - `WHY`: `Input should be 'TRAIN', 'VALIDATE' or 'INFERENCE'`

### Running D4 Configuration Demo
Run the interactive validation demonstration script:
```bash
python scripts/config_validation_demo.py
```

### Running D4 Configuration Tests
Run the configuration unit tests:
```bash
python -m unittest tests/test_config.py -v
```

## D5 — Decorators, Context Managers & Caching

### Overview
D5 introduces pythonic production utility patterns including higher-order function decorators, parameterized execution control, strict resource management via context managers, and bounded in-memory caching with `functools.lru_cache`.

### Decorators
- **What Decorators Are**: Decorators are higher-order functions that take a function object as an argument, extend or modify its execution behavior, and return a callable wrapper function.
- **Function Wrapping & `functools.wraps`**: When a function is wrapped by a decorator, its intrinsic metadata (`__name__`, `__doc__`, annotations) is replaced by the wrapper function. `functools.wraps(func)` copies the original metadata onto the wrapper function, preserving introspectability and debugging clarity.
- **Parameterized Decorators**: Decorators accepting arguments (e.g., `@retry(max_attempts=3)`) use a three-tier nested closure structure: the outer function receives arguments, the inner function receives the target callable, and the innermost wrapper executes the logic.

### `@timeit`
- **Purpose**: Measures and logs the precise execution wall-clock time of any function or method.
- **Usage**:
  ```python
  @timeit
  def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
      ...
  ```
- **Logging**: Logs function name and duration using `logging.getLogger(__name__)` (e.g. `Function 'process' executed in 0.000123 seconds`). Does not use `print()` statements and propagates exceptions unchanged.

### `@retry(max_attempts=N)`
- **Purpose**: Retries transiently failing functions automatically up to `max_attempts`.
- **Validation**: Enforces that `max_attempts` is an integer strictly greater than zero (`> 0`); invalid types or values raise `TypeError` or `ValueError`.
- **Behavior**: Catches exceptions during execution attempts, logs warning messages with attempt numbers, returns immediately upon success, and re-raises the final exception if all `max_attempts` are exhausted.

### Context Managers
- **Protocol (`__enter__` & `__exit__`)**: Classes implementing `__enter__` (acquire resource) and `__exit__` (release resource) form context managers used via `with` statements.
- **`contextlib.contextmanager`**: A decorator allowing generator functions using `try...finally` blocks to act as lightweight context managers.
- **Why Resource Cleanup Belongs in Context Managers**: The `__exit__` method or `finally` block is guaranteed to execute even if code inside the `with` block raises an exception. This prevents resource leaks (open file descriptors, lingering network sockets, or unreleased locks).

### Caching
- **`functools.lru_cache`**: Caches function call return values based on input arguments using a Least Recently Used (LRU) eviction strategy.
- **Cache Hits & Misses**: Repeated calls with identical arguments return cached results instantly in $O(1)$ time without re-executing function logic.
- **`cache_info()` & `cache_clear()`**: `.cache_info()` reports hit/miss counts and current size; `.cache_clear()` clears cached entries.
- **Bounded Caching (`maxsize=128`)**: Specifying a bounded `maxsize` prevents unbounded RAM consumption compared to unlimited caching (`maxsize=None`).
- **Stale Data & Invalidation**: If underlying data or configuration changes at runtime, cached results become stale. Callers must invoke `cache_clear()` to force cache invalidation.
- **Dangers of Caching Mutable Data**: Functions returning mutable lists or dictionaries return reference handles to cached objects. If a caller mutates the returned object, the cached state is mutated for all future callers across the application! Therefore, cached functions should return immutable structures or read-only views.

### Pipeline Integration
D5 features are directly integrated into the project's D3 Pipeline architecture (`app/services/pipeline_stages.py`):
1. **`TaskProcessingStep.process`**: Wrapped with `@timeit` to log stage execution timing automatically.
2. **`ReliableTaskFetcherStep`**: Uses `@retry(max_attempts=3)` to handle transient errors when fetching task data.
3. **`TaskBatchFileStep`**: Employs `PipelineResourceContext` inside its `process` method to safely manage writing batch records to file resources.
4. **`TaskValidationStep` & `TaskTransformationStep`**: Consume `get_pipeline_step_config` (backed by `@lru_cache`) to load deterministic step configuration parameters.

### Running D5 Demonstration Script
Run the interactive D5 feature demonstration:
```bash
python scripts/decorators_demo.py
```

### Running Complete Test Suite
Run all unit tests across D1–D5:
```bash
python -m unittest discover tests -v
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
python -m unittest discover tests -v
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
