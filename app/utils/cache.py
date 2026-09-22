from functools import lru_cache
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Predefined immutable pipeline configuration rules
DEFAULT_PIPELINE_RULES: Dict[str, Dict[str, Any]] = {
    "TaskValidationStep": {
        "title_required": True,
        "max_title_length": 100,
        "min_title_length": 1,
    },
    "TaskTransformationStep": {
        "strip_whitespace": True,
        "default_completed": False,
    },
    "TaskProcessingStep": {
        "status_label": "PROCESSED",
        "set_processed_flag": True,
    },
}


@lru_cache(maxsize=128)
def get_pipeline_step_config(step_name: str, environment: str = "production") -> Dict[str, Any]:
    """Retrieve default configuration parameters for a given pipeline step.

    CACHING DESIGN & SAFETY DOCUMENTATION:
    --------------------------------------
    1. Why Safe to Cache:
       The configuration output returned for a given (step_name, environment) pair is deterministic
       and immutable across pipeline execution cycles.

    2. Benefit of Caching:
       Repeated pipeline invocations avoid re-parsing or re-querying configuration defaults,
       executing metadata lookups in O(1) time.

    3. Dangers of Caching Mutable Data:
       If a function returns a mutable dictionary or list, mutating the returned object in one place
       will mutate the cached reference for all subsequent callers across the entire application!
       To ensure safety, callers should treat returned dictionaries as read-only or make explicit copies.

    4. Invalidation & Stale Data Concerns:
       If underlying environment settings change at runtime, cached results become stale.
       In such cases, caller must invoke `get_pipeline_step_config.cache_clear()` to force cache invalidation.

    5. Bounded Cache Memory Considerations:
       Using `@lru_cache(maxsize=128)` prevents unbounded memory usage. Least recently used items
       are automatically evicted when the cache capacity (128 entries) is reached.
    """
    logger.info(f"Cache miss: Computing configuration for step '{step_name}' in environment '{environment}'")
    base_config = DEFAULT_PIPELINE_RULES.get(step_name, {"enabled": True}).copy()
    base_config["environment"] = environment
    return base_config
