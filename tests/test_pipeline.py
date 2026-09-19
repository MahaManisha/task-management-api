import unittest
from typing import Any, Dict

from app.services.pipeline import Pipeline
from app.services.pipeline_stages import (
    Step,
    TaskValidationStep,
    TaskTransformationStep,
    TaskProcessingStep,
)


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

