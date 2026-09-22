from dataclasses import dataclass, field
from typing import Optional
from app.utils.helpers import get_current_timestamp


@dataclass
class Task:
    id: int
    title: str
    description: Optional[str] = None
    completed: bool = False
    user_id: Optional[int] = None
    created_at: str = field(default_factory=get_current_timestamp)
