"""
command_handler.py - Command execution engine for Jarvis
Action handlers return None  — announcement already spoken by main.py
Info handlers return a string — spoken as the response
"""

import os
import subprocess
import webbrowser
import random

import browser_controller
import config
import task_manager
from utils import get_time_str, get_date_str, normalize_command, setup_logger

logger = setup_logger(__name__)


def _speak(text):
    from voice_engine import speak
    speak(text)

def _listen(**kwargs):
    from voice_engine import listen
    return listen(**kwargs)


# ── Handlers ──────────────────────────────────────────────────────────────────

def _handle_youtube_app(text: str, tokens: list) -> str | None:
    """Opens the YouTube Windows app (if installed) and searches inside it."""
    import subprocess
    query = ""
    if "play" in text:
        query = text.split("play", 1)[-1].strip()

    # Try to open YouTube UWP app via URI scheme
    # youtube:// URI opens the YouTube app on Windows
    try:
        if query:
            uri = f"youtube://search?q={query.replace(' ', '+')}"
        else:
            uri = "youtube://"
        subprocess.Popen(["cmd", "/c", "start", uri], shell=False)
    except Exception:
        # Fallback: open YouTube app via Windows store protocol
        try:
            subprocess.Popen(
                ["explorer", f"youtube://search?q={query.replace(' ','+')}" if query else "youtube://"],
                shell=True
            )
        except Exception as exc:
            logger.error("YouTube app open failed: %s", exc)
            return "I could not open the YouTube app. Make sure it is installed from the Microsoft Store."
    return None


def _handle_youtube_play(text: str, tokens: list) -> str | None:
    """Opens YouTube WEBSITE and plays a video."""
    query = ""
    if "play" in text:
        query = text.split("play", 1)[-1].strip().replace("on youtube", "").strip()
    if query:
        browser_controller.youtube_search_and_play(query)
    else:
        browser_controller.open_website("https://www.youtube.com")
    return None


def _handle_smart_open(text: str, tokens: list) -> str | None:
    """Navigate browser to a named site."""
    destination = ""
    if "go to" in text:
        destination = text.split("go to", 1)[-1].strip()
    elif "navigate to" in text:
        destination = text.split("navigate to", 1)[-1].strip()
    elif "open" in text:
        destination = text.split("open", 1)[-1].strip()
        destination = destination.replace("chrome and", "").replace("chrome", "").strip()
    if destination:
        browser_controller.navigate_to_site(destination)
    return None


def _handle_search(text: str, tokens: list) -> str | None:
    """Search Google in the browser."""
    query = ""
    if "search for" in text:
        query = text.split("search for", 1)[-1].strip().replace("on google", "").strip()
    elif "google search" in text:
        query = text.split("google search", 1)[-1].strip()
    elif "search" in text:
        query = text.split("search", 1)[-1].strip()
    elif "look up" in text:
        query = text.split("look up", 1)[-1].strip()
    if query:
        browser_controller.google_search(query)
    return None


def _handle_open_app(text: str, tokens: list) -> str | None:
    """Launch a desktop application."""
    for app_name, app_path in config.APP_PATHS.items():
        if app_name in tokens or app_name in text:
            try:
                resolved = app_path.format(username=os.getlogin())
                subprocess.Popen([resolved], shell=True)
                return None
            except Exception as exc:
                logger.error("Failed to open %s: %s", app_name, exc)
                return f"I could not open {app_name}. Check the path in config.py."
    return None


def _handle_open_website(text: str, tokens: list) -> str | None:
    """Open a website in the default browser."""
    for site_name, url in config.WEBSITES.items():
        if site_name in tokens or site_name in text:
            webbrowser.open(url)
            return None
    return "I did not recognise which website to open. Try saying open YouTube."


def _handle_open_file(text: str, tokens: list) -> str | None:
    """Open a file shortcut."""
    for file_key, file_path in config.FILE_SHORTCUTS.items():
        if file_key in tokens or file_key in text:
            if os.path.exists(file_path):
                os.startfile(file_path)
                return None
            return f"I could not find your {file_key} at {file_path}."
    return None


