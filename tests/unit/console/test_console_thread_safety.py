"""Tests for BasicConsole thread safety.

This module tests that BasicConsole properly handles concurrent writes
from multiple threads without data corruption.
"""

import threading
from io import StringIO

from aclaf.console._basic import BasicConsole


class TestConsoleThreadSafety:
    """Test BasicConsole thread safety."""

    def test_concurrent_writes_are_serialized(self):
        """Concurrent writes from multiple threads don't corrupt output."""
        buffer = StringIO()
        console = BasicConsole(file=buffer)

        # Number of threads and writes per thread
        num_threads = 10
        writes_per_thread = 20

        def worker(thread_id: int):
            for i in range(writes_per_thread):
                console.print(f"Thread-{thread_id}-Write-{i}")

        threads = []
        for tid in range(num_threads):
            thread = threading.Thread(target=worker, args=(tid,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        output = buffer.getvalue()
        lines = output.strip().split("\n")

        # Verify we got the expected number of lines
        expected_lines = num_threads * writes_per_thread
        assert len(lines) == expected_lines

        # Verify each line is well-formed (not corrupted)
        for line in lines:
            assert line.startswith("Thread-")
            assert "-Write-" in line

    def test_lock_prevents_interleaving(self):
        """Lock prevents interleaving of multi-part writes."""
        buffer = StringIO()
        console = BasicConsole(file=buffer)

        num_threads = 5
        writes_per_thread = 10

        def worker(_thread_id: int):
            for _ in range(writes_per_thread):
                # Each print writes "A B C\n" as a single atomic operation
                console.print("A", "B", "C")

        threads = []
        for tid in range(num_threads):
            thread = threading.Thread(target=worker, args=(tid,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        output = buffer.getvalue()
        lines = output.strip().split("\n")

        # Every line should be exactly "A B C" with no interleaving
        for line in lines:
            assert line == "A B C", f"Line was corrupted: {line!r}"

    def test_flush_is_thread_safe(self):
        """Flush operations are thread-safe."""
        buffer = StringIO()
        console = BasicConsole(file=buffer)

        num_threads = 5

        def worker():
            for i in range(10):
                console.print(f"Message {i}", flush=True)

        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        output = buffer.getvalue()
        lines = output.strip().split("\n")

        # Verify all messages were written
        assert len(lines) == num_threads * 10

    def test_single_threaded_performance(self):
        """Single-threaded operation still works correctly with lock."""
        buffer = StringIO()
        console = BasicConsole(file=buffer)

        # Single-threaded writes should work normally
        for i in range(100):
            console.print(f"Line {i}")

        output = buffer.getvalue()
        lines = output.strip().split("\n")

        assert len(lines) == 100
        for i, line in enumerate(lines):
            assert line == f"Line {i}"
