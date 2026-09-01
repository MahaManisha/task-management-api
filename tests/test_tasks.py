import unittest
from pydantic import ValidationError
from app.schemas.task import TaskCreate
from app.services.task_service import (
    create_task,
    get_task,
    get_tasks,
    update_task_completion,
    clear_tasks_db,
)


class TestTaskService(unittest.TestCase):
    def setUp(self):
        clear_tasks_db()

    def test_create_and_get_task(self):
        task_in = TaskCreate(title="Set up Python FastAPI", description="Complete task 2")
        created = create_task(task_in)

        self.assertEqual(created.id, 1)
        self.assertEqual(created.title, "Set up Python FastAPI")
        self.assertFalse(created.completed)

        fetched = get_task(1)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.title, "Set up Python FastAPI")

    def test_create_task_invalid_title(self):
        with self.assertRaises((ValueError, ValidationError)):
            TaskCreate(title="")

    def test_update_task_completion(self):
        task_in = TaskCreate(title="Test Task")
        created = create_task(task_in)

        updated = update_task_completion(created.id, True)
        self.assertIsNotNone(updated)
        self.assertTrue(updated.completed)


if __name__ == "__main__":
    unittest.main()
