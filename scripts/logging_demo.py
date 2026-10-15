import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.pipeline import Pipeline
from app.services.pipeline_stages import (
    TaskValidationStep,
    TaskTransformationStep,
    TaskProcessingStep,
    TaskBatchFileStep,
    ReliableTaskFetcherStep,
)
from app.utils.exceptions import TaskManagementError
from app.utils.logging_config import configure_logging, get_logger

LOG_FILE_PATH = Path(__file__).resolve().parent.parent / "logs" / "pipeline.log"


def run_demo():
    # Configure logging for production mode with structured JSON logs saved to file
    logger = configure_logging(
        environment="production",
        log_file=LOG_FILE_PATH,
        level=10,  # DEBUG
    )

    demo_logger = get_logger("scripts.logging_demo")
    demo_logger.info("=" * 75, extra={"event": "demo_start"})
    demo_logger.info("D7: STRUCTURED LOGGING & PRODUCTION DEBUGGING DEMONSTRATION", extra={"event": "demo_title"})
    demo_logger.info("=" * 75, extra={"event": "demo_divider"})

    with tempfile.TemporaryDirectory() as temp_dir:
        batch_file = Path(temp_dir) / "demo_batch.txt"

        # 1. Successful Pipeline Execution Run
        demo_logger.info("1. EXECUTING SUCCESSFUL PIPELINE RUN", extra={"event": "demo_successful_run_start"})
        successful_pipeline = Pipeline(
            TaskValidationStep(),
            TaskTransformationStep(),
            TaskBatchFileStep(batch_file_path=batch_file),
            TaskProcessingStep(status_label="LOGGING_DEMO_SUCCESS"),
        )

        input_data = {"title": "  Structured Logging Task  "}
        demo_logger.info("Running pipeline with valid input", extra={"event": "input_payload", "input_title": input_data["title"]})
        result = successful_pipeline.run(input_data)
        demo_logger.info("Successful pipeline run output", extra={"event": "output_payload", "output": result})

        # 2. Deliberately Failing Pipeline Execution Run
        demo_logger.info("2. EXECUTING DELIBERATELY FAILING PIPELINE RUN", extra={"event": "demo_failed_run_start"})
        failing_pipeline = Pipeline(
            TaskValidationStep(),
            ReliableTaskFetcherStep(max_attempts=3, fail_count=5),  # Will exhaust retries and fail
        )

        demo_logger.info("Running pipeline expecting failure...", extra={"event": "input_failing_payload"})
        try:
            failing_pipeline.run({"title": "Failing Task"})
        except TaskManagementError as exc:
            demo_logger.error(
                "Caught expected pipeline failure in demo runner",
                extra={
                    "event": "demo_caught_failure",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "log_file_location": str(LOG_FILE_PATH),
                },
            )

    demo_logger.info(f"Log output persisted to: {LOG_FILE_PATH}", extra={"event": "log_file_persisted", "path": str(LOG_FILE_PATH)})
    demo_logger.info("=" * 75, extra={"event": "demo_end"})
    demo_logger.info("DEMO COMPLETED SUCCESSFULLY", extra={"event": "demo_complete"})


if __name__ == "__main__":
    run_demo()
