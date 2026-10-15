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


def resolve_step_param(step_name: str, param_name: str, explicit_value: Any, default: Any = None) -> Any:
    """Resolve a pipeline step parameter using explicit value first, then cached config, then default."""
    if explicit_value is not None:
        return explicit_value
    cached_config = get_pipeline_step_config(step_name)
    return cached_config.get(param_name, default)


def validate_task_payload(data: Dict[str, Any], title_required: bool = True) -> None:
    """Validate task payload title constraints according to domain rules."""
    title = data.get("title")
    logger.debug(
        "Validating task title presence and length",
        extra={"event": "validation_check", "step": "TaskValidationStep", "title": title},
    )

    if title_required:
        if not title or not validate_task_title(title):
            logger.warning(
                "Task title validation failed: empty or invalid length",
                extra={"event": "validation_failure", "step": "TaskValidationStep"},
            )
            raise DataValidationError(
                "TaskValidationStep: task title is missing or invalid; title is required and must be between 1 and 100 characters."
            )
    elif title is not None and not validate_task_title(title):
        logger.warning(
            "Task title validation failed: invalid format",
            extra={"event": "validation_failure", "step": "TaskValidationStep"},
        )
        raise DataValidationError(
            "TaskValidationStep: task title format is invalid; title must be between 1 and 100 characters."
        )


def format_batch_record(task_title: str) -> str:
    """Format a task title into a standardized batch record line."""
    return f"BATCH RECORD: {task_title}\n"


def write_batch_record(file_path: Path, record_text: str, simulate_io_error: bool = False) -> None:
    """Safely append a batch record using PipelineResourceContext."""
    if simulate_io_error:
        raise OSError("Disk full or permission denied")
    with PipelineResourceContext(resource_name=f"BatchFile-{file_path.name}", file_path=file_path) as ctx:
        ctx.write(record_text)


class Step(ABC):
    """Abstract base class establishing the interface for pipeline steps."""

    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data dictionary and return the transformed data dictionary."""
        pass

    def _validate_payload(self, data: Any, event: Optional[str] = None) -> Dict[str, Any]:
        """Validate that input data is a dictionary.

        Raises:
            TypeError: If input data is not a dictionary.
        """
        if not isinstance(data, dict):
            step_name = self.__class__.__name__
            if event:
                logger.error(
                    f"{step_name} received invalid non-dict payload",
                    extra={"event": event, "step": step_name},
                )
            raise TypeError(f"{step_name}: input payload is not a dictionary; dictionary input is required.")
        return data


class TaskValidationStep(Step):
    """Pipeline step that validates task data fields using cached configuration defaults."""

    def __init__(self, title_required: Optional[bool] = None):
        self._title_required = resolve_step_param(
            "TaskValidationStep", "title_required", title_required, default=True
        )

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._validate_payload(data, event="validation_type_error")
        validate_task_payload(data, title_required=self._title_required)
        logger.info(
            "Task validation succeeded",
            extra={"event": "validation_success", "step": "TaskValidationStep", "record_count": 1},
        )
        return data.copy()


class TaskTransformationStep(Step):
    """Pipeline step that normalizes and formats task data using cached step rules."""

    def __init__(self, default_completed: Optional[bool] = None):
        self._default_completed = resolve_step_param(
            "TaskTransformationStep", "default_completed", default_completed, default=False
        )

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._validate_payload(data, event="transform_type_error")

        transformed = data.copy()
        if "title" in transformed and isinstance(transformed["title"], str):
            transformed["title"] = transformed["title"].strip()

        if "completed" not in transformed:
            transformed["completed"] = self._default_completed
        else:
            transformed["completed"] = bool(transformed["completed"])

        logger.info(
            "Task transformation completed",
            extra={"event": "transformation_success", "step": "TaskTransformationStep", "record_count": 1},
        )
        return transformed


class TaskProcessingStep(Step):
    """Pipeline step that enriches task data with processing metadata, timed via @timeit."""

    def __init__(self, status_label: Optional[str] = None):
        self._status_label = resolve_step_param(
            "TaskProcessingStep", "status_label", status_label, default="PROCESSED"
        )

    @timeit
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._validate_payload(data, event="processing_type_error")

        processed = data.copy()
        processed["status"] = self._status_label
        processed["processed"] = True
        logger.info(
            "Task processing completed",
            extra={"event": "processing_success", "step": "TaskProcessingStep", "status_label": self._status_label, "record_count": 1},
        )
        return processed


class TaskBatchFileStep(Step):
    """Pipeline step that logs batch task records to file using PipelineResourceContext."""

    def __init__(self, batch_file_path: Union[str, Path], simulate_io_error: bool = False):
        self._batch_file_path = Path(batch_file_path)
        self._simulate_io_error = simulate_io_error

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._validate_payload(data)

        out_data = data.copy()
        title = out_data.get("title", "Untitled")
        record_text = format_batch_record(title)

        logger.info(
            f"Writing task record to batch file '{self._batch_file_path.name}'",
            extra={"event": "batch_file_start", "step": "TaskBatchFileStep", "file_count": 1},
        )
        try:
            write_batch_record(
                self._batch_file_path,
                record_text,
                simulate_io_error=self._simulate_io_error,
            )
        except OSError as err:
            logger.error(
                f"Failed to access batch file '{self._batch_file_path.name}': {err}",
                extra={"event": "batch_file_error", "step": "TaskBatchFileStep", "error": str(err)},
            )
            raise ProcessingError(
                f"TaskBatchFileStep: failed to access batch file '{self._batch_file_path.name}'; filesystem I/O operation failed."
            ) from err

        out_data["batch_logged"] = True
        logger.info(
            f"Successfully wrote record to batch file '{self._batch_file_path.name}'",
            extra={"event": "batch_file_success", "step": "TaskBatchFileStep", "record_count": 1},
        )
        return out_data


class ReliableTaskFetcherStep(Step):
    """Pipeline step demonstrating @retry logic and ProcessingError for unreliable network or data operations."""

    def __init__(self, max_attempts: int = 3, fail_count: int = 0):
        self._max_attempts = max_attempts
        self._fail_count = fail_count
        self._attempts_made = 0

    @retry(max_attempts=3)
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        self._validate_payload(data)

        self._attempts_made += 1
        logger.info(
            f"Fetching task data (attempt {self._attempts_made}/{self._max_attempts})",
            extra={"event": "fetch_attempt", "step": "ReliableTaskFetcherStep", "attempt": self._attempts_made},
        )
        if self._attempts_made <= self._fail_count:
            raise ProcessingError(
                f"ReliableTaskFetcherStep: transient fetching failure on attempt {self._attempts_made}; remote service unavailable."
            )

        result = data.copy()
        result["fetcher_attempts"] = self._attempts_made
        logger.info(
            "Task data fetched successfully",
            extra={"event": "fetch_success", "step": "ReliableTaskFetcherStep", "attempts": self._attempts_made},
        )
        return result


# Backward compatibility aliases
PipelineStage = Step
TaskValidationStage = TaskValidationStep
TaskTransformationStage = TaskTransformationStep
TaskProcessingStage = TaskProcessingStep
