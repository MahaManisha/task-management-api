import re
import unittest
from pathlib import Path
from pydantic import ValidationError

from app.config import load_pipeline_config
from app.services.pipeline_stages import (
    TaskValidationStep,
    TaskBatchFileStep,
    ReliableTaskFetcherStep,
)
from app.utils.exceptions import (
    TaskManagementError,
    DataValidationError,
    ConfigError,
    ProcessingError,
)


class TestExceptions(unittest.TestCase):
    """Comprehensive unit test suite for D6 Exception Hierarchies & Error Design."""

    def test_1_base_exception_exists(self):
        """Verify project base exception TaskManagementError exists and inherits from Exception."""
        self.assertTrue(issubclass(TaskManagementError, Exception))

    def test_2_data_validation_error_inheritance(self):
        """Verify DataValidationError inherits from TaskManagementError."""
        self.assertTrue(issubclass(DataValidationError, TaskManagementError))

    def test_3_config_error_inheritance(self):
        """Verify ConfigError inherits from TaskManagementError."""
        self.assertTrue(issubclass(ConfigError, TaskManagementError))

    def test_4_processing_error_inheritance(self):
        """Verify ProcessingError inherits from TaskManagementError."""
        self.assertTrue(issubclass(ProcessingError, TaskManagementError))

    def test_5_specific_exceptions_caught_individually(self):
        """Verify that custom exceptions can be caught by their specific type."""
        try:
            raise DataValidationError("Data error")
        except DataValidationError as e:
            self.assertIsInstance(e, DataValidationError)

        try:
            raise ConfigError("Config error")
        except ConfigError as e:
            self.assertIsInstance(e, ConfigError)

        try:
            raise ProcessingError("Processing error")
        except ProcessingError as e:
            self.assertIsInstance(e, ProcessingError)

    def test_6_base_exception_catches_all_subclasses(self):
        """Verify TaskManagementError catches all project custom exception subclasses."""
        for exc_class in (DataValidationError, ConfigError, ProcessingError):
            caught = False
            try:
                raise exc_class("Sample error message")
            except TaskManagementError:
                caught = True
            self.assertTrue(caught, f"Base exception failed to catch {exc_class.__name__}")

    def test_7_data_validation_error_raised_for_invalid_data(self):
        """Verify DataValidationError is raised for invalid pipeline task data."""
        step = TaskValidationStep()
        with self.assertRaises(DataValidationError) as cm:
            step.process({"title": ""})

        self.assertIn("TaskValidationStep", str(cm.exception))
        self.assertIn("title is missing or invalid", str(cm.exception))

    def test_8_config_error_raised_for_invalid_config(self):
        """Verify ConfigError is raised when loading invalid configuration via load_pipeline_config."""
        with self.assertRaises(ConfigError) as cm:
            load_pipeline_config(input_path=Path("non_existent_path_xyz_12345"))

        self.assertIn("PipelineConfig", str(cm.exception))

    def test_9_processing_error_raised_for_resource_failure(self):
        """Verify ProcessingError is raised during resource processing failure."""
        step = TaskBatchFileStep(batch_file_path="invalid_path.txt", simulate_io_error=True)
        with self.assertRaises(ProcessingError) as cm:
            step.process({"title": "Sample Task"})

        self.assertIn("TaskBatchFileStep", str(cm.exception))

    def test_10_error_messages_contain_what_where_why(self):
        """Verify exception messages clearly convey WHAT, WHERE, and WHY."""
        step = TaskValidationStep()
        try:
            step.process({"title": "a" * 105})
        except DataValidationError as exc:
            msg = str(exc)
            # WHERE: TaskValidationStep
            self.assertIn("TaskValidationStep", msg)
            # WHAT: task title is missing or invalid
            self.assertIn("task title is missing or invalid", msg)
            # WHY: title is required and must be between 1 and 100 characters
            self.assertIn("must be between 1 and 100 characters", msg)

    def test_11_exception_chaining_works(self):
        """Verify exception chaining using 'raise ... from exc'."""
        try:
            load_pipeline_config(input_path=Path("non_existent_folder_abc"))
        except ConfigError as exc:
            self.assertIsNotNone(exc.__cause__)
            self.assertIsInstance(exc.__cause__, ValidationError)

    def test_12_cause_contains_original_exception(self):
        """Verify __cause__ attribute references the original lower-level exception."""
        step = TaskBatchFileStep(batch_file_path="simulated.txt", simulate_io_error=True)
        try:
            step.process({"title": "Test Task"})
        except ProcessingError as exc:
            self.assertIsNotNone(exc.__cause__)
            self.assertIsInstance(exc.__cause__, OSError)
            self.assertEqual(str(exc.__cause__), "Disk full or permission denied")

    def test_13_final_exception_not_silently_swallowed(self):
        """Verify final exceptions from retried operations propagate without being swallowed."""
        fetcher = ReliableTaskFetcherStep(max_attempts=3, fail_count=5)
        with self.assertRaises(ProcessingError) as cm:
            fetcher.process({"title": "Test Task"})

        self.assertIn("ReliableTaskFetcherStep", str(cm.exception))

    def test_14_no_bare_except_in_production_code(self):
        """Verify production application code under app/ contains no bare 'except:' statements."""
        app_dir = Path(__file__).resolve().parent.parent / "app"
        bare_except_pattern = re.compile(r"^\s*except\s*:", re.MULTILINE)

        for py_file in app_dir.glob("**/*.py"):
            content = py_file.read_text(encoding="utf-8")
            matches = bare_except_pattern.findall(content)
            self.assertEqual(
                len(matches),
                0,
                f"Bare 'except:' found in production file: {py_file.relative_to(app_dir.parent)}",
            )


if __name__ == "__main__":
    unittest.main()
