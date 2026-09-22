import json
import logging
import re
import tempfile
import unittest
from pathlib import Path

from app.services.pipeline import Pipeline
from app.services.pipeline_stages import (
    TaskValidationStep,
    TaskTransformationStep,
    TaskProcessingStep,
    ReliableTaskFetcherStep,
)
from app.utils.exceptions import ProcessingError
from app.utils.logging_config import JSONFormatter, configure_logging
from app.utils.decorators import timeit


class TestLogging(unittest.TestCase):
    """Comprehensive test suite for D7 Structured Logging & Production Debugging."""

    def setUp(self):
        self._reset_loggers()

    def tearDown(self):
        self._reset_loggers()

    def _reset_loggers(self):
        root = logging.getLogger()
        for handler in list(root.handlers):
            handler.close()
            root.removeHandler(handler)

        app_logger = logging.getLogger("app")
        for handler in list(app_logger.handlers):
            handler.close()
            app_logger.removeHandler(handler)

    def test_json_formatter(self):
        """Verify JSONFormatter formats record into valid JSON with custom extra fields."""
        formatter = JSONFormatter(environment="test")
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Sample event",
            args=(),
            exc_info=None,
        )
        record.event = "custom_event"
        record.duration_ms = 42.5

        formatted_json = formatter.format(record)
        data = json.loads(formatted_json)

        self.assertEqual(data["logger"], "test_logger")
        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["message"], "Sample event")
        self.assertEqual(data["environment"], "test")
        self.assertEqual(data["event"], "custom_event")
        self.assertEqual(data["duration_ms"], 42.5)
        self.assertIn("timestamp", data)

    def test_development_logging_configuration(self):
        """Verify configure_logging sets plain text formatter in development mode."""
        logger = configure_logging(environment="development")
        self.assertEqual(logger.level, logging.INFO)

        root = logging.getLogger()
        self.assertGreater(len(root.handlers), 0)
        handler = root.handlers[0]
        self.assertNotIsInstance(handler.formatter, JSONFormatter)

    def test_production_logging_configuration(self):
        """Verify configure_logging sets JSONFormatter in production mode."""
        logger = configure_logging(environment="production")
        root = logging.getLogger()
        self.assertGreater(len(root.handlers), 0)
        handler = root.handlers[0]
        self.assertIsInstance(handler.formatter, JSONFormatter)

    def test_log_file_creation(self):
        """Verify configure_logging creates and writes structured JSON logs to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "test_output.log"
            logger = configure_logging(environment="production", log_file=log_path)
            logger.info("Test file message", extra={"event": "file_test"})

            self.assertTrue(log_path.exists())
            content = log_path.read_text(encoding="utf-8")
            self.assertIn("Test file message", content)
            self.assertIn('"event": "file_test"', content)

            self._reset_loggers()

    def test_no_duplicate_handlers(self):
        """Verify consecutive configure_logging calls do not duplicate handlers."""
        configure_logging(environment="development")
        configure_logging(environment="production")
        configure_logging(environment="development")

        root = logging.getLogger()
        self.assertEqual(len(root.handlers), 1)

    def test_pipeline_lifecycle_and_step_logging(self):
        """Verify Pipeline.run logs start, step lifecycle, and completion events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "lifecycle.log"
            configure_logging(environment="production", log_file=log_path)

            pipeline = Pipeline(
                TaskValidationStep(),
                TaskTransformationStep(),
                TaskProcessingStep(),
            )
            pipeline.run({"title": "   Lifecycle Task   "})

            content = log_path.read_text(encoding="utf-8")
            self.assertIn('"event": "pipeline_start"', content)
            self.assertIn('"event": "step_start"', content)
            self.assertIn('"event": "step_complete"', content)
            self.assertIn('"event": "pipeline_complete"', content)

            self._reset_loggers()

    def test_exception_traceback_logging(self):
        """Verify pipeline failure logs full exception traceback via logger.exception."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "exception.log"
            configure_logging(environment="production", log_file=log_path)

            pipeline = Pipeline(
                TaskValidationStep(),
                ReliableTaskFetcherStep(max_attempts=2, fail_count=3),
            )

            with self.assertRaises(ProcessingError):
                pipeline.run({"title": "Failing Task"})

            content = log_path.read_text(encoding="utf-8")
            self.assertIn('"event": "pipeline_failure"', content)
            self.assertIn('"exception": "Traceback', content)
            self.assertIn("ProcessingError", content)

            self._reset_loggers()

    def test_timeit_decorator_logs_instead_of_printing(self):
        """Verify @timeit logs timing information with duration_ms instead of using print."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "timeit.log"
            configure_logging(environment="production", log_file=log_path)

            @timeit
            def timed_fn():
                return 42

            result = timed_fn()
            self.assertEqual(result, 42)

            content = log_path.read_text(encoding="utf-8")
            self.assertIn('"event": "function_timing"', content)
            self.assertIn('"duration_ms"', content)

            self._reset_loggers()

    def test_no_print_calls_in_application_code(self):
        """Verify that zero print() calls exist across app/, tests/, and scripts/."""
        project_root = Path(__file__).resolve().parent.parent
        dirs_to_check = [project_root / "app", project_root / "tests", project_root / "scripts"]
        print_pattern = re.compile(r"^\s*print\(", re.MULTILINE)

        for dir_path in dirs_to_check:
            for py_file in dir_path.glob("**/*.py"):
                content = py_file.read_text(encoding="utf-8")
                matches = print_pattern.findall(content)
                self.assertEqual(
                    len(matches),
                    0,
                    f"Found print() call in file: {py_file.relative_to(project_root)}",
                )


if __name__ == "__main__":
    unittest.main()
