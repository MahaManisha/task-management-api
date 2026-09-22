import logging
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.decorators import timeit, retry
from app.utils.context_managers import PipelineResourceContext, managed_pipeline_file
from app.utils.cache import get_pipeline_step_config
from app.utils.logging_config import configure_logging
from app.services.pipeline import Pipeline
from app.services.pipeline_stages import (
    TaskValidationStep,
    TaskTransformationStep,
    TaskProcessingStep,
    TaskBatchFileStep,
    ReliableTaskFetcherStep,
)

logger = configure_logging(environment="development")


def run_demo():
    logger.info("=" * 75)
    logger.info(" D5: DECORATORS, CONTEXT MANAGERS & CACHING DEMONSTRATION")
    logger.info("=" * 75)

    # 1. @timeit Decorator Demo
    logger.info("1. @timeit DECORATOR DEMONSTRATION")
    logger.info("-" * 50)

    @timeit
    def compute_heavy_task(n: int) -> int:
        """Compute the sum of squares up to n."""
        return sum(i * i for i in range(n))

    result = compute_heavy_task(100_000)
    logger.info(f"Function Name     : {compute_heavy_task.__name__}")
    logger.info(f"Function Doc      : {compute_heavy_task.__doc__}")
    logger.info(f"Function Result   : {result}")
    logger.info("  -> Logged execution duration using standard Python logging.")

    # 2. @retry Decorator Demo
    logger.info("2. @retry(max_attempts=N) DECORATOR DEMONSTRATION")
    logger.info("-" * 50)

    attempts_count = 0

    @retry(max_attempts=3)
    def unreliable_operation():
        """Simulate an operation that succeeds on attempt 3."""
        nonlocal attempts_count
        attempts_count += 1
        if attempts_count < 3:
            raise ConnectionError(f"Transient error (attempt {attempts_count})")
        return "SUCCESS_DATA"

    logger.info("Executing unreliable operation (max_attempts=3)...")
    res = unreliable_operation()
    logger.info(f"Final Result      : {res}")
    logger.info(f"Attempts Needed   : {attempts_count}")

    logger.info("Executing operation that always fails (max_attempts=2)...")
    @retry(max_attempts=2)
    def failing_operation():
        raise ValueError("Permanent failure")

    try:
        failing_operation()
    except ValueError as e:
        logger.info(f"Caught Final Exception as expected: {e}")

    # 3. Context Manager Demo
    logger.info("3. RESOURCE CONTEXT MANAGER DEMONSTRATION")
    logger.info("-" * 50)
    with tempfile.TemporaryDirectory() as temp_dir:
        sample_path = Path(temp_dir) / "demo_resource.txt"
        logger.info(f"Managing resource at: {sample_path.name}")

        logger.info("Entering context block...")
        with PipelineResourceContext(resource_name="DemoResource", file_path=sample_path) as ctx:
            logger.info(f"  Inside context, is_acquired={ctx.is_acquired}")
            if ctx._file_handle:
                ctx._file_handle.write("Resource Data Line\n")

        logger.info(f"Exited context block, is_acquired={ctx.is_acquired}")

        logger.info("Demonstrating cleanup upon exception inside context block...")
        try:
            with PipelineResourceContext(resource_name="ExceptionResource") as ctx:
                logger.info(f"  Inside context, is_acquired={ctx.is_acquired}")
                raise RuntimeError("Simulated error inside context")
        except RuntimeError as err:
            logger.info(f"  Caught Exception: {err}")
            logger.info(f"  After Exception, is_acquired={ctx.is_acquired}")

    # 4. lru_cache Caching Demo
    logger.info("4. CACHING WITH lru_cache DEMONSTRATION")
    logger.info("-" * 50)
    get_pipeline_step_config.cache_clear()

    logger.info("Initial Call (Cache Miss):")
    cfg1 = get_pipeline_step_config("TaskValidationStep", "production")
    logger.info(f"  Config Result : {cfg1}")
    logger.info(f"  Cache Stats   : {get_pipeline_step_config.cache_info()}")

    logger.info("Second Call with Same Arguments (Cache Hit):")
    cfg2 = get_pipeline_step_config("TaskValidationStep", "production")
    logger.info(f"  Config Result : {cfg2}")
    logger.info(f"  Cache Stats   : {get_pipeline_step_config.cache_info()}")

    logger.info("Clearing Cache...")
    get_pipeline_step_config.cache_clear()
    logger.info(f"  Cache Stats after clear : {get_pipeline_step_config.cache_info()}")

    # 5. Full Pipeline Integration Demo
    logger.info("5. ACTUAL PIPELINE INTEGRATION DEMONSTRATION")
    logger.info("-" * 50)
    with tempfile.TemporaryDirectory() as temp_dir:
        batch_file = Path(temp_dir) / "pipeline_batch.txt"
        pipeline = Pipeline(
            ReliableTaskFetcherStep(max_attempts=3, fail_count=1),
            TaskValidationStep(),
            TaskTransformationStep(),
            TaskBatchFileStep(batch_file_path=batch_file),
            TaskProcessingStep(status_label="PIPELINE_COMPLETE"),
        )

        input_data = {"title": "   Integrated D5 Pipeline Task   "}
        logger.info(f"Input Task Data  : {input_data}")
        output_data = pipeline.run(input_data)
        logger.info(f"Output Task Data : {output_data}")
        logger.info(f"Batch File Saved : {batch_file.exists()}")

    logger.info("=" * 75)
    logger.info(" DEMO COMPLETED SUCCESSFULLY")
    logger.info("=" * 75)


if __name__ == "__main__":
    run_demo()
