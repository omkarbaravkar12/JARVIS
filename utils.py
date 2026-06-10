"""
utils.py — Shared helper utilities for Jarvis AI Assistant
"""

import datetime
import logging
import os


def get_greeting() -> str:
    """
    Return a time-aware greeting string.
    Morning: 5–11, Afternoon: 12–17, Evening: 18+
    """
    hour = datetime.datetime.now().hour
    if 5 <= hour < 12:
        return "Good morning"
    elif 12 <= hour < 18:
        return "Good afternoon"
    else:
        return "Good evening"


def get_time_str() -> str:
    """Return current time in human-readable format: '3:45 PM'."""
    return datetime.datetime.now().strftime("%I:%M %p")


def get_date_str() -> str:
    """Return current date in human-readable format: 'Wednesday, June 3, 2026'."""
    return datetime.datetime.now().strftime("%A, %B %d, %Y")


def get_today_key() -> str:
    """Return ISO date string (YYYY-MM-DD) for use as task dictionary key."""
    return datetime.date.today().isoformat()


def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Set up a named logger with consistent formatting.
    Each module should call: logger = setup_logger(__name__)
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def ensure_dir(path: str) -> None:
    """Create directory (and parents) if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp value between lo and hi."""
    return max(lo, min(hi, value))


def normalize_command(text: str) -> str:
    """
    Lowercase and strip punctuation from recognized text
    to make keyword matching reliable.
    """
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)  # Remove punctuation
    return text