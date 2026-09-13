from typing import Any, Dict, List, Optional
from app.services.pipeline_stages import PipelineStage


class Pipeline:
    """Reusable data processing pipeline executing stages sequentially."""

    def __init__(self, stages: Optional[List[PipelineStage]] = None):
        self._stages: List[PipelineStage] = []
        if stages:
            for stage in stages:
                self.add_stage(stage)

    @property
    def stages(self) -> List[PipelineStage]:
        return list(self._stages)

    def add_stage(self, stage: PipelineStage) -> "Pipeline":
        if not isinstance(stage, PipelineStage):
            raise TypeError("Stage must be an instance of PipelineStage.")
        self._stages.append(stage)
        return self

    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        current_data = data.copy() if isinstance(data, dict) else data
        for stage in self._stages:
            current_data = stage.process(current_data)
        return current_data
