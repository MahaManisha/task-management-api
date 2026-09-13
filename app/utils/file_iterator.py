import os
from pathlib import Path
from typing import Iterator, List, Tuple, Union


class FileBatchIterator:
    """Custom iterator that lazily reads files from a directory in batches."""

    def __init__(self, folder_path: Union[str, Path], batch_size: int = 100):
        self.folder_path = Path(folder_path)
        if not self.folder_path.exists():
            raise FileNotFoundError(f"Directory not found: {folder_path}")
        if not self.folder_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {folder_path}")
        if batch_size <= 0:
            raise ValueError("batch_size must be a positive integer.")

        self.batch_size = batch_size
        self._scandir_it = None

    def __iter__(self) -> "FileBatchIterator":
        self._scandir_it = os.scandir(self.folder_path)
        return self

    def __next__(self) -> List[Tuple[str, str]]:
        if self._scandir_it is None:
            self._scandir_it = os.scandir(self.folder_path)

        batch_data = []
        try:
            while len(batch_data) < self.batch_size:
                entry = next(self._scandir_it)
                if entry.is_file():
                    with open(entry.path, "r", encoding="utf-8", errors="replace") as f:
                        batch_data.append((entry.name, f.read()))
        except StopIteration:
            pass

        if not batch_data:
            if self._scandir_it:
                self._scandir_it.close()
                self._scandir_it = None
            raise StopIteration

        return batch_data


def read_files_in_batches(
    folder_path: Union[str, Path], batch_size: int = 100
) -> Iterator[List[Tuple[str, str]]]:
    """Generator function yielding batches of file contents lazily."""
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Directory not found: {folder_path}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {folder_path}")
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer.")

    with os.scandir(folder) as scandir_it:
        batch_data = []
        for entry in scandir_it:
            if entry.is_file():
                with open(entry.path, "r", encoding="utf-8", errors="replace") as f:
                    batch_data.append((entry.name, f.read()))
                if len(batch_data) == batch_size:
                    yield batch_data
                    batch_data = []
        if batch_data:
            yield batch_data


def load_all_files(folder_path: Union[str, Path]) -> List[Tuple[str, str]]:
    """Eager function that loads all file contents into memory at once."""
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Directory not found: {folder_path}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {folder_path}")

    all_data = []
    with os.scandir(folder) as scandir_it:
        for entry in scandir_it:
            if entry.is_file():
                with open(entry.path, "r", encoding="utf-8", errors="replace") as f:
                    all_data.append((entry.name, f.read()))
    return all_data
