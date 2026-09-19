from typing import Any, Dict, List, Optional, Union
from app.services.pipeline_stages import Step


class Pipeline:
    """Reusable data processing pipeline composed of interchangeable Step objects."""

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
        for step in self._steps:
            current_data = step.process(current_data)
        return current_data

