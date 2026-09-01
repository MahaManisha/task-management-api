import unittest
from app.schemas.user import UserCreate
from app.services.user_service import create_user, get_user, get_users, clear_users_db


class TestUserService(unittest.TestCase):
    def setUp(self):
        clear_users_db()

    def test_create_and_get_user(self):
        user_in = UserCreate(name="Alice Smith", email="alice@example.com")
        created = create_user(user_in)

        self.assertEqual(created.id, 1)
        self.assertEqual(created.name, "Alice Smith")
        self.assertEqual(created.email, "alice@example.com")

        fetched = get_user(1)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Alice Smith")

    def test_create_user_invalid_email(self):
        user_in = UserCreate(name="Bob", email="not-an-email")
        with self.assertRaises(ValueError):
            create_user(user_in)

    def test_get_all_users(self):
        create_user(UserCreate(name="User 1", email="user1@example.com"))
        create_user(UserCreate(name="User 2", email="user2@example.com"))

        users = get_users()
        self.assertEqual(len(users), 2)


if __name__ == "__main__":
    unittest.main()
