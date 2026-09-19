from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Task Management API"
    VERSION: str = "1.0.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()


class ExecutionMode(str, Enum):
    TRAIN = "TRAIN"
    VALIDATE = "VALIDATE"
    INFERENCE = "INFERENCE"


class ExecutionDevice(str, Enum):
    CPU = "CPU"
    CUDA = "CUDA"
    MPS = "MPS"


class ImageSize(BaseModel):
    width: int = Field(default=224, description="Image width in pixels")
    height: int = Field(default=224, description="Image height in pixels")

    @field_validator("width", "height")
    @classmethod
    def validate_dimension(cls, v: int, info: ValidationInfo) -> int:
        if v <= 0:
            raise ValueError(f"image_size {info.field_name} must be greater than 0")
        return v


class PipelineConfig(BaseModel):
    input_path: Path = Field(..., description="Path to input data directory or file")
    batch_size: int = Field(default=32, description="Processing batch size")
    image_size: ImageSize = Field(default_factory=ImageSize)
    feature_columns: list[str] = Field(default_factory=lambda: ["title", "description", "status"])
    mode: ExecutionMode = Field(default=ExecutionMode.INFERENCE)
    device: ExecutionDevice = Field(default=ExecutionDevice.CPU)
    confidence_threshold: float = Field(default=0.8, description="Confidence threshold between 0.0 and 1.0")

    @field_validator("input_path")
    @classmethod
    def validate_input_path_exists(cls, v: Path) -> Path:
        path = Path(v)
        if not path.exists():
            raise ValueError(f"input_path does not exist: '{v}'")
        return path

    @field_validator("batch_size")
    @classmethod
    def validate_batch_size_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("batch_size must be greater than 0")
        return v

    @field_validator("feature_columns")
    @classmethod
    def validate_feature_columns_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("feature_columns must contain at least one column")
        return v

    @field_validator("confidence_threshold")
    @classmethod
    def validate_confidence_threshold_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("confidence_threshold must be between 0.0 and 1.0")
        return v


@dataclass
class DataclassPipelineConfig:
    """Demonstration dataclass showing that standard Python dataclasses do not validate inputs at runtime."""
    input_path: str
    batch_size: int
    confidence_threshold: float