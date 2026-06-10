"""
wake_word_detector.py - Wake word detection for Jarvis
Listens continuously for "jarvis wake up" or similar phrases.
No new packages needed - uses speech_recognition + sounddevice.
"""

import io
import wave
import threading
import numpy as np
import sounddevice as sd
import speech_recognition as sr

from utils import setup_logger

logger = setup_logger(__name__)

# All phrases that will wake Jarvis up
WAKE_PHRASES = [
    "jarvis wake up",
    "jarvis wakeup",
    "hey jarvis",
    "ok jarvis",
    "jarvis",
    "wake up jarvis",
    "jarvis are you there",
    "jarvis come back",
]


class WakeWordDetector:
    """
    Continuously records short audio chunks and checks each one
    for the wake word using Google STT.

    Usage (blocking):
        detector = WakeWordDetector()
        detector.wait_for_wake_word()   # blocks until wake word heard

    Usage (non-blocking with callback):
        def on_wake():
            print("Wake word detected!")
        detector = WakeWordDetector(callback=on_wake)
        detector.start()
        # ... later:
        detector.stop()
    """

    def __init__(self, callback=None):
        self._callback  = callback
        self._running   = False
        self._thread    = None
        self._recognizer = sr.Recognizer()

    # ── Public API ────────────────────────────────────────────────────────────

    def wait_for_wake_word(self) -> None:
        """Block until the wake word is detected."""
        print("\n🎙️  [JARVIS] Listening for 'Jarvis wake up'...\n")
        logger.info("Wake word detector active.")

        while True:
            audio_np = self._record_chunk(duration=3)

            # Skip silence
            if int(np.max(np.abs(audio_np))) < 100:
                continue

            text = self._transcribe(audio_np)
            if text is None:
                continue

            logger.debug("Heard: '%s'", text)

            if self._is_wake_word(text):
                logger.info("Wake word detected: '%s'", text)
                print(f"\n[JARVIS] Wake word detected: '{text}'\n")
                return

    def start(self) -> None:
        """Start wake word detection in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Wake word detector started in background.")

    def stop(self) -> None:
        """Stop the background detection thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("Wake word detector stopped.")

    # ── Private methods ───────────────────────────────────────────────────────

    def _run(self) -> None:
        """Background thread — calls callback when wake word detected."""
        while self._running:
            audio_np = self._record_chunk(duration=3)

            if int(np.max(np.abs(audio_np))) < 100:
                continue

            text = self._transcribe(audio_np)
            if text is None:
                continue

            if self._is_wake_word(text):
                logger.info("Wake word detected: '%s'", text)
                if self._callback:
                    self._callback()

    def _record_chunk(self, duration: int = 3,
                      sample_rate: int = 16000) -> np.ndarray:
        """Record a short audio chunk silently."""
        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        )
        sd.wait()
        return audio

    def _to_wav_bytes(self, audio: np.ndarray,
                      sample_rate: int = 16000) -> bytes:
        """Convert numpy array to WAV bytes."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())
        buf.seek(0)
        return buf.read()

    def _transcribe(self, audio_np: np.ndarray) -> str | None:
        """Transcribe audio to text. Returns None on failure."""
        wav_bytes = self._to_wav_bytes(audio_np)
        with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
            audio_data = self._recognizer.record(source)
        try:
            text = self._recognizer.recognize_google(audio_data)
            return text.lower().strip()
        except sr.UnknownValueError:
            return None
        except sr.RequestError as exc:
            logger.error("STT error in wake detector: %s", exc)
            return None

    def _is_wake_word(self, text: str) -> bool:
        """Check if transcribed text contains any wake phrase."""
        text = text.lower().strip()
        return any(phrase in text for phrase in WAKE_PHRASES)


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Say 'Jarvis wake up' to test...")
    d = WakeWordDetector()
    d.wait_for_wake_word()
    print("Wake word detected!")