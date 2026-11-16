"""Audio loading and non-destructive WAV clip export."""

import csv
import io
import re
from datetime import datetime
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


def _safe_component(value: str) -> str:
    component = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip("._")
    return component[:80] or "klipp"


def _unique_path(path: Path) -> Path:
    candidate = path
    suffix = 2
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}-{suffix:02d}{path.suffix}")
        suffix += 1
    return candidate


def export_segments(
    audio: np.ndarray,
    sample_rate: int,
    source_name: str,
    segments: list[dict[str, object]],
    output_dir: str | Path,
) -> tuple[list[Path], Path]:
    """Write selected regions from the original audio and a CSV manifest."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    source_stem = _safe_component(Path(source_name).stem)
    exported_paths = []
    manifest_rows = []

    for segment in segments:
        start = float(segment["start"])
        end = float(segment["end"])
        start_index = max(0, min(round(start * sample_rate), len(audio)))
        end_index = max(0, min(round(end * sample_rate), len(audio)))
        if end_index <= start_index:
            continue

        label = _safe_component(str(segment.get("label", "")))
        start_ms = round(start_index * 1000 / sample_rate)
        end_ms = round(end_index * 1000 / sample_rate)
        filename = (
            f"{source_stem}_{start_ms // 60000:02d}m"
            f"{(start_ms // 1000) % 60:02d}.{start_ms % 1000:03d}s-"
            f"{end_ms // 60000:02d}m{(end_ms // 1000) % 60:02d}."
            f"{end_ms % 1000:03d}s_{label}.wav"
        )
        clip_path = _unique_path(destination / filename)
        sf.write(clip_path, audio[start_index:end_index], sample_rate, subtype="PCM_16")
        exported_paths.append(clip_path)
        manifest_rows.append(
            {
                "fil": clip_path.name,
                "start_sekunder": f"{start_index / sample_rate:.3f}",
                "slut_sekunder": f"{end_index / sample_rate:.3f}",
                "etikett": str(segment.get("label", "")).strip(),
            }
        )

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    manifest_path = _unique_path(destination / f"manifest-{timestamp}.csv")
    with manifest_path.open("w", encoding="utf-8-sig", newline="") as manifest_file:
        writer = csv.DictWriter(
            manifest_file,
            fieldnames=("fil", "start_sekunder", "slut_sekunder", "etikett"),
        )
        writer.writeheader()
        writer.writerows(manifest_rows)
    return exported_paths, manifest_path