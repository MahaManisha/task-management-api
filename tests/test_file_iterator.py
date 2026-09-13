import tempfile
import unittest
from pathlib import Path

from app.utils.file_iterator import (
    FileBatchIterator,
    load_all_files,
    read_files_in_batches,
)


class TestFileBatchIterator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_dummy_files(self, count: int):
        for i in range(count):
            file_path = self.dir_path / f"file_{i:04d}.txt"
            file_path.write_text(f"Sample content for file {i}", encoding="utf-8")

    def test_correct_batch_size(self):
        self._create_dummy_files(10)
        iterator = FileBatchIterator(self.dir_path, batch_size=3)
        batches = list(iterator)

        self.assertEqual(len(batches), 4)
        self.assertEqual(len(batches[0]), 3)
        self.assertEqual(len(batches[1]), 3)
        self.assertEqual(len(batches[2]), 3)

    def test_all_files_eventually_processed(self):
        self._create_dummy_files(25)
        iterator = FileBatchIterator(self.dir_path, batch_size=7)

        processed_files = []
        for batch in iterator:
            for filename, _ in batch:
                processed_files.append(filename)

        self.assertEqual(len(processed_files), 25)
        expected_files = sorted([f"file_{i:04d}.txt" for i in range(25)])
        self.assertEqual(processed_files, expected_files)

    def test_final_batch_fewer_items(self):
        self._create_dummy_files(10)
        iterator = FileBatchIterator(self.dir_path, batch_size=3)
        batches = list(iterator)

        self.assertEqual(len(batches[-1]), 1)

    def test_empty_folder_behavior(self):
        iterator = FileBatchIterator(self.dir_path, batch_size=5)
        batches = list(iterator)
        self.assertEqual(len(batches), 0)

        fresh_iterator = FileBatchIterator(self.dir_path, batch_size=5)
        with self.assertRaises(StopIteration):
            next(fresh_iterator)

    def test_iter_and_next_protocol(self):
        self._create_dummy_files(5)
        iterator = FileBatchIterator(self.dir_path, batch_size=2)

        iter_obj = iter(iterator)
        self.assertIs(iter_obj, iterator)

        batch1 = next(iter_obj)
        self.assertEqual(len(batch1), 2)
        self.assertEqual(batch1[0][0], "file_0000.txt")

        batch2 = next(iter_obj)
        self.assertEqual(len(batch2), 2)
        self.assertEqual(batch2[0][0], "file_0002.txt")

        batch3 = next(iter_obj)
        self.assertEqual(len(batch3), 1)
        self.assertEqual(batch3[0][0], "file_0004.txt")

        with self.assertRaises(StopIteration):
            next(iter_obj)

    def test_generator_function(self):
        self._create_dummy_files(8)
        generator = read_files_in_batches(self.dir_path, batch_size=3)
        batches = list(generator)

        self.assertEqual(len(batches), 3)
        self.assertEqual(len(batches[0]), 3)
        self.assertEqual(len(batches[1]), 3)
        self.assertEqual(len(batches[2]), 2)

    def test_eager_load_all_files(self):
        self._create_dummy_files(5)
        all_files = load_all_files(self.dir_path)
        self.assertEqual(len(all_files), 5)

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            FileBatchIterator(self.dir_path, batch_size=0)

        non_existent = self.dir_path / "does_not_exist"
        with self.assertRaises(FileNotFoundError):
            FileBatchIterator(non_existent, batch_size=5)


if __name__ == "__main__":
    unittest.main()
