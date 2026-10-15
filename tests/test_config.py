import unittest
from pathlib import Path
import tempfile
from pydantic import ValidationError
from app.config import (
    PipelineConfig,
    ImageSize,
    ExecutionMode,
    ExecutionDevice,
    DataclassPipelineConfig,
)


class TestPipelineConfig(unittest.TestCase):

    def test_valid_configuration_loads_successfully(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = PipelineConfig(
                input_path=temp_path,
                batch_size=16,
                image_size=ImageSize(width=224, height=224),
                feature_columns=["title", "description"],
                mode=ExecutionMode.TRAIN,
                device=ExecutionDevice.CPU,
                confidence_threshold=0.75,
            )
            self.assertEqual(config.input_path, temp_path)
            self.assertEqual(config.batch_size, 16)
            self.assertEqual(config.image_size.width, 224)
            self.assertEqual(config.image_size.height, 224)
            self.assertEqual(config.feature_columns, ["title", "description"])
            self.assertEqual(config.mode, ExecutionMode.TRAIN)
            self.assertEqual(config.device, ExecutionDevice.CPU)
            self.assertEqual(config.confidence_threshold, 0.75)

    def test_wrong_type_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValidationError) as ctx:
                PipelineConfig(
                    input_path=Path(temp_dir),
                    batch_size="not_an_integer",
                )
            self.assertIn("batch_size", str(ctx.exception))

    def test_invalid_batch_size_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with self.assertRaises(ValidationError) as ctx:
                PipelineConfig(input_path=temp_path, batch_size=0)
            self.assertIn("batch_size must be greater than 0", str(ctx.exception))

            with self.assertRaises(ValidationError) as ctx2:
                PipelineConfig(input_path=temp_path, batch_size=-10)
            self.assertIn("batch_size must be greater than 0", str(ctx2.exception))

    def test_invalid_threshold_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with self.assertRaises(ValidationError) as ctx:
                PipelineConfig(input_path=temp_path, confidence_threshold=1.5)
            self.assertIn("confidence_threshold must be between 0.0 and 1.0", str(ctx.exception))

            with self.assertRaises(ValidationError) as ctx2:
                PipelineConfig(input_path=temp_path, confidence_threshold=-0.1)
            self.assertIn("confidence_threshold must be between 0.0 and 1.0", str(ctx2.exception))

    def test_missing_required_field_rejected(self):
        with self.assertRaises(ValidationError) as ctx:
            PipelineConfig()
        self.assertIn("input_path", str(ctx.exception))

    def test_non_existent_input_path_rejected(self):
        fake_path = Path("non_existent_path_xyz_99999")
        with self.assertRaises(ValidationError) as ctx:
            PipelineConfig(input_path=fake_path)
        self.assertIn("input_path does not exist", str(ctx.exception))

    def test_invalid_enum_value_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with self.assertRaises(ValidationError) as ctx:
                PipelineConfig(input_path=temp_path, mode="UNSUPPORTED_MODE")
            self.assertIn("mode", str(ctx.exception))

            with self.assertRaises(ValidationError) as ctx2:
                PipelineConfig(input_path=temp_path, device="QUANTUM_CPU")
            self.assertIn("device", str(ctx2.exception))

    def test_valid_enum_values_accepted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            for mode in ExecutionMode:
                for device in ExecutionDevice:
                    cfg = PipelineConfig(input_path=temp_path, mode=mode, device=device)
                    self.assertEqual(cfg.mode, mode)
                    self.assertEqual(cfg.device, device)

    def test_empty_feature_columns_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            with self.assertRaises(ValidationError) as ctx:
                PipelineConfig(input_path=temp_path, feature_columns=[])
            self.assertIn("feature_columns must contain at least one column", str(ctx.exception))

    def test_dataclass_vs_pydantic_validation_comparison(self):
        dataclass_obj = DataclassPipelineConfig(
            input_path="fake_path",
            batch_size=-100,
            confidence_threshold=999.0,
        )
        self.assertEqual(dataclass_obj.batch_size, -100)

        with self.assertRaises(ValidationError):
            PipelineConfig(
                input_path=Path("fake_path"),
                batch_size=-100,
                confidence_threshold=999.0,
            )
