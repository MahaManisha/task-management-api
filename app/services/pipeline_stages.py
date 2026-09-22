from abc import ABC, abstractmethod
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from app.utils.validators import validate_task_title
from app.utils.decorators import timeit, retry
from app.utils.context_managers import PipelineResourceContext
from app.utils.cache import get_pipeline_step_config
from app.utils.exceptions import DataValidationError, ProcessingError

logger = logging.getLogger(__name__)


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
            logger.error("TaskValidationStep received invalid non-dict payload", extra={"event": "validation_type_error", "step": "TaskValidationStep"})
            raise TypeError("TaskValidationStep: input payload is not a dictionary; dictionary input is required.")

        title = data.get("title")
        logger.debug("Validating task title presence and length", extra={"event": "validation_check", "step": "TaskValidationStep", "title": title})

        if self._title_required:
            if not title or not validate_task_title(title):
                logger.warning("Task title validation failed: empty or invalid length", extra={"event": "validation_failure", "step": "TaskValidationStep"})
                raise DataValidationError(
                    "TaskValidationStep: task title is missing or invalid; title is required and must be between 1 and 100 characters."
                )
        elif title is not None and not validate_task_title(title):
            logger.warning("Task title validation failed: invalid format", extra={"event": "validation_failure", "step": "TaskValidationStep"})
            raise DataValidationError(
                "TaskValidationStep: task title format is invalid; title must be between 1 and 100 characters."
            )

        logger.info("Task validation succeeded", extra={"event": "validation_success", "step": "TaskValidationStep", "record_count": 1})
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
            logger.error("TaskTransformationStep received invalid non-dict payload", extra={"event": "transform_type_error", "step": "TaskTransformationStep"})
            raise TypeError("TaskTransformationStep: input payload is not a dictionary; dictionary input is required.")

        transformed = data.copy()
        if "title" in transformed and isinstance(transformed["title"], str):
            transformed["title"] = transformed["title"].strip()

        if "completed" not in transformed:
            transformed["completed"] = self._default_completed
        else:
            transformed["completed"] = bool(transformed["completed"])

        logger.info("Task transformation completed", extra={"event": "transformation_success", "step": "TaskTransformationStep", "record_count": 1})
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
            logger.error("TaskProcessingStep received invalid non-dict payload", extra={"event": "processing_type_error", "step": "TaskProcessingStep"})
            raise TypeError("TaskProcessingStep: input payload is not a dictionary; dictionary input is required.")

        processed = data.copy()
        processed["status"] = self._status_label
        processed["processed"] = True
        logger.info("Task processing completed", extra={"event": "processing_success", "step": "TaskProcessingStep", "status_label": self._status_label, "record_count": 1})
        return processed


class TaskBatchFileStep(Step):
    """Pipeline step using a resource context manager and try/except/else/finally to write batch records safely."""

    def __init__(self, batch_file_path: Union[str, Path], simulate_io_error: bool = False):
        self._batch_file_path = Path(batch_file_path)
        self._simulate_io_error = simulate_io_error

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise TypeError("TaskBatchFileStep: input payload is not a dictionary; dictionary input is required.")

        out_data = data.copy()
        file_handle = None
        logger.info(f"Writing task record to batch file '{self._batch_file_path.name}'", extra={"event": "batch_file_start", "step": "TaskBatchFileStep", "file_count": 1})
        try:
            if self._simulate_io_error:
                raise OSError("Disk full or permission denied")
            file_handle = open(self._batch_file_path, "a+", encoding="utf-8")
        except OSError as err:
            logger.error(f"Failed to access batch file '{self._batch_file_path.name}': {err}", extra={"event": "batch_file_error", "step": "TaskBatchFileStep", "error": str(err)})
            raise ProcessingError(
                f"TaskBatchFileStep: failed to access batch file '{self._batch_file_path.name}'; filesystem I/O operation failed."
            ) from err
        else:
            title = out_data.get("title", "Untitled")
            file_handle.write(f"BATCH RECORD: {title}\n")
            out_data["batch_logged"] = True
            logger.info(f"Successfully wrote record to batch file '{self._batch_file_path.name}'", extra={"event": "batch_file_success", "step": "TaskBatchFileStep", "record_count": 1})
        finally:
            if file_handle and not file_handle.closed:
                file_handle.close()

        return out_data


class ReliableTaskFetcherStep(Step):
    """Pipeline step demonstrating @retry logic and ProcessingError for unreliable network or data operations."""

    def __init__(self, max_attempts: int = 3, fail_count: int = 0):
        self._max_attempts = max_attempts
        self._fail_count = fail_count
        self._attempts_made = 0

    @retry(max_attempts=3)
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise TypeError("ReliableTaskFetcherStep: input payload is not a dictionary; dictionary input is required.")

        self._attempts_made += 1
        logger.info(f"Fetching task data (attempt {self._attempts_made}/{self._max_attempts})", extra={"event": "fetch_attempt", "step": "ReliableTaskFetcherStep", "attempt": self._attempts_made})
        if self._attempts_made <= self._fail_count:
            raise ProcessingError(
                f"ReliableTaskFetcherStep: transient fetching failure on attempt {self._attempts_made}; remote service unavailable."
            )

        result = data.copy()
        result["fetcher_attempts"] = self._attempts_made
        logger.info("Task data fetched successfully", extra={"event": "fetch_success", "step": "ReliableTaskFetcherStep", "attempts": self._attempts_made})
        return result


# Backward compatibility aliases
PipelineStage = Step
TaskValidationStage = TaskValidationStep
TaskTransformationStage = TaskTransformationStep
TaskProcessingStage = TaskProcessingStep
