from contextlib import contextmanager
import logging
from pathlib import Path
from typing import Any, Generator, IO, Optional, Union

logger = logging.getLogger(__name__)


class PipelineResourceContext:
    """Class-based context manager for managing pipeline resource acquisition and cleanup."""

    def __init__(self, resource_name: str, file_path: Optional[Union[str, Path]] = None):
        self.resource_name = resource_name
        self.file_path = Path(file_path) if file_path else None
        self._file_handle: Optional[IO[Any]] = None
        self.is_acquired = False

    def __enter__(self) -> "PipelineResourceContext":
        logger.info(f"Acquiring pipeline resource: {self.resource_name}")
        self.is_acquired = True
        if self.file_path:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_handle = open(self.file_path, "a+", encoding="utf-8")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        try:
            if self._file_handle and not self._file_handle.closed:
                self._file_handle.close()
        finally:
            self.is_acquired = False
            logger.info(f"Released pipeline resource: {self.resource_name}")
        return False


@contextmanager
def managed_pipeline_file(file_path: Union[str, Path], mode: str = "w") -> Generator[IO[Any], None, None]:
    """Generator-based context manager for managing pipeline file handles safely."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Opening managed pipeline file: {path.name}")
    file_obj = open(path, mode, encoding="utf-8")
    try:
        yield file_obj
    finally:
        file_obj.close()
        logger.info(f"Closed managed pipeline file: {path.name}")
