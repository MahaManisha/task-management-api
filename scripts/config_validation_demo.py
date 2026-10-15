import logging
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError
from app.config import (
    PipelineConfig,
    ImageSize,
    ExecutionMode,
    ExecutionDevice,
    DataclassPipelineConfig,
)
from app.utils.logging_config import configure_logging

logger = configure_logging(environment="development")


def run_demo():
    logger.info("=" * 70)
    logger.info(" D4: TYPE HINTS & PYDANTIC CONFIGURATION VALIDATION DEMO")
    logger.info("=" * 70)

    # 1. Valid Configuration Example
    logger.info("1. VALID CONFIGURATION DEMONSTRATION")
    logger.info("-" * 50)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        valid_config = PipelineConfig(
            input_path=temp_path,
            batch_size=64,
            image_size=ImageSize(width=512, height=512),
            feature_columns=["title", "description", "priority"],
            mode=ExecutionMode.TRAIN,
            device=ExecutionDevice.CUDA,
            confidence_threshold=0.95,
        )
        logger.info("Successfully loaded valid configuration:")
        logger.info(f"  Input Path           : {valid_config.input_path}")
        logger.info(f"  Batch Size           : {valid_config.batch_size}")
        logger.info(f"  Image Size           : {valid_config.image_size.width}x{valid_config.image_size.height}")
        logger.info(f"  Feature Columns      : {valid_config.feature_columns}")
        logger.info(f"  Execution Mode       : {valid_config.mode.value}")
        logger.info(f"  Execution Device     : {valid_config.device.value}")
        logger.info(f"  Confidence Threshold : {valid_config.confidence_threshold}")

    # 2. Invalid Configuration Examples
    logger.info("2. DELIBERATELY INVALID CONFIGURATIONS (PYDANTIC RUNTIME VALIDATION)")
    logger.info("-" * 70)

    invalid_cases = [
        (
            "Non-existent Input Path",
            {"input_path": Path("non_existent_folder_xyz_12345")},
        ),
        (
            "Invalid Batch Size (Zero or Negative)",
            {"input_path": Path("."), "batch_size": 0},
        ),
        (
            "Out-of-Range Confidence Threshold",
            {"input_path": Path("."), "confidence_threshold": 1.5},
        ),
        (
            "Invalid Execution Mode Enum",
            {"input_path": Path("."), "mode": "SUPERVISED"},
        ),
        (
            "Wrong Data Type for Batch Size",
            {"input_path": Path("."), "batch_size": "not_an_int"},
        ),
    ]

    for label, kwargs in invalid_cases:
        logger.info(f"[Case] {label}:")
        try:
            PipelineConfig(**kwargs)
            logger.warning("  FAIL: Expected ValidationError but configuration was accepted.")
        except ValidationError as e:
            for err in e.errors():
                location = " -> ".join(str(loc) for loc in err["loc"])
                msg = err["msg"]
                err_type = err["type"]
                logger.info(f"  WHERE : Field '{location}'")
                logger.info(f"  WHAT  : {err_type}")
                logger.info(f"  WHY   : {msg}")

    # 3. Dataclass vs Pydantic Runtime Validation Comparison
    logger.info("3. DATACLASS VS PYDANTIC RUNTIME VALIDATION COMPARISON")
    logger.info("-" * 70)
    logger.info("Instantiating Dataclass with invalid values (non-existent path, batch_size=-50, threshold=99.0)...")
    dataclass_cfg = DataclassPipelineConfig(
        input_path="non_existent_file.txt",
        batch_size=-50,
        confidence_threshold=99.0,
    )
    logger.info("  Result: Dataclass initialized without error!")
    logger.info(f"  Unvalidated state: batch_size={dataclass_cfg.batch_size}, threshold={dataclass_cfg.confidence_threshold}")
    logger.info("  Explanation: Standard Python dataclasses structure data but perform NO runtime type or constraint validation on initialization.")
    logger.info("  Contrast: Pydantic BaseModel performs strict runtime type coercion and constraint validation when initialized.")
    logger.info("=" * 70)


if __name__ == "__main__":
    run_demo()