def _handle_tasks_today(text: str, tokens: list) -> str | None:
    tasks = task_manager.get_today_tasks()
    return task_manager.format_tasks_for_speech(tasks)


def _handle_add_task(text: str, tokens: list) -> str | None:
    if "add task" in text:
        task_text = text.split("add task", 1)[-1].strip()
    elif "new task" in text:
        task_text = text.split("new task", 1)[-1].strip()
    else:
        task_text = ""

    if not task_text:
        _speak("What is the task?")
        task_text = _listen(prompt=False) or ""

    if task_text:
        task_manager.add_task(task_text)
        return f"Task added: {task_text}"
    return "No task added."


def _handle_time(text: str, tokens: list) -> str | None:
    return f"The current time is {get_time_str()}."


def _handle_date(text: str, tokens: list) -> str | None:
    return f"Today is {get_date_str()}."


def _handle_greeting(text: str, tokens: list) -> str | None:
    return f"Hello, {config.USER_NAME}! How can I help you?"


def _handle_joke(text: str, tokens: list) -> str | None:
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "A SQL query walks into a bar and asks two tables: Can I join you?",
        "I told my computer I needed a break. Now it won't stop sending me Kit Kat ads.",
        "Why did the developer go broke? Because he used up all his cache!",
        "There are only 10 types of people: those who understand binary, and those who do not.",
        "What is a computer's favourite snack? Microchips!",
    ]
    return random.choice(jokes)


def _handle_exit(text: str, tokens: list) -> str | None:
    return "__EXIT__"


# ── Command routing table ─────────────────────────────────────────────────────

COMMANDS = [
    # Exit / sleep
    {"keywords": ["exit","stop","sleep","goodbye","quit","bye"],
     "handler":  _handle_exit},

    # YouTube APP — "open youtube app" / "open youtube app and play X"
    {"keywords": ["youtube app"],
     "handler":  _handle_youtube_app},

    # YouTube WEBSITE play — "open youtube and play X" / "play X on youtube"
    {"keywords": ["youtube and play","open youtube and play","play","on youtube"],
     "handler":  _handle_youtube_play},

    # Smart navigation — "go to canva" / "navigate to github"
    {"keywords": ["go to","navigate to"],
     "handler":  _handle_smart_open},

    # Time & date
    {"keywords": ["what time","time"],   "handler": _handle_time},
    {"keywords": ["what day","date"],    "handler": _handle_date},

    # Greeting
    {"keywords": ["hello","hi","hey"],   "handler": _handle_greeting},

    # Tasks
    {"keywords": ["add task","new task","create task","remind me"],
     "handler":  _handle_add_task},
    {"keywords": ["task","tasks","my tasks","to do","schedule"],
     "handler":  _handle_tasks_today},

    # Search
    {"keywords": ["search","look up","find"],
     "handler":  _handle_search},

    # Open specific apps — before generic open
    {"keywords": ["open chrome","open firefox","open notepad","open calculator",
                  "open explorer","open vscode","open vs code","open vlc",
                  "open word","open excel"],
     "handler":  _handle_open_app},

    # Open websites / smart open
    {"keywords": ["open","launch"],
     "handler":  _handle_smart_open},

    # Open files
    {"keywords": ["open my","show my","open file"],
     "handler":  _handle_open_file},

    # Joke
    {"keywords": ["joke","tell me a joke","funny"],
     "handler":  _handle_joke},
]


# ── Dispatcher ────────────────────────────────────────────────────────────────

def process_command(raw_text: str) -> str | None:
    text   = normalize_command(raw_text)
    tokens = text.split()
    logger.info("Processing: '%s'", text)

    for command in COMMANDS:
        for kw in command["keywords"]:
            if kw in text:
                logger.debug("Matched '%s' -> %s", kw, command["handler"].__name__)
                result = command["handler"](text, tokens)
                if result is not None:
                    return result
                break   # handler returned None — action done, no response needed

    return (f"I am not sure how to help with that, {config.USER_NAME}. "
            "Try saying open YouTube, search Python tutorials, or what are my tasks.")