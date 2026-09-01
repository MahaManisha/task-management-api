import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email(email: str) -> bool:
    """Validate email address format."""
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_task_title(title: str) -> bool:
    """Validate task title (must be non-empty string between 1 and 100 characters)."""
    if not title or not isinstance(title, str):
        return False
    stripped = title.strip()
    return 1 <= len(stripped) <= 100
