import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger(__name__)


def timeit(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that logs the execution duration of a function with structured metadata."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            duration = time.perf_counter() - start_time
            duration_ms = round(duration * 1000, 2)
            logger.info(
                f"Function '{func.__name__}' executed in {duration:.6f} seconds ({duration_ms} ms)",
                extra={"event": "function_timing", "function_name": func.__name__, "duration_ms": duration_ms},
            )

    return wrapper


def retry(max_attempts: int = 3) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Parameterized decorator that retries a function upon exception up to max_attempts."""
    if not isinstance(max_attempts, int):
        raise TypeError("max_attempts must be an integer.")
    if max_attempts <= 0:
        raise ValueError("max_attempts must be greater than zero.")

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception = RuntimeError("No attempts made.")
            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        logger.info(
                            f"Function '{func.__name__}' succeeded on attempt {attempt}/{max_attempts}.",
                            extra={"event": "retry_success", "attempt": attempt, "max_attempts": max_attempts},
                        )
                    return result
                except Exception as exc:
                    last_exception = exc
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} for function '{func.__name__}' failed with error: {exc}",
                        extra={"event": "retry_attempt_failed", "attempt": attempt, "max_attempts": max_attempts, "error": str(exc)},
                    )
                    if attempt == max_attempts:
                        logger.error(
                            f"Function '{func.__name__}' failed after {max_attempts} attempts. Re-raising exception.",
                            extra={"event": "retry_exhausted", "max_attempts": max_attempts, "error": str(exc)},
                        )
                        raise last_exception

            raise last_exception

        return wrapper

    return decorator
