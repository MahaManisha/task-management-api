import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.decorators import timeit, retry
from app.utils.context_managers import PipelineResourceContext, managed_pipeline_file
from app.utils.cache import get_pipeline_step_config
from app.services.pipeline import Pipeline
from app.services.pipeline_stages import (
    TaskValidationStep,
    TaskTransformationStep,
    TaskProcessingStep,
    TaskBatchFileStep,
    ReliableTaskFetcherStep,
)


def run_demo():
    print("=" * 75)
    print(" D5: DECORATORS, CONTEXT MANAGERS & CACHING DEMONSTRATION")
    print("=" * 75)

    # 1. @timeit Decorator Demo
    print("\n1. @timeit DECORATOR DEMONSTRATION")
    print("-" * 50)

    @timeit
    def compute_heavy_task(n: int) -> int:
        """Compute the sum of squares up to n."""
        return sum(i * i for i in range(n))

    result = compute_heavy_task(100_000)
    print(f"Function Name     : {compute_heavy_task.__name__}")
    print(f"Function Doc      : {compute_heavy_task.__doc__}")
    print(f"Function Result   : {result}")
    print("  -> Logged execution duration using standard Python logging.")

    # 2. @retry Decorator Demo
    print("\n2. @retry(max_attempts=N) DECORATOR DEMONSTRATION")
    print("-" * 50)

    attempts_count = 0

    @retry(max_attempts=3)
    def unreliable_operation():
        """Simulate an operation that succeeds on attempt 3."""
        nonlocal attempts_count
        attempts_count += 1
        if attempts_count < 3:
            raise ConnectionError(f"Transient error (attempt {attempts_count})")
        return "SUCCESS_DATA"

    print("Executing unreliable operation (max_attempts=3)...")
    res = unreliable_operation()
    print(f"Final Result      : {res}")
    print(f"Attempts Needed   : {attempts_count}")

    print("\nExecuting operation that always fails (max_attempts=2)...")
    @retry(max_attempts=2)
    def failing_operation():
        raise ValueError("Permanent failure")

    try:
        failing_operation()
    except ValueError as e:
        print(f"Caught Final Exception as expected: {e}")

    # 3. Context Manager Demo
    print("\n3. RESOURCE CONTEXT MANAGER DEMONSTRATION")
    print("-" * 50)
    with tempfile.TemporaryDirectory() as temp_dir:
        sample_path = Path(temp_dir) / "demo_resource.txt"
        print(f"Managing resource at: {sample_path.name}")

        print("Entering context block...")
        with PipelineResourceContext(resource_name="DemoResource", file_path=sample_path) as ctx:
            print(f"  Inside context, is_acquired={ctx.is_acquired}")
            if ctx._file_handle:
                ctx._file_handle.write("Resource Data Line\n")

        print(f"Exited context block, is_acquired={ctx.is_acquired}")

        print("\nDemonstrating cleanup upon exception inside context block...")
        try:
            with PipelineResourceContext(resource_name="ExceptionResource") as ctx:
                print(f"  Inside context, is_acquired={ctx.is_acquired}")
                raise RuntimeError("Simulated error inside context")
        except RuntimeError as err:
            print(f"  Caught Exception: {err}")
            print(f"  After Exception, is_acquired={ctx.is_acquired}")

    # 4. lru_cache Caching Demo
    print("\n4. CACHING WITH lru_cache DEMONSTRATION")
    print("-" * 50)
    get_pipeline_step_config.cache_clear()

    print("Initial Call (Cache Miss):")
    cfg1 = get_pipeline_step_config("TaskValidationStep", "production")
    print(f"  Config Result : {cfg1}")
    print(f"  Cache Stats   : {get_pipeline_step_config.cache_info()}")

    print("\nSecond Call with Same Arguments (Cache Hit):")
    cfg2 = get_pipeline_step_config("TaskValidationStep", "production")
    print(f"  Config Result : {cfg2}")
    print(f"  Cache Stats   : {get_pipeline_step_config.cache_info()}")

    print("\nClearing Cache...")
    get_pipeline_step_config.cache_clear()
    print(f"  Cache Stats after clear : {get_pipeline_step_config.cache_info()}")

    # 5. Full Pipeline Integration Demo
    print("\n5. ACTUAL PIPELINE INTEGRATION DEMONSTRATION")
    print("-" * 50)
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
        print(f"Input Task Data  : {input_data}")
        output_data = pipeline.run(input_data)
        print(f"Output Task Data : {output_data}")
        print(f"Batch File Saved : {batch_file.exists()}")

    print("=" * 75)
    print(" DEMO COMPLETED SUCCESSFULLY")
    print("=" * 75)


if __name__ == "__main__":
    run_demo()
