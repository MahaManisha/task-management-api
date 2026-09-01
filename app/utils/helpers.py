from datetime import datetime, timezone
from typing import Dict, List, Union


def get_current_timestamp() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def generate_id(existing_items: Union[Dict[int, object], List[object]]) -> int:
    """Generate a simple sequential integer ID for in-memory storage entities."""
    if not existing_items:
        return 1
    if isinstance(existing_items, dict):
        return max(existing_items.keys()) + 1
    return len(existing_items) + 1
