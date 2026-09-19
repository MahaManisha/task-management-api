import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tempfile
from pydantic import ValidationError
from app.config import (
    PipelineConfig,
    ImageSize,
    ExecutionMode,
    ExecutionDevice,
    DataclassPipelineConfig,
)



def run_demo():
    print("=" * 70)
    print(" D4: TYPE HINTS & PYDANTIC CONFIGURATION VALIDATION DEMO")
    print("=" * 70)

    # 1. Valid Configuration Example
    print("\n1. VALID CONFIGURATION DEMONSTRATION")
    print("-" * 50)
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
        print("Successfully loaded valid configuration:")
        print(f"  Input Path           : {valid_config.input_path}")
        print(f"  Batch Size           : {valid_config.batch_size}")
        print(f"  Image Size           : {valid_config.image_size.width}x{valid_config.image_size.height}")
        print(f"  Feature Columns      : {valid_config.feature_columns}")
        print(f"  Execution Mode       : {valid_config.mode.value}")
        print(f"  Execution Device     : {valid_config.device.value}")
        print(f"  Confidence Threshold : {valid_config.confidence_threshold}")

    # 2. Invalid Configuration Examples
    print("\n2. DELIBERATELY INVALID CONFIGURATIONS (PYDANTIC RUNTIME VALIDATION)")
    print("-" * 70)

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
        print(f"\n[Case] {label}:")
        try:
            PipelineConfig(**kwargs)
            print("  FAIL: Expected ValidationError but configuration was accepted.")
        except ValidationError as e:
            for err in e.errors():
                location = " -> ".join(str(loc) for loc in err["loc"])
                msg = err["msg"]
                err_type = err["type"]
                print(f"  WHERE : Field '{location}'")
                print(f"  WHAT  : {err_type}")
                print(f"  WHY   : {msg}")

    # 3. Dataclass vs Pydantic Runtime Validation Comparison
    print("\n3. DATACLASS VS PYDANTIC RUNTIME VALIDATION COMPARISON")
    print("-" * 70)
    print("Instantiating Dataclass with invalid values (non-existent path, batch_size=-50, threshold=99.0)...")
    dataclass_cfg = DataclassPipelineConfig(
        input_path="non_existent_file.txt",
        batch_size=-50,
        confidence_threshold=99.0,
    )
    print("  Result: Dataclass initialized without error!")
    print(f"  Unvalidated state: batch_size={dataclass_cfg.batch_size}, threshold={dataclass_cfg.confidence_threshold}")
    print("  Explanation: Standard Python dataclasses structure data but perform NO runtime type or constraint validation on initialization.")
    print("  Contrast: Pydantic BaseModel performs strict runtime type coercion and constraint validation when initialized.")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
