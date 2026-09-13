from abc import ABC, abstractmethod
from typing import Any, Dict
from app.utils.validators import validate_task_title


class PipelineStage(ABC):
    """Abstract base class for pipeline processing stages."""

    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return transformed data."""
        pass


class TaskValidationStage(PipelineStage):
    """Pipeline stage that validates task data fields."""

    def __init__(self, title_required: bool = True):
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


class TaskTransformationStage(PipelineStage):
    """Pipeline stage that normalizes and formats task data."""

    def __init__(self, default_completed: bool = False):
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


class TaskProcessingStage(PipelineStage):
    """Pipeline stage that enriches task data with processing metadata."""

    def __init__(self, status_label: str = "PROCESSED"):
        self._status_label = status_label

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise TypeError("Input data must be a dictionary.")

        processed = data.copy()
        processed["status"] = self._status_label
        processed["processed"] = True
        return processed
