"""
tests/test_jarvis.py — Unit tests for Jarvis AI Assistant

Run from project root:
    python -m pytest tests/ -v

Or without pytest:
    python tests/test_jarvis.py
"""

import sys
import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# ── Make parent directory importable ─────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ─────────────────────────────────────────────────────────────────────────────
# utils tests
# ─────────────────────────────────────────────────────────────────────────────
class TestUtils(unittest.TestCase):

    def test_normalize_command_lowercase(self):
        from utils import normalize_command
        self.assertEqual(normalize_command("OPEN YOUTUBE"), "open youtube")

    def test_normalize_command_strips_punctuation(self):
        from utils import normalize_command
        self.assertEqual(normalize_command("hello!"), "hello")

    def test_normalize_command_strips_whitespace(self):
        from utils import normalize_command
        self.assertEqual(normalize_command("  exit  "), "exit")

    def test_get_today_key_format(self):
        from utils import get_today_key
        key = get_today_key()
        # Must be YYYY-MM-DD
        self.assertRegex(key, r"^\d{4}-\d{2}-\d{2}$")

    def test_greeting_returns_string(self):
        from utils import get_greeting
        greeting = get_greeting()
        self.assertIn(greeting, ["Good morning", "Good afternoon", "Good evening"])

    def test_get_time_str_format(self):
        from utils import get_time_str
        ts = get_time_str()
        # e.g. "03:45 PM"
        self.assertRegex(ts, r"^\d{2}:\d{2} (AM|PM)$")

    def test_clamp(self):
        from utils import clamp
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-1, 0, 10), 0)
        self.assertEqual(clamp(15, 0, 10), 10)


# ─────────────────────────────────────────────────────────────────────────────
# task_manager tests
# ─────────────────────────────────────────────────────────────────────────────
class TestTaskManager(unittest.TestCase):

    def setUp(self):
        """Use a temporary tasks file to isolate tests."""
        self.tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.tmp.close()
        # Override config path
        import config
        self._original_path = config.TASKS_FILE
        config.TASKS_FILE = self.tmp.name
        # Write empty JSON
        with open(self.tmp.name, "w") as f:
            json.dump({}, f)

    def tearDown(self):
        import config
        config.TASKS_FILE = self._original_path
        os.unlink(self.tmp.name)

    def test_add_and_get_task(self):
        import task_manager
        task_manager.add_task("Study Python at 5 PM")
        tasks = task_manager.get_today_tasks()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0], "Study Python at 5 PM")

    def test_add_multiple_tasks(self):
        import task_manager
        task_manager.add_task("Task A")
        task_manager.add_task("Task B")
        task_manager.add_task("Task C")
        self.assertEqual(len(task_manager.get_today_tasks()), 3)

    def test_remove_task_valid(self):
        import task_manager
        task_manager.add_task("Task 1")
        task_manager.add_task("Task 2")
        removed = task_manager.remove_task(1)
        self.assertEqual(removed, "Task 1")
        self.assertEqual(len(task_manager.get_today_tasks()), 1)

    def test_remove_task_invalid_index(self):
        import task_manager
        task_manager.add_task("Task 1")
        removed = task_manager.remove_task(99)
        self.assertIsNone(removed)

    def test_clear_today_tasks(self):
        import task_manager
        task_manager.add_task("Task X")
        task_manager.clear_today_tasks()
        self.assertEqual(task_manager.get_today_tasks(), [])

    def test_format_no_tasks(self):
        import task_manager
        msg = task_manager.format_tasks_for_speech([])
        self.assertIn("no tasks", msg.lower())

    def test_format_one_task(self):
        import task_manager
        msg = task_manager.format_tasks_for_speech(["Study at 5 PM"])
        self.assertIn("1 task", msg)
        self.assertIn("Study at 5 PM", msg)

    def test_format_multiple_tasks(self):
        import task_manager
        msg = task_manager.format_tasks_for_speech(["A", "B", "C"])
        self.assertIn("3 tasks", msg)

    def test_add_empty_task_returns_false(self):
        import task_manager
        result = task_manager.add_task("   ")
        self.assertFalse(result)


# ─────────────────────────────────────────────────────────────────────────────
# command_handler tests (no actual system actions executed)
# ─────────────────────────────────────────────────────────────────────────────
class TestCommandHandler(unittest.TestCase):

    def _process(self, text):
        from command_handler import process_command
        return process_command(text)

    @patch("webbrowser.open")
    def test_open_youtube(self, mock_wb):
        response = self._process("open youtube")
        mock_wb.assert_called_once()
        called_url = mock_wb.call_args[0][0]
        self.assertIn("youtube.com", called_url)
        self.assertIn("Opening", response)

    @patch("webbrowser.open")
    def test_search_command(self, mock_wb):
        response = self._process("search python tutorials")
        mock_wb.assert_called_once()
        called_url = mock_wb.call_args[0][0]
        self.assertIn("google.com/search", called_url)
        self.assertIn("python", called_url)

    def test_exit_command(self):
        response = self._process("exit")
        self.assertEqual(response, "__EXIT__")

    def test_stop_command(self):
        response = self._process("stop")
        self.assertEqual(response, "__EXIT__")

    def test_time_command(self):
        response = self._process("what time is it")
        self.assertIn("time", response.lower())

    def test_date_command(self):
        response = self._process("what is today's date")
        self.assertIsNotNone(response)

    def test_greeting(self):
        response = self._process("hello")
        self.assertIsNotNone(response)
        self.assertIn("Hello", response)

    def test_joke_command(self):
        response = self._process("tell me a joke")
        self.assertIsNotNone(response)
        self.assertGreater(len(response), 10)

    def test_unknown_command_returns_fallback(self):
        response = self._process("xyzzy frobnicate")
        self.assertIsNotNone(response)
        self.assertIn("not sure", response.lower())

    def test_tasks_today(self):
        with patch("task_manager.get_today_tasks", return_value=[]):
            response = self._process("what are my tasks today")
            self.assertIn("no tasks", response.lower())


# ─────────────────────────────────────────────────────────────────────────────
# clap_detector tests (no actual audio hardware needed)
# ─────────────────────────────────────────────────────────────────────────────
class TestClapDetector(unittest.TestCase):

    def test_single_clap_does_not_trigger(self):
        """One clap should not set the event."""
        import threading
        import numpy as np
        from clap_detector import ClapDetector

        detector = ClapDetector()
        event = threading.Event()

        # Simulate one clap chunk
        loud_chunk = np.array([2000] * 1024, dtype=np.int16)
        detector._process_chunk(loud_chunk, event)
        self.assertFalse(event.is_set(), "Single clap must not trigger.")

    def test_double_clap_triggers(self):
        """Two claps within the window should set the event."""
        import threading
        import time
        import numpy as np
        from clap_detector import ClapDetector
        import config

        detector = ClapDetector()
        event = threading.Event()

        loud_chunk = np.array([2000] * 1024, dtype=np.int16)

        # First clap
        detector._process_chunk(loud_chunk, event)
        # Wait longer than cooldown but within window
        time.sleep(config.CLAP_COOLDOWN_SEC + 0.05)
        # Second clap
        detector._process_chunk(loud_chunk, event)

        self.assertTrue(event.is_set(), "Double clap must trigger the event.")

    def test_claps_outside_window_do_not_trigger(self):
        """Two claps separated by more than CLAP_WINDOW_SEC must not trigger."""
        import threading
        import time
        import numpy as np
        from clap_detector import ClapDetector
        import config

        detector = ClapDetector()
        event = threading.Event()

        loud_chunk = np.array([2000] * 1024, dtype=np.int16)

        detector._process_chunk(loud_chunk, event)
        time.sleep(config.CLAP_WINDOW_SEC + 0.3)
        detector._process_chunk(loud_chunk, event)

        self.assertFalse(event.is_set(), "Claps outside window must not trigger.")

    def test_quiet_audio_ignored(self):
        """Audio below threshold must not register as a clap."""
        import threading
        import numpy as np
        from clap_detector import ClapDetector
        import config

        detector = ClapDetector()
        event = threading.Event()

        quiet_chunk = np.array([50] * 1024, dtype=np.int16)
        detector._process_chunk(quiet_chunk, event)
        detector._process_chunk(quiet_chunk, event)
        self.assertFalse(event.is_set())


# ─────────────────────────────────────────────────────────────────────────────
# Run tests
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)