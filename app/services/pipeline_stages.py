from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union
from app.utils.validators import validate_task_title
from app.utils.decorators import timeit, retry
from app.utils.context_managers import PipelineResourceContext
from app.utils.cache import get_pipeline_step_config


class Step(ABC):
    """Abstract base class establishing the interface for pipeline steps."""

    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data dictionary and return the transformed data dictionary."""
        pass


class TaskValidationStep(Step):
    """Pipeline step that validates task data fields using cached configuration defaults."""

    def __init__(self, title_required: Optional[bool] = None):
        cached_config = get_pipeline_step_config("TaskValidationStep")
        if title_required is None:
            self._title_required = cached_config.get("title_required", True)
        else:
            self._title_required = title_required

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise TypeError("Input data must be a dictionary.")

        title = data.get("title")
        if self._title_required:
            if not title or not validate_task_title(title):
                raise ValueError("Task title is required and must be between 1 and 100 characters.")
        elif title is not None and not validate_task_title(title):
            raise ValueError("Task title must be between 1 and 100 characters.")

        return data.copy()


class TaskTransformationStep(Step):
    """Pipeline step that normalizes and formats task data using cached step rules."""

    def __init__(self, default_completed: Optional[bool] = None):
        cached_config = get_pipeline_step_config("TaskTransformationStep")
        if default_completed is None:
            self._default_completed = cached_config.get("default_completed", False)
        else:
            self._default_completed = default_completed

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise TypeError("Input data must be a dictionary.")

        transformed = data.copy()
        if "title" in transformed and isinstance(transformed["title"], str):
            transformed["title"] = transformed["title"].strip()

        if "completed" not in transformed:
            transformed["completed"] = self._default_completed
        else:
            transformed["completed"] = bool(transformed["completed"])

        return transformed


class TaskProcessingStep(Step):
    """Pipeline step that enriches task data with processing metadata, timed via @timeit."""

    def __init__(self, status_label: Optional[str] = None):
        cached_config = get_pipeline_step_config("TaskProcessingStep")
        if status_label is None:
            self._status_label = cached_config.get("status_label", "PROCESSED")
        else:
            self._status_label = status_label

    @timeit
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise TypeError("Input data must be a dictionary.")

        processed = data.copy()
        processed["status"] = self._status_label
        processed["processed"] = True
        return processed


class TaskBatchFileStep(Step):
    """Pipeline step using a resource context manager to write batch records safely."""

    def __init__(self, batch_file_path: Union[str, Path]):
        self._batch_file_path = Path(batch_file_path)

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise TypeError("Input data must be a dictionary.")

        out_data = data.copy()
        with PipelineResourceContext(resource_name="TaskBatchWriter", file_path=self._batch_file_path) as ctx:
            if ctx._file_handle:
                title = out_data.get("title", "Untitled")
                ctx._file_handle.write(f"BATCH RECORD: {title}\n")
                out_data["batch_logged"] = True

        return out_data


class ReliableTaskFetcherStep(Step):
    """Pipeline step demonstrating @retry logic for unreliable network or data operations."""

    def __init__(self, max_attempts: int = 3, fail_count: int = 0):
        self._max_attempts = max_attempts
        self._fail_count = fail_count
        self._attempts_made = 0

    @retry(max_attempts=3)
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise TypeError("Input data must be a dictionary.")

        self._attempts_made += 1
        if self._attempts_made <= self._fail_count:
            raise RuntimeError(f"Simulated transient error on attempt {self._attempts_made}")

        result = data.copy()
        result["fetcher_attempts"] = self._attempts_made
        return result


# Backward compatibility aliases
PipelineStage = Step
TaskValidationStage = TaskValidationStep
TaskTransformationStage = TaskTransformationStep
TaskProcessingStage = TaskProcessingStep
