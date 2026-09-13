import os
import sys
import tempfile
import tracemalloc
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.file_iterator import (
    FileBatchIterator,
    load_all_files,
    read_files_in_batches,
)


def create_dummy_dataset(target_dir: Path, file_count: int, file_size_kb: int = 1):
    """Generate dummy text files in target_dir."""
    content = "A" * (file_size_kb * 1024)
    for i in range(file_count):
        file_path = target_dir / f"sample_{i:05d}.txt"
        file_path.write_text(content, encoding="utf-8")


def measure_eager_memory(folder_path: Path) -> float:
    """Measure peak memory usage in KB for loading all files at once."""
    tracemalloc.start()
    tracemalloc.reset_peak()

    data = load_all_files(folder_path)
    # Perform dummy access to ensure data is in RAM
    _ = len(data)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    del data
    return peak / 1024.0


def measure_lazy_iterator_memory(folder_path: Path, batch_size: int = 100) -> float:
    """Measure peak memory usage in KB using FileBatchIterator."""
    tracemalloc.start()
    tracemalloc.reset_peak()

    iterator = FileBatchIterator(folder_path, batch_size=batch_size)
    for batch in iterator:
        _ = len(batch)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024.0


def measure_generator_memory(folder_path: Path, batch_size: int = 100) -> float:
    """Measure peak memory usage in KB using read_files_in_batches generator."""
    tracemalloc.start()
    tracemalloc.reset_peak()

    gen = read_files_in_batches(folder_path, batch_size=batch_size)
    for batch in gen:
        _ = len(batch)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak / 1024.0


def run_benchmark():
    dataset_sizes = [100, 1000, 10000]
    batch_size = 100
    file_size_kb = 1

    print("=" * 80)
    print(" D2 MEMORY BENCHMARK: EAGER vs LAZY ITERATOR vs GENERATOR")
    print(f" Fixed Batch Size: {batch_size} files | File Size: ~{file_size_kb} KB each")
    print("=" * 80)
    print(f"{'Dataset Size':<15} | {'Eager Peak (KB)':<18} | {'Lazy Iterator (KB)':<20} | {'Generator (KB)':<16}")
    print("-" * 80)

    results = []

    for size in dataset_sizes:
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            create_dummy_dataset(dir_path, size, file_size_kb=file_size_kb)

            eager_peak = measure_eager_memory(dir_path)
            lazy_peak = measure_lazy_iterator_memory(dir_path, batch_size=batch_size)
            gen_peak = measure_generator_memory(dir_path, batch_size=batch_size)

            results.append((size, eager_peak, lazy_peak, gen_peak))

            print(
                f"{size:<15} | {eager_peak:<18.2f} | {lazy_peak:<20.2f} | {gen_peak:<16.2f}"
            )

    print("=" * 80)
    print("Summary Observation:")
    print("- Eager loading memory scales linearly O(N) with the dataset size.")
    print("- Lazy Iterator & Generator memory remains approximately stable O(B) bounded by batch size.")
    print("=" * 80)

    return results


if __name__ == "__main__":
    run_benchmark()
