from typing import Dict, List, Optional
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.validators import validate_email
from app.utils.helpers import generate_id

# In-memory user database
_users_db: Dict[int, User] = {}


def create_user(user_in: UserCreate) -> User:
    """Create a new user after validating email format."""
    if not validate_email(user_in.email):
        raise ValueError("Invalid email format.")

    for user in _users_db.values():
        if user.email.lower() == user_in.email.lower():
            raise ValueError("Email already registered.")

    user_id = generate_id(_users_db)
    new_user = User(
        id=user_id,
        name=user_in.name,
        email=user_in.email,
    )
    _users_db[user_id] = new_user
    return new_user


def get_user(user_id: int) -> Optional[User]:
    """Retrieve a user by ID."""
    return _users_db.get(user_id)


def get_users() -> List[User]:
    """Retrieve all users."""
    return list(_users_db.values())


def clear_users_db() -> None:
    """Clear in-memory user database."""
    _users_db.clear()
