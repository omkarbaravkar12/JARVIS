import io
import wave
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import pyttsx3

import config
from utils import setup_logger

logger = setup_logger(__name__)
_tts_engine = None


def _get_tts_engine():
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = pyttsx3.init()
        voices = _tts_engine.getProperty("voices")
        if voices and config.VOICE_INDEX < len(voices):
            _tts_engine.setProperty("voice", voices[config.VOICE_INDEX].id)
        _tts_engine.setProperty("rate", config.VOICE_RATE)
        _tts_engine.setProperty("volume", config.VOICE_VOLUME)
    return _tts_engine


def speak(text: str) -> None:
    if not text:
        return
    print(f"🤖 [JARVIS]: {text}")
    engine = _get_tts_engine()
    engine.say(text)
    engine.runAndWait()


def _record_with_sounddevice(duration=5, sample_rate=16000):
    print(f"👂 [JARVIS] Recording for {duration}s — speak now…")
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )
    sd.wait()
    return audio


def _to_wav_bytes(audio, sample_rate=16000):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    buf.seek(0)
    return buf.read()


def listen(prompt: bool = True) -> str | None:
    sample_rate = 16000
    duration = config.PHRASE_LIMIT

    try:
        audio_np = _record_with_sounddevice(duration, sample_rate)
    except Exception as exc:
        logger.error("Microphone error: %s", exc)
        speak("I could not access the microphone.")
        return None

    if int(np.max(np.abs(audio_np))) < 150:
        return None

    wav_bytes = _to_wav_bytes(audio_np, sample_rate)
    recognizer = sr.Recognizer()

    with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data)
        logger.info("Recognised: %s", text)
        return text.lower().strip()
    except sr.UnknownValueError:
        speak("Sorry, I did not catch that.")
        return None
    except sr.RequestError as exc:
        logger.error("STT error: %s", exc)
        speak("Speech service unavailable.")
        return None


def list_available_voices():
    voices = _get_tts_engine()