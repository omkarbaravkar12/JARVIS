"""
clap_detector.py — Microphone-based double-clap wake-trigger for Jarvis

HOW IT WORKS
------------
1. Continuously reads audio chunks from the default microphone.
2. Computes the peak amplitude of each chunk.
3. If amplitude exceeds CLAP_THRESHOLD, it records the timestamp as a "clap".
4. If two claps arrive within CLAP_WINDOW_SEC of each other (and are separated
   by at least CLAP_COOLDOWN_SEC to avoid counting one clap twice), the
   detector fires and returns True.

DEPENDENCIES
------------
    pip install sounddevice numpy
"""

import time
import threading
import numpy as np

from utils import setup_logger
import config

logger = setup_logger(__name__)


class ClapDetector:
    """
    Detects a double-clap pattern from the default microphone.

    Usage (blocking):
        detector = ClapDetector()
        detector.wait_for_double_clap()   # blocks until two claps detected

    Usage (non-blocking with callback):
        def on_clap():
            print("Clap detected!")
        detector = ClapDetector(callback=on_clap)
        detector.start()   # runs in background thread
        # ... later:
        detector.stop()
    """

    def __init__(self, callback=None):
        self._callback = callback
        self._running = False
        self._thread = None

        # Timestamps of recent claps
        self._clap_times: list[float] = []

        # Minimal cooldown: ignore amplitude spikes for this many seconds
        # after detecting a clap (prevents one hand-clap from registering twice)
        self._last_clap_time: float = 0.0

    # ──────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────────────────────

    def wait_for_double_clap(self) -> None:
        """
        Block the calling thread until a valid double-clap is detected.
        Prints a ready message and then streams audio until triggered.
        """
        logger.info("Clap detector active — waiting for double clap…")
        print("\n🎙️  [JARVIS] Listening for double clap to wake up…\n")

        try:
            import sounddevice as sd
        except ImportError:
            logger.error(
                "sounddevice not installed. Run: pip install sounddevice numpy"
            )
            raise

        detected = threading.Event()

        def _audio_callback(indata, frames, time_info, status):
            if status:
                logger.debug("Audio status: %s", status)
            self._process_chunk(indata[:, 0], detected)

        with sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=1,
            blocksize=config.CHUNK_SIZE,
            dtype="int16",
            callback=_audio_callback,
        ):
            detected.wait()  # Block until double-clap event is set

        logger.info("Double clap detected — waking up!")

    def start(self) -> None:
        """Start clap detection in a background daemon thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Clap detector started in background thread.")

    def stop(self) -> None:
        """Stop the background detection thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Clap detector stopped.")

    # ──────────────────────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ──────────────────────────────────────────────────────────────────────────

    def _run(self) -> None:
        """Background thread target — streams audio and calls callback."""
        try:
            import sounddevice as sd
        except ImportError:
            logger.error("sounddevice not installed.")
            return

        triggered = threading.Event()

        def _audio_callback(indata, frames, time_info, status):
            if not self._running:
                raise sd.CallbackStop()
            self._process_chunk(indata[:, 0], triggered)

        with sd.InputStream(
            samplerate=config.SAMPLE_RATE,
            channels=1,
            blocksize=config.CHUNK_SIZE,
            dtype="int16",
            callback=_audio_callback,
        ):
            while self._running:
                if triggered.wait(timeout=0.1):
                    if self._callback:
                        self._callback()
                    triggered.clear()
                    # Purge clap history after trigger to avoid re-firing
                    self._clap_times.clear()

    def _process_chunk(self, chunk: np.ndarray, event: threading.Event) -> None:
        """
        Analyse one audio chunk. If a clap is detected and this is the
        second clap within the time window, set the threading.Event.
        """
        peak = int(np.max(np.abs(chunk)))
        now = time.monotonic()

        if peak < config.CLAP_THRESHOLD:
            return  # Just background noise

        # Guard against double-counting a single clap
        if (now - self._last_clap_time) < config.CLAP_COOLDOWN_SEC:
            return

        # Valid clap — record it
        self._last_clap_time = now
        self._clap_times.append(now)
        logger.debug("Clap detected! Peak=%d  Total claps=%d", peak, len(self._clap_times))

        # Prune stale clap timestamps outside the window
        self._clap_times = [
            t for t in self._clap_times
            if (now - t) <= config.CLAP_WINDOW_SEC
        ]

        if len(self._clap_times) >= 2:
            logger.info("✅ Double clap confirmed!")
            self._clap_times.clear()
            event.set()


# ──────────────────────────────────────────────────────────────────────────────
# Quick standalone test
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing clap detector. Clap twice quickly…")
    d = ClapDetector()
    d.wait_for_double_clap()
    print("Double clap detected! ✅")