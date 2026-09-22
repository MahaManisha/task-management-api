import logging
import time
from typing import Any, Dict, List, Optional, Union
from app.services.pipeline_stages import Step

logger = logging.getLogger(__name__)


class Pipeline:
    """Reusable data processing pipeline composed of interchangeable Step objects with structured logging instrumentation."""

    def __init__(self, *args: Union[Step, List[Step]], steps: Optional[List[Step]] = None):
        self._steps: List[Step] = []
        if steps is not None:
            for step in steps:
                self.add_step(step)
        for arg in args:
            if isinstance(arg, list):
                for step in arg:
                    self.add_step(step)
            else:
                self.add_step(arg)

    @property
    def steps(self) -> List[Step]:
        return list(self._steps)

    def add_step(self, step: Step) -> "Pipeline":
        if not isinstance(step, Step):
            raise TypeError("Step must be an instance of Step.")
        self._steps.append(step)
        return self

    def add_stage(self, stage: Step) -> "Pipeline":
        """Alias for add_step for backward compatibility."""
        return self.add_step(stage)

    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        current_data = data.copy() if isinstance(data, dict) else data
        start_time = time.perf_counter()
        logger.info(
            "Pipeline execution started",
            extra={"event": "pipeline_start", "step_count": len(self._steps)},
        )

        for step in self._steps:
            step_name = step.__class__.__name__
            logger.info(
                f"Executing pipeline step '{step_name}'",
                extra={"event": "step_start", "step": step_name},
            )
            try:
                current_data = step.process(current_data)
                logger.info(
                    f"Completed pipeline step '{step_name}'",
                    extra={"event": "step_complete", "step": step_name},
                )
            except Exception as exc:
                logger.exception(
                    f"Pipeline execution failed at step '{step_name}': {exc}",
                    extra={
                        "event": "pipeline_failure",
                        "step": step_name,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    },
                )
                raise

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            f"Pipeline execution completed successfully in {duration_ms} ms",
            extra={"event": "pipeline_complete", "duration_ms": duration_ms},
        )
        return current_data
