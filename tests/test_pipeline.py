import unittest
from typing import Any, Dict

from app.services.pipeline import Pipeline
from app.services.pipeline_stages import (
    PipelineStage,
    TaskValidationStage,
    TaskTransformationStage,
    TaskProcessingStage,
)


class DummyCustomStage(PipelineStage):
    """Custom stage for testing stage interchangeability and polymorphism."""

    def __init__(self, tag: str = "TAGGED"):
        self.tag = tag

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = data.copy()
        result["tag"] = self.tag
        return result


class TestPipeline(unittest.TestCase):

    def test_multi_stage_pipeline_execution(self):
        pipeline = Pipeline([
            TaskValidationStage(),
            TaskTransformationStage(default_completed=False),
            TaskProcessingStage(status_label="COMPLETED_STAGE"),
        ])
        raw_input = {"title": "  Complete D3 Internship Task  "}
        result = pipeline.run(raw_input)

        self.assertEqual(result["title"], "Complete D3 Internship Task")
        self.assertFalse(result["completed"])
        self.assertEqual(result["status"], "COMPLETED_STAGE")
        self.assertTrue(result["processed"])

    def test_stages_execute_in_correct_order_and_pass_data(self):
        execution_order = []

        class FirstStage(PipelineStage):
            def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
                execution_order.append("first")
                data_copy = data.copy()
                data_copy["step1"] = True
                return data_copy

        class SecondStage(PipelineStage):
            def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
                execution_order.append("second")
                if not data.get("step1"):
                    raise ValueError("step1 flag is missing from previous stage output.")
                data_copy = data.copy()
                data_copy["step2"] = True
                return data_copy

        pipeline = Pipeline()
        pipeline.add_stage(FirstStage()).add_stage(SecondStage())
        result = pipeline.run({"title": "Test Order"})

        self.assertEqual(execution_order, ["first", "second"])
        self.assertTrue(result.get("step1"))
        self.assertTrue(result.get("step2"))

    def test_single_stage_pipeline(self):
        pipeline = Pipeline([TaskTransformationStage(default_completed=True)])
        result = pipeline.run({"title": "  Single Stage Task  "})
        self.assertEqual(result["title"], "Single Stage Task")
        self.assertTrue(result["completed"])

    def test_pipeline_invalid_task_data(self):
        pipeline = Pipeline([TaskValidationStage()])

        with self.assertRaises(ValueError):
            pipeline.run({"title": ""})

        with self.assertRaises(ValueError):
            pipeline.run({"title": "a" * 101})

        with self.assertRaises(TypeError):
            pipeline.run("not a dictionary")

    def test_reusable_and_interchangeable_stages(self):
        validation = TaskValidationStage()
        transformation = TaskTransformationStage()
        custom = DummyCustomStage(tag="INTERCHANGEABLE")

        pipeline_a = Pipeline([validation, transformation, custom])
        result_a = pipeline_a.run({"title": "Task A"})
        self.assertEqual(result_a["tag"], "INTERCHANGEABLE")

        pipeline_b = Pipeline([validation, custom, TaskProcessingStage()])
        result_b = pipeline_b.run({"title": "Task B"})
        self.assertEqual(result_b["tag"], "INTERCHANGEABLE")
        self.assertTrue(result_b["processed"])

    def test_add_invalid_stage_raises_type_error(self):
        pipeline = Pipeline()
        with self.assertRaises(TypeError):
            pipeline.add_stage("not_a_stage")
