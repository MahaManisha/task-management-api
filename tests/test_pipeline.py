import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

from app.services.pipeline import Pipeline
from app.services.pipeline_stages import (
    Step,
    TaskValidationStep,
    TaskTransformationStep,
    TaskProcessingStep,
    TaskBatchFileStep,
    ReliableTaskFetcherStep,
    resolve_step_param,
    validate_task_payload,
    format_batch_record,
    write_batch_record,
)
from app.utils.exceptions import DataValidationError


class TaskTaggingStep(Step):
    """Custom step to demonstrate extending the pipeline without modifying Pipeline class."""

    def __init__(self, tag: str = "URGENT"):
        self.tag = tag

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise TypeError("Input data must be a dictionary.")
        result = data.copy()
        result["tag"] = self.tag
        return result


class TaskPriorityStep(Step):
    """Another custom step to demonstrate step interchangeability."""

    def __init__(self, priority: str = "HIGH"):
        self.priority = priority

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise TypeError("Input data must be a dictionary.")
        result = data.copy()
        result["priority"] = self.priority
        return result


class TestPipeline(unittest.TestCase):

    def test_step_is_abstract(self):
        """Verify that Step is an abstract base class and cannot be instantiated."""
        with self.assertRaises(TypeError):
            Step()

    def test_three_concrete_steps_execution(self):
        """Verify that all 3 concrete Steps work together in a pipeline."""
        pipeline = Pipeline(
            TaskValidationStep(),
            TaskTransformationStep(default_completed=False),
            TaskProcessingStep(status_label="COMPLETED_STAGE"),
        )
        raw_input = {"title": "  Complete D3 Internship Task  "}
        result = pipeline.run(raw_input)

        self.assertEqual(result["title"], "Complete D3 Internship Task")
        self.assertFalse(result["completed"])
        self.assertEqual(result["status"], "COMPLETED_STAGE")
        self.assertTrue(result["processed"])

    def test_steps_execute_in_correct_order_and_pass_data(self):
        """Verify that steps execute in order and output from one step becomes input to the next."""
        execution_order = []

        class FirstStep(Step):
            def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
                execution_order.append("first")
                data_copy = data.copy()
                data_copy["step1"] = True
                return data_copy

        class SecondStep(Step):
            def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
                execution_order.append("second")
                if not data.get("step1"):
                    raise ValueError("step1 flag is missing from previous step output.")
                data_copy = data.copy()
                data_copy["step2"] = True
                return data_copy

        pipeline = Pipeline()
        pipeline.add_step(FirstStep()).add_step(SecondStep())
        result = pipeline.run({"title": "Test Order"})

        self.assertEqual(execution_order, ["first", "second"])
        self.assertTrue(result.get("step1"))
        self.assertTrue(result.get("step2"))

    def test_runtime_step_swapping(self):
        """Demonstrate that one Step can be swapped for another at runtime without modifying Pipeline."""
        validation = TaskValidationStep()
        processing = TaskProcessingStep()

        # Pipeline A uses TaskTransformationStep in position 2
        pipeline_a = Pipeline(validation, TaskTransformationStep(default_completed=True), processing)
        result_a = pipeline_a.run({"title": "Task A"})
        self.assertTrue(result_a["completed"])

        # Pipeline B swaps position 2 with TaskPriorityStep without modifying Pipeline class
        pipeline_b = Pipeline(validation, TaskPriorityStep(priority="CRITICAL"), processing)
        result_b = pipeline_b.run({"title": "Task B"})
        self.assertEqual(result_b["priority"], "CRITICAL")
        self.assertTrue(result_b["processed"])

    def test_add_new_custom_step_without_modifying_pipeline(self):
        """Demonstrate adding a newly created Step to Pipeline without modifying Pipeline class."""
        pipeline = Pipeline()
        pipeline.add_step(TaskValidationStep())
        pipeline.add_step(TaskTaggingStep(tag="FEAT_D3"))

        result = pipeline.run({"title": "New Step Test"})
        self.assertEqual(result["title"], "New Step Test")
        self.assertEqual(result["tag"], "FEAT_D3")

    def test_pipeline_invalid_task_data(self):
        """Verify invalid task data raises expected validation errors."""
        pipeline = Pipeline(TaskValidationStep())

        with self.assertRaises(ValueError):
            pipeline.run({"title": ""})

        with self.assertRaises(ValueError):
            pipeline.run({"title": "a" * 101})

        with self.assertRaises(TypeError):
            pipeline.run("not a dictionary")

    def test_pipeline_reusability(self):
        """Verify that a Pipeline instance is reusable across multiple inputs."""
        pipeline = Pipeline(
            TaskValidationStep(),
            TaskTransformationStep(),
        )
        res1 = pipeline.run({"title": "  Task One  "})
        res2 = pipeline.run({"title": "  Task Two  "})

        self.assertEqual(res1["title"], "Task One")
        self.assertEqual(res2["title"], "Task Two")

    def test_add_invalid_step_raises_type_error(self):
        """Verify adding an object that is not a Step raises TypeError."""
        pipeline = Pipeline()
        with self.assertRaises(TypeError):
            pipeline.add_step("not_a_step")

    def test_d5_pipeline_integration_batch_file_context_manager(self):
        """Verify TaskBatchFileStep (using context manager) works seamlessly in Pipeline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            batch_path = Path(temp_dir) / "pipeline_batch.txt"
            pipeline = Pipeline(
                TaskValidationStep(),
                TaskBatchFileStep(batch_file_path=batch_path),
            )
            res = pipeline.run({"title": "Batch Managed Task"})
            self.assertTrue(res.get("batch_logged"))
            self.assertTrue(batch_path.exists())
            self.assertIn("BATCH RECORD: Batch Managed Task", batch_path.read_text(encoding="utf-8"))

    def test_d5_pipeline_integration_reliable_fetcher_retry(self):
        """Verify ReliableTaskFetcherStep (using @retry) retries and succeeds in Pipeline."""
        pipeline = Pipeline(
            ReliableTaskFetcherStep(max_attempts=3, fail_count=2),
            TaskValidationStep(),
        )
        res = pipeline.run({"title": "Retryable Task"})
        self.assertEqual(res["fetcher_attempts"], 3)
        self.assertEqual(res["title"], "Retryable Task")

    def test_resolve_step_param_priority_and_fallback(self):
        """Verify resolve_step_param prioritizes explicit values, then cached config, then default."""
        # 1. Explicit value overrides cached config
        explicit_res = resolve_step_param("TaskValidationStep", "title_required", False, default=True)
        self.assertFalse(explicit_res)

        # 2. None explicit value uses cached config
        cached_res = resolve_step_param("TaskValidationStep", "title_required", None, default=False)
        self.assertTrue(cached_res)

        # 3. Missing parameter returns fallback default
        fallback_res = resolve_step_param("UnknownStep", "non_existent_key", None, default="FALLBACK")
        self.assertEqual(fallback_res, "FALLBACK")

    def test_validate_task_payload_helper(self):
        """Verify validate_task_payload enforces title presence and length constraints."""
        # Valid payload passes
        validate_task_payload({"title": "Valid Task Title"}, title_required=True)

        # Missing title when required raises DataValidationError
        with self.assertRaises(DataValidationError) as cm1:
            validate_task_payload({"title": ""}, title_required=True)
        self.assertIn("task title is missing or invalid", str(cm1.exception))

        # Title exceeding max length raises DataValidationError
        with self.assertRaises(DataValidationError) as cm2:
            validate_task_payload({"title": "x" * 105}, title_required=True)
        self.assertIn("must be between 1 and 100 characters", str(cm2.exception))

        # None title when optional passes
        validate_task_payload({"title": None}, title_required=False)

    def test_format_batch_record_helper(self):
        """Verify format_batch_record produces consistent batch line output."""
        formatted = format_batch_record("Deploy Task Management API")
        self.assertEqual(formatted, "BATCH RECORD: Deploy Task Management API\n")

    def test_write_batch_record_helper_and_simulated_io_error(self):
        """Verify write_batch_record writes via context manager and propagates simulated I/O errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "helper_batch.txt"
            record = "BATCH RECORD: Helper Test\n"

            # Normal write
            write_batch_record(file_path, record, simulate_io_error=False)
            self.assertTrue(file_path.exists())
            self.assertEqual(file_path.read_text(encoding="utf-8"), record)

            # Simulated I/O error
            with self.assertRaises(OSError) as cm:
                write_batch_record(file_path, record, simulate_io_error=True)
            self.assertIn("Disk full or permission denied", str(cm.exception))

    def test_step_validate_payload_method(self):
        """Verify base Step._validate_payload accepts dicts and rejects non-dicts with informative error."""
        step = TaskValidationStep()

        # Valid dict returns itself
        valid_dict = {"key": "value"}
        self.assertEqual(step._validate_payload(valid_dict), valid_dict)

        # Non-dict raises TypeError identifying the step
        with self.assertRaises(TypeError) as cm:
            step._validate_payload(["not", "a", "dict"])
        self.assertIn("TaskValidationStep: input payload is not a dictionary", str(cm.exception))

    def test_extensibility_custom_preprocessing_and_audit_steps_without_modifying_pipeline(self):
        """Demonstrate adding custom preprocessing and postprocessing steps without modifying Pipeline."""
        execution_order = []

        class TaskSanitizationStep(Step):
            """Custom preprocessing step sanitizing title to titlecase."""
            def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
                self._validate_payload(data)
                execution_order.append("sanitize")
                result = data.copy()
                raw_title = result.get("title", "")
                result["title"] = raw_title.strip().title()
                result["sanitized"] = True
                return result

        class TaskAuditStep(Step):
            """Custom postprocessing step adding an audit verification stamp."""
            def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
                self._validate_payload(data)
                execution_order.append("audit")
                result = data.copy()
                result["audit_verified"] = True
                return result

        # Compose pipeline with custom preprocessing, built-in stages, and custom postprocessing
        pipeline = Pipeline(
            TaskSanitizationStep(),
            TaskValidationStep(),
            TaskTransformationStep(default_completed=False),
            TaskProcessingStep(status_label="EXTENDED_STAGE"),
            TaskAuditStep(),
        )

        input_payload = {"title": "  clean code solid refactoring  "}
        output = pipeline.run(input_payload)

        # Verify execution order was preserved
        self.assertEqual(execution_order, ["sanitize", "audit"])

        # Verify all transformations occurred in order without modifying Pipeline orchestration
        self.assertEqual(output["title"], "Clean Code Solid Refactoring")
        self.assertTrue(output["sanitized"])
        self.assertFalse(output["completed"])
        self.assertEqual(output["status"], "EXTENDED_STAGE")
        self.assertTrue(output["processed"])
        self.assertTrue(output["audit_verified"])
