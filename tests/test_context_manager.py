import tempfile
import unittest
from pathlib import Path
from app.utils.context_managers import PipelineResourceContext, managed_pipeline_file


class TestPipelineResourceContext(unittest.TestCase):
    """Unit tests for PipelineResourceContext and managed_pipeline_file."""

    def test_acquire_and_normal_release(self):
        ctx = PipelineResourceContext(resource_name="TestResource")
        self.assertFalse(ctx.is_acquired)

        with ctx:
            self.assertTrue(ctx.is_acquired)

        self.assertFalse(ctx.is_acquired)

    def test_file_resource_acquisition_and_cleanup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_resource.txt"
            ctx = PipelineResourceContext(resource_name="FileResource", file_path=file_path)

            with ctx:
                self.assertTrue(ctx.is_acquired)
                self.assertIsNotNone(ctx._file_handle)
                self.assertFalse(ctx._file_handle.closed)
                ctx._file_handle.write("Sample content\n")

            self.assertFalse(ctx.is_acquired)
            self.assertTrue(ctx._file_handle.closed)
            self.assertTrue(file_path.exists())

    def test_release_after_exception(self):
        ctx = PipelineResourceContext(resource_name="ExceptionResource")

        with self.assertRaises(ZeroDivisionError):
            with ctx:
                self.assertTrue(ctx.is_acquired)
                _ = 1 / 0

        self.assertFalse(ctx.is_acquired)

    def test_managed_pipeline_file_normal_and_exception(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "managed_file.txt"

            # Normal execution
            with managed_pipeline_file(file_path, mode="w") as f:
                f.write("Line 1\n")
            self.assertTrue(file_path.exists())

            # Exception handling release
            with self.assertRaises(ValueError):
                with managed_pipeline_file(file_path, mode="a") as f:
                    f.write("Line 2\n")
                    raise ValueError("File context exception")

            content = file_path.read_text(encoding="utf-8")
            self.assertIn("Line 1\nLine 2\n", content)

    def test_pipeline_resource_context_write_and_unacquired_error(self):
        """Verify PipelineResourceContext write method safely writes data and raises RuntimeError when unacquired."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "write_test.txt"
            ctx = PipelineResourceContext(resource_name="WriteTest", file_path=file_path)

            # Attempt writing before acquisition raises RuntimeError
            with self.assertRaises(RuntimeError):
                ctx.write("Should fail")

            # Within context manager, write succeeds
            with ctx:
                bytes_written = ctx.write("Hello Resource\n")
                self.assertGreater(bytes_written, 0)

            # After exit, write raises RuntimeError
            with self.assertRaises(RuntimeError):
                ctx.write("Should fail after exit")

            self.assertEqual(file_path.read_text(encoding="utf-8"), "Hello Resource\n")


if __name__ == "__main__":
    unittest.main()
