from dataclasses import dataclass, field
from app.utils.helpers import get_current_timestamp


@dataclass
class User:
    id: int
    name: str
    email: str
    created_at: str = field(default_factory=get_current_timestamp)
