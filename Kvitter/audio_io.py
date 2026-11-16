"""Audio loading and WAV encoding for previews and downloads."""

import io
from pathlib import Path
from typing import BinaryIO

import numpy as np
import soundfile as sf


SUPPORTED_AUDIO_EXTENSIONS = (
    "wav",
    "wave",
    "flac",
    "mp3",
    "ogg",
    "oga",
    "aiff",
    "aif",
    "au",
    "caf",
    "w64",
    "rf64",
    "sph",
)


def load_audio(source: str | Path | BinaryIO) -> tuple[np.ndarray, int]:
    """Load libsndfile-supported audio as float32 with shape (frames, channels)."""
    audio, sample_rate = sf.read(source, dtype="float32", always_2d=True)
    if audio.shape[0] == 0 or sample_rate <= 0:
        raise ValueError("Ljudfilen är tom eller har ogiltig samplingsfrekvens.")
    if not np.all(np.isfinite(audio)):
        raise ValueError("Ljudfilen innehåller ogiltiga ljudvärden.")
    return audio, int(sample_rate)


def audio_to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    """Encode audio as a standard 16-bit PCM WAV byte stream."""
    buffer = io.BytesIO()
    sf.write(buffer, audio, sample_rate, format="WAV", subtype="PCM_16")
    return buffer.getvalue()