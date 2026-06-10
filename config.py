"""
config.py - Central configuration for Jarvis AI Assistant
All paths, thresholds, and settings live here. No hardcoding elsewhere.
"""

import os

# ── Voice settings ────────────────────────────────────────────────────────────
VOICE_RATE   = 175
VOICE_VOLUME = 1.0
VOICE_INDEX  = 0       # 0 = male, 1 = female (if available)

# ── Clap detection (kept for reference) ──────────────────────────────────────
CLAP_THRESHOLD    = 800
CLAP_WINDOW_SEC   = 1.8
CLAP_COOLDOWN_SEC = 0.15
SAMPLE_RATE       = 44100
CHUNK_SIZE        = 1024

# ── Speech recognition ────────────────────────────────────────────────────────
LISTEN_TIMEOUT   = 8
PHRASE_LIMIT     = 5       # seconds to record per command
ENERGY_THRESHOLD = 300

# ── Task storage ──────────────────────────────────────────────────────────────
TASKS_FILE = os.path.join(os.path.dirname(__file__), "data", "tasks.json")

# ── Application paths ─────────────────────────────────────────────────────────
APP_PATHS = {
    "chrome":      r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "firefox":     r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "notepad":     r"notepad.exe",
    "calculator":  r"calc.exe",
    "explorer":    r"explorer.exe",
    "vlc":         r"C:\Program Files\VideoLAN\VLC\vlc.exe",
    "vscode":      r"C:\Users\Omkar\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "word":        r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":       r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
}

# ── YouTube app URI (Windows Store app) ───────────────────────────────────────
# If YouTube app is installed from Microsoft Store, this URI opens it
YOUTUBE_APP_URI = "youtube://"

# ── Website shortcuts ─────────────────────────────────────────────────────────
WEBSITES = {
    "youtube":       "https://www.youtube.com",
    "google":        "https://www.google.com",
    "github":        "https://www.github.com",
    "gmail":         "https://mail.google.com",
    "linkedin":      "https://www.linkedin.com",
    "stackoverflow": "https://stackoverflow.com",
    "reddit":        "https://www.reddit.com",
    "wikipedia":     "https://www.wikipedia.org",
    "netflix":       "https://www.netflix.com",
    "twitter":       "https://www.twitter.com",
    "chatgpt":       "https://chat.openai.com",
    "canva":         "https://www.canva.com",
    "pinterest":     "https://www.pinterest.com",
    "instagram":     "https://www.instagram.com",
    "whatsapp":      "https://web.whatsapp.com",
    "spotify":       "https://open.spotify.com",
    "amazon":        "https://www.amazon.in",
    "flipkart":      "https://www.flipkart.com",
}

# ── File shortcuts ────────────────────────────────────────────────────────────
FILE_SHORTCUTS = {
    "resume": os.path.expanduser(r"~/Documents/resume.pdf"),
    "notes":  os.path.expanduser(r"~/Documents/notes.txt"),
}

# ── Assistant persona ─────────────────────────────────────────────────────────
ASSISTANT_NAME = "Jarvis"
USER_NAME      = "Omkar"