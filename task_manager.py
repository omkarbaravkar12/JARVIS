"""
task_manager.py — Daily task storage and retrieval for Jarvis

STORAGE FORMAT
--------------
tasks.json structure:
{
    "2026-06-03": ["study DSA at 5 PM", "go to gym at 6 PM"],
    "2026-06-04": ["team meeting at 10 AM"]
}

Tasks are keyed by ISO date (YYYY-MM-DD).

DEPENDENCIES
------------
Standard library only (json, os, datetime).
"""

import json
import os

import config
from utils import get_today_key, setup_logger, ensure_dir

logger = setup_logger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _load_all_tasks() -> dict:
    """Load the entire tasks JSON file and return as a dict."""
    if not os.path.exists(config.TASKS_FILE):
        return {}
    try:
        with open(config.TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load tasks file: %s", exc)
        return {}


def _save_all_tasks(data: dict) -> bool:
    """Persist the full tasks dict back to disk. Returns True on success."""
    try:
        ensure_dir(os.path.dirname(config.TASKS_FILE))
        with open(config.TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError as exc:
        logger.error("Failed to save tasks: %s", exc)
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def get_today_tasks() -> list[str]:
    """
    Return a list of tasks for today (empty list if none).
    """
    all_tasks = _load_all_tasks()
    return all_tasks.get(get_today_key(), [])


def add_task(task_text: str) -> bool:
    """
    Append a new task to today's task list.

    Args:
        task_text: The task description (e.g. "study DSA at 5 PM").

    Returns:
        True if saved successfully, False otherwise.
    """
    task_text = task_text.strip()
    if not task_text:
        return False

    all_tasks = _load_all_tasks()
    today = get_today_key()

    if today not in all_tasks:
        all_tasks[today] = []

    all_tasks[today].append(task_text)
    logger.info("Task added for %s: '%s'", today, task_text)
    return _save_all_tasks(all_tasks)


def remove_task(index: int) -> str | None:
    """
    Remove a task by its 1-based index from today's list.

    Returns:
        The removed task string, or None if index was invalid.
    """
    all_tasks = _load_all_tasks()
    today = get_today_key()
    tasks = all_tasks.get(today, [])

    if not (1 <= index <= len(tasks)):
        logger.warning("Invalid task index: %d (have %d tasks)", index, len(tasks))
        return None

    removed = tasks.pop(index - 1)
    all_tasks[today] = tasks
    _save_all_tasks(all_tasks)
    logger.info("Task removed: '%s'", removed)
    return removed


def clear_today_tasks() -> None:
    """Remove all tasks for today."""
    all_tasks = _load_all_tasks()
    all_tasks[get_today_key()] = []
    _save_all_tasks(all_tasks)
    logger.info("All today's tasks cleared.")


def format_tasks_for_speech(tasks: list[str]) -> str:
    """
    Convert a list of tasks into a natural spoken string.

    Example output:
        "You have 2 tasks today. Task 1: study DSA at 5 PM. Task 2: go to gym."
    """
    if not tasks:
        return "You have no tasks scheduled for today."

    count = len(tasks)
    intro = f"You have {count} task{'s' if count > 1 else ''} today."
    items = " ".join(
        f"Task {i + 1}: {task}." for i, task in enumerate(tasks)
    )
    return f"{intro} {items}"


# ──────────────────────────────────────────────────────────────────────────────
# Standalone test
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Adding test tasks…")
    add_task("Study DSA at 5 PM")
    add_task("Go to gym at 6 PM")
    add_task("Read Python docs at 9 PM")

    tasks = get_today_tasks()
    print("Today's tasks:", tasks)
    print("Speech format:", format_tasks_for_speech(tasks))

    removed = remove_task(2)
    print(f"Removed: '{removed}'")
    print("After removal:", get_today_tasks())