import unittest
from app.utils.validators import validate_email, validate_task_title


class TestValidators(unittest.TestCase):
    def test_validate_email_valid(self):
        self.assertTrue(validate_email("user@example.com"))
        self.assertTrue(validate_email("john.doe+test@domain.co.uk"))

    def test_validate_email_invalid(self):
        self.assertFalse(validate_email("invalid-email"))
        self.assertFalse(validate_email("user@domain"))
        self.assertFalse(validate_email(""))

    def test_validate_task_title_valid(self):
        self.assertTrue(validate_task_title("Complete Triton Internship Task"))
        self.assertTrue(validate_task_title("A"))

    def test_validate_task_title_invalid(self):
        self.assertFalse(validate_task_title(""))
        self.assertFalse(validate_task_title("   "))
        self.assertFalse(validate_task_title("a" * 101))


if __name__ == "__main__":
    unittest.main()
