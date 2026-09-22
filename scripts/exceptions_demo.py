import logging
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_pipeline_config
from app.services.pipeline import Pipeline
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
from app.utils.logging_config import configure_logging

logger = configure_logging(environment="development")


def run_demo():
    logger.info("=" * 75)
    logger.info(" D6: EXCEPTION HIERARCHIES & ERROR DESIGN DEMONSTRATION")
    logger.info("=" * 75)

    # 1. DataValidationError Demo
    logger.info("1. DataValidationError DEMONSTRATION (Validation Layer)")
    logger.info("-" * 55)
    validator = TaskValidationStep()
    try:
        validator.process({"title": ""})
    except DataValidationError as exc:
        logger.info(f"Caught Specific Exception : {type(exc).__name__}")
        logger.info(f"Error Message             : {exc}")
        logger.info(f"Is TaskManagementError?   : {isinstance(exc, TaskManagementError)}")

    # 2. ConfigError & Exception Chaining Demo
    logger.info("2. ConfigError & EXCEPTION CHAINING DEMONSTRATION (Config Layer)")
    logger.info("-" * 55)
    try:
        load_pipeline_config(input_path=Path("non_existent_folder_abc"))
    except ConfigError as exc:
        logger.info(f"Caught Domain Exception   : {type(exc).__name__}")
        logger.info(f"Error Message             : {exc}")
        logger.info(f"Original Cause (__cause__): {type(exc.__cause__).__name__}")
        logger.info(f"Cause Details             : {exc.__cause__}")

    # 3. ProcessingError & try/except/else/finally Demo
    logger.info("3. ProcessingError & try / except / else / finally DEMONSTRATION")
    logger.info("-" * 55)
    with tempfile.TemporaryDirectory() as temp_dir:
        batch_file = Path(temp_dir) / "batch_records.txt"
        step = TaskBatchFileStep(batch_file_path=batch_file, simulate_io_error=True)

        logger.info("Executing step with simulated I/O failure...")
        try:
            step.process({"title": "Sample Pipeline Task"})
        except ProcessingError as exc:
            logger.info(f"  [except] Caught ProcessingError: {exc}")
            logger.info(f"  [except] Underlying __cause__ : {type(exc.__cause__).__name__} -> {exc.__cause__}")
        else:
            logger.info("  [else] Operation succeeded with no errors!")
        finally:
            logger.info("  [finally] Guaranteed cleanup block executed.")

    # 4. Polymorphic Base Exception Handling Demo
    logger.info("4. POLYMORPHIC BASE EXCEPTION CATCHING (TaskManagementError)")
    logger.info("-" * 55)
    pipeline = Pipeline(
        TaskValidationStep(),
        ReliableTaskFetcherStep(max_attempts=2, fail_count=3),
    )

    logger.info("Executing pipeline that will fail during processing...")
    try:
        pipeline.run({"title": "Valid Title"})
    except TaskManagementError as exc:
        logger.info(f"Polymorphically Caught Base Exception : {type(exc).__name__}")
        logger.info(f"Inherits from TaskManagementError    : {isinstance(exc, TaskManagementError)}")
        logger.info(f"Structured Error Message              : {exc}")

    logger.info("=" * 75)
    logger.info(" DEMO COMPLETED SUCCESSFULLY")
    logger.info("=" * 75)


if __name__ == "__main__":
    run_demo()
