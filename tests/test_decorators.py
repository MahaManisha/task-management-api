import logging
import unittest
from unittest.mock import MagicMock
from app.utils.decorators import timeit, retry


class TestTimeitDecorator(unittest.TestCase):
    """Unit tests for @timeit decorator."""

    def test_result_preserved(self):
        @timeit
        def add(a: int, b: int) -> int:
            return a + b

        self.assertEqual(add(5, 7), 12)

    def test_metadata_preserved(self):
        @timeit
        def sample_function():
            """Docstring for sample_function."""
            return True

        self.assertEqual(sample_function.__name__, "sample_function")
        self.assertEqual(sample_function.__doc__, "Docstring for sample_function.")

    def test_logging(self):
        logger = logging.getLogger("app.utils.decorators")
        with self.assertLogs(logger, level="INFO") as cm:
            @timeit
            def dummy_task():
                return "done"

            result = dummy_task()

        self.assertEqual(result, "done")
        self.assertTrue(any("Function 'dummy_task' executed in" in log for log in cm.output))

    def test_exception_propagation(self):
        @timeit
        def failing_function():
            raise ValueError("Timeit failure test")

        with self.assertRaises(ValueError) as cm:
            failing_function()
        self.assertEqual(str(cm.exception), "Timeit failure test")


class TestRetryDecorator(unittest.TestCase):
    """Unit tests for @retry decorator."""

    def test_immediate_success(self):
        mock_func = MagicMock(return_value="success")

        @retry(max_attempts=3)
        def target():
            return mock_func()

        result = target()
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 1)

    def test_eventual_success(self):
        attempts = 0

        @retry(max_attempts=3)
        def target():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError(f"Failure attempt {attempts}")
            return "eventual_success"

        result = target()
        self.assertEqual(result, "eventual_success")
        self.assertEqual(attempts, 3)

    def test_repeated_failure(self):
        attempts = 0

        @retry(max_attempts=3)
        def target():
            nonlocal attempts
            attempts += 1
            raise RuntimeError(f"Persistent failure {attempts}")

        with self.assertRaises(RuntimeError) as cm:
            target()

        self.assertEqual(attempts, 3)
        self.assertIn("Persistent failure 3", str(cm.exception))

    def test_exact_attempt_count(self):
        attempts = 0

        @retry(max_attempts=5)
        def target():
            nonlocal attempts
            attempts += 1
            raise ValueError("Fail")

        with self.assertRaises(ValueError):
            target()

        self.assertEqual(attempts, 5)

    def test_invalid_max_attempts(self):
        with self.assertRaises(ValueError):
            @retry(max_attempts=0)
            def func_a():
                pass

        with self.assertRaises(ValueError):
            @retry(max_attempts=-3)
            def func_b():
                pass

        with self.assertRaises(TypeError):
            @retry(max_attempts="invalid")  # type: ignore
            def func_c():
                pass

    def test_metadata_preservation(self):
        @retry(max_attempts=2)
        def annotated_func():
            """Decorated docstring."""
            return 42

        self.assertEqual(annotated_func.__name__, "annotated_func")
        self.assertEqual(annotated_func.__doc__, "Decorated docstring.")


if __name__ == "__main__":
    unittest.main()
