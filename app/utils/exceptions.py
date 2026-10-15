class TaskManagementError(Exception):
    """Base exception class for all domain-specific errors in the Task Management Application."""
    pass


class DataValidationError(TaskManagementError, ValueError):
    """Raised when task input data or pipeline payload fails validation constraints."""
    pass


class ConfigError(TaskManagementError, ValueError):
    """Raised when application or pipeline configuration loading or validation fails."""
    pass


class ProcessingError(TaskManagementError, RuntimeError):
    """Raised when data transformation, resource handling, or step processing fails during pipeline execution."""
    pass
