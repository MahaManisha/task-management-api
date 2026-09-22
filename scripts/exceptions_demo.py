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


def run_demo():
    print("=" * 75)
    print(" D6: EXCEPTION HIERARCHIES & ERROR DESIGN DEMONSTRATION")
    print("=" * 75)

    # 1. DataValidationError Demo
    print("\n1. DataValidationError DEMONSTRATION (Validation Layer)")
    print("-" * 55)
    validator = TaskValidationStep()
    try:
        validator.process({"title": ""})
    except DataValidationError as exc:
        print(f"Caught Specific Exception : {type(exc).__name__}")
        print(f"Error Message             : {exc}")
        print(f"Is TaskManagementError?   : {isinstance(exc, TaskManagementError)}")

    # 2. ConfigError & Exception Chaining Demo
    print("\n2. ConfigError & EXCEPTION CHAINING DEMONSTRATION (Config Layer)")
    print("-" * 55)
    try:
        load_pipeline_config(input_path=Path("non_existent_folder_abc"))
    except ConfigError as exc:
        print(f"Caught Domain Exception   : {type(exc).__name__}")
        print(f"Error Message             : {exc}")
        print(f"Original Cause (__cause__): {type(exc.__cause__).__name__}")
        print(f"Cause Details             : {exc.__cause__}")

    # 3. ProcessingError & try/except/else/finally Demo
    print("\n3. ProcessingError & try / except / else / finally DEMONSTRATION")
    print("-" * 55)
    with tempfile.TemporaryDirectory() as temp_dir:
        batch_file = Path(temp_dir) / "batch_records.txt"
        step = TaskBatchFileStep(batch_file_path=batch_file, simulate_io_error=True)

        print("Executing step with simulated I/O failure...")
        try:
            step.process({"title": "Sample Pipeline Task"})
        except ProcessingError as exc:
            print(f"  [except] Caught ProcessingError: {exc}")
            print(f"  [except] Underlying __cause__ : {type(exc.__cause__).__name__} -> {exc.__cause__}")
        else:
            print("  [else] Operation succeeded with no errors!")
        finally:
            print("  [finally] Guaranteed cleanup block executed.")

    # 4. Polymorphic Base Exception Handling Demo
    print("\n4. POLYMORPHIC BASE EXCEPTION CATCHING (TaskManagementError)")
    print("-" * 55)
    pipeline = Pipeline(
        TaskValidationStep(),
        ReliableTaskFetcherStep(max_attempts=2, fail_count=3),
    )

    print("Executing pipeline that will fail during processing...")
    try:
        pipeline.run({"title": "Valid Title"})
    except TaskManagementError as exc:
        print(f"Polymorphically Caught Base Exception : {type(exc).__name__}")
        print(f"Inherits from TaskManagementError    : {isinstance(exc, TaskManagementError)}")
        print(f"Structured Error Message              : {exc}")

    print("=" * 75)
    print(" DEMO COMPLETED SUCCESSFULLY")
    print("=" * 75)


if __name__ == "__main__":
    run_demo()
