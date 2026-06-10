"""
main.py - Jarvis AI Assistant
- Wake word: "Jarvis wake up" / "Hey Jarvis"
- Every action spoken aloud before executing
- Full terminal log of every conversation
- Sleep / shutdown support
"""

import sys
import time
import argparse
from datetime import datetime

import config
from wake_word_detector import WakeWordDetector
from voice_engine import speak, listen
from command_handler import process_command
from utils import get_greeting, get_date_str, setup_logger

logger = setup_logger(__name__)

# ── Terminal log ──────────────────────────────────────────────────────────────

def log(message: str, tag: str = "INFO") -> None:
    now = datetime.now().strftime("%H:%M:%S")
    symbols = {
        "INFO":   "[ ]",
        "CMD":    "[>]",
        "SPEAK":  "[S]",
        "HEAR":   "[M]",
        "WAKE":   "[*]",
        "SLEEP":  "[Z]",
        "ERROR":  "[!]",
        "ACTION": "[A]",
    }
    line = f"{now} {symbols.get(tag,'[ ]')} {message}"
    print(line)

# ── Greeting ──────────────────────────────────────────────────────────────────

def greet() -> None:
    greeting = get_greeting()
    date_str = get_date_str()
    msg = (f"{greeting}, {config.USER_NAME}! I am {config.ASSISTANT_NAME}. "
           f"Today is {date_str}. How can I help you?")
    log(f"WAKE — {greeting} {config.USER_NAME}", "WAKE")
    speak(msg)

# ── Announcement — spoken BEFORE action executes ──────────────────────────────

def _get_announcement(text: str) -> str | None:
    t = text.lower().strip()

    # YouTube APP (says "app")
    if "youtube app" in t and "play" in t:
        query = t.split("play", 1)[-1].strip()
        return f"Opening YouTube app and playing {query} for you."
    if "youtube app" in t:
        return "Opening YouTube app for you."

    # YouTube WEBSITE play
    if "youtube" in t and "play" in t:
        query = t.split("play", 1)[-1].strip().replace("on youtube","").strip()
        return f"Opening YouTube and playing {query} for you."

    # Navigation
    if "go to" in t:
        return f"Navigating to {t.split('go to',1)[-1].strip()} for you."
    if "navigate to" in t:
        return f"Opening {t.split('navigate to',1)[-1].strip()} for you."

    # Websites
    for site in ["youtube","google","github","gmail","linkedin","netflix",
                 "reddit","canva","pinterest","whatsapp","spotify","chatgpt",
                 "instagram","twitter","stackoverflow","wikipedia","amazon","flipkart"]:
        if f"open {site}" in t:
            return f"Opening {site.capitalize()} for you."

    # Apps
    app_msgs = {
        "chrome":     "Launching Chrome for you.",
        "firefox":    "Launching Firefox for you.",
        "notepad":    "Opening Notepad for you.",
        "calculator": "Opening Calculator for you.",
        "vscode":     "Launching VS Code for you.",
        "vs code":    "Launching VS Code for you.",
        "vlc":        "Opening VLC for you.",
        "word":       "Opening Microsoft Word for you.",
        "excel":      "Opening Microsoft Excel for you.",
        "explorer":   "Opening File Explorer for you.",
    }
    for app, msg in app_msgs.items():
        if f"open {app}" in t:
            return msg

    # Search
    if "search for" in t:
        return f"Searching for {t.split('search for',1)[-1].strip()}."
    if "search" in t:
        q = t.split("search",1)[-1].strip()
        if q: return f"Searching for {q}."
    if "look up" in t:
        q = t.split("look up",1)[-1].strip()
        if q: return f"Searching for {q}."

    # Tasks
    if "add task" in t or "new task" in t:
        return "Adding that task for you."
    if "my tasks" in t or "tasks today" in t:
        return "Let me check your tasks."

    # Files
    if "open my" in t or "open file" in t:
        return "Opening that file for you."

    # Play without youtube
    if "play" in t:
        q = t.split("play",1)[-1].strip()
        if q: return f"Playing {q} for you."

    # Joke
    if "joke" in t:
        return "Sure, here is one for you."

    # Catch-all open
    if "open" in t:
        target = t.split("open",1)[-1].strip()
        if target: return f"Opening {target} for you."

    return None

# ── Voice command loop ────────────────────────────────────────────────────────

def run_voice_loop() -> None:
    log("Jarvis active — voice loop started", "INFO")
    speak("I am listening. Say a command, or say sleep to go back to standby.")

    while True:
        log("─── Waiting for your command ───", "HEAR")
        raw_text = listen()

        if raw_text is None:
            log("Nothing heard — listening again", "INFO")
            continue

        log(f'You said: "{raw_text}"', "HEAR")

        t = raw_text.lower().strip()

        # Sleep
        if any(w in t for w in ["sleep","standby","go to sleep","bye","goodbye","see you"]):
            log("Going to standby", "SLEEP")
            speak("Sleeping now. Say Jarvis wake up anytime to wake me again.")
            return

        # Shutdown
        if any(w in t for w in ["shutdown jarvis","shut down jarvis",
                                  "turn off jarvis","exit jarvis","quit jarvis"]):
            log("Shutting down completely", "SLEEP")
            speak(f"Shutting down completely. Goodbye {config.USER_NAME}!")
            time.sleep(1.5)
            sys.exit(0)

        # Announce FIRST — spoken before action
        announcement = _get_announcement(raw_text)
        if announcement:
            log(f'Jarvis: "{announcement}"', "ACTION")
            speak(announcement)
        else:
            log("No announcement for this command", "INFO")

        # Execute
        log(f"Executing: {raw_text}", "CMD")
        response = process_command(raw_text)

        if response == "__EXIT__":
            log("EXIT — going to standby", "SLEEP")
            speak("Sleeping now. Say Jarvis wake up anytime to wake me again.")
            return

        # Speak response only if it adds NEW info (not already announced)
        if response and response not in (None, "None", ""):
            log(f'Jarvis: "{response[:80]}"', "SPEAK")
            speak(response)

        log("Done. Ready for next command.", "INFO")
        print("")

# ── Background wake word loop ─────────────────────────────────────────────────

def background_loop() -> None:
    log("Jarvis is running in background", "INFO")
    log("Say 'Jarvis wake up' or 'Hey Jarvis' to activate", "INFO")
    print("")
    detector = WakeWordDetector()

    while True:
        log("Listening for wake word...", "INFO")
        detector.wait_for_wake_word()
        log("WAKE WORD HEARD — activating Jarvis!", "WAKE")
        print("")
        greet()
        run_voice_loop()
        log("Back to standby. Say 'Jarvis wake up' to activate.", "SLEEP")
        print("")

# ── Text mode ─────────────────────────────────────────────────────────────────

def run_text_loop() -> None:
    print(f"\n{'='*52}")
    print(f"  JARVIS -- TEXT MODE (no mic needed)")
    print(f"  Type commands. Type 'exit' to quit.")
    print(f"{'='*52}\n")
    speak(f"Text mode activated. {get_greeting()}, {config.USER_NAME}!")

    while True:
        try:
            raw_text = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not raw_text:
            continue

        log(f'Input: "{raw_text}"', "CMD")
        t = raw_text.lower()

        if any(w in t for w in ["sleep","bye","goodbye"]):
            speak(f"Goodbye {config.USER_NAME}!")
            break
        if any(w in t for w in ["quit","exit","shutdown"]):
            speak(f"Shutting down. Goodbye {config.USER_NAME}!")
            break

        announcement = _get_announcement(raw_text)
        if announcement:
            log(f'Jarvis: "{announcement}"', "ACTION")
            speak(announcement)

        response = process_command(raw_text)
        if response == "__EXIT__":
            speak(f"Goodbye {config.USER_NAME}!")
            break
        if response:
            log(f'Jarvis: "{response[:80]}"', "SPEAK")
            speak(response)
        print("")

# ── Boot banner ───────────────────────────────────────────────────────────────

def boot_banner() -> None:
    print("""
╔════════════════════════════════════════════════════╗
║      JARVIS  —  AI Desktop Assistant  v1.0        ║
║                                                    ║
║   [*]  Say "Jarvis wake up" to activate           ║
║   [Z]  Say "sleep" to return to standby           ║
║   [!]  Say "shutdown jarvis" to fully quit        ║
║                                                    ║
║   All conversations shown here in real time       ║
╚════════════════════════════════════════════════════╝
""")
    log(f"Jarvis starting — User: {config.USER_NAME}", "INFO")
    log(f"Phrase limit: {config.PHRASE_LIMIT}s per command", "INFO")
    log("Initialising audio engine...", "INFO")

# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", action="store_true")
    parser.add_argument("--skip", action="store_true")
    args = parser.parse_args()

    boot_banner()

    if args.text:
        run_text_loop()
    elif args.skip:
        greet()
        run_voice_loop()
        background_loop()
    else:
        background_loop()

if __name__ == "__main__":
    main()
