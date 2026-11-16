"""Energy-based candidate detection for manual bird-call review."""

from collections.abc import Iterable

import numpy as np


def detect_segments(
    audio: np.ndarray,
    sample_rate: int,
    threshold_db: float = 8.0,
    min_duration: float = 0.12,
    merge_gap: float = 2.5,
    padding: float = 0.1,
    frame_ms: float = 20.0,
    hop_ms: float = 10.0,
) -> list[dict[str, float]]:
    """Find energetic regions and join regions separated by at most merge_gap
    seconds of silence. Return padded start/end times in seconds.

    The threshold is relative to the 20th-percentile frame level, with a
    -72 dBFS floor. This is a lightweight activity detector, not a bird or
    species or individual classifier.
    """
    samples = np.asarray(audio, dtype=np.float64)
    if samples.ndim == 1:
        samples = samples[:, np.newaxis]
    if samples.ndim != 2 or samples.shape[0] == 0 or sample_rate <= 0:
        raise ValueError("Ljudet måste innehålla minst en sampel och ha giltig samplingsfrekvens.")
    if not np.all(np.isfinite(samples)):
        raise ValueError("Ljudet innehåller ogiltiga värden.")

    frame_size = max(1, round(sample_rate * frame_ms / 1000))
    hop_size = max(1, round(sample_rate * hop_ms / 1000))
    starts = np.arange(0, samples.shape[0], hop_size, dtype=np.int64)
    ends = np.minimum(starts + frame_size, samples.shape[0])

    sample_power = np.mean(np.square(samples), axis=1)
    cumulative_power = np.concatenate(([0.0], np.cumsum(sample_power)))
    frame_power = (cumulative_power[ends] - cumulative_power[starts]) / (ends - starts)
    frame_db = 10 * np.log10(np.maximum(frame_power, 1e-16))
    noise_floor_db = float(np.percentile(frame_db, 20))
    active = frame_db >= max(noise_floor_db + threshold_db, -72.0)

    active_starts = np.flatnonzero(active & ~np.r_[False, active[:-1]])
    active_ends = np.flatnonzero(active & ~np.r_[active[1:], False])
    if active_starts.size == 0:
        return []

    regions: list[tuple[int, int]] = []
    for first_frame, last_frame in zip(active_starts, active_ends):
        start_sample = int(starts[first_frame])
        end_sample = int(ends[last_frame])
        if regions and start_sample - regions[-1][1] <= merge_gap * sample_rate:
            previous_start, previous_end = regions[-1]
            regions[-1] = (previous_start, max(previous_end, end_sample))
        else:
            regions.append((start_sample, end_sample))

    padding_samples = round(padding * sample_rate)
    results = []
    for start_sample, end_sample in regions:
        if (end_sample - start_sample) / sample_rate < min_duration:
            continue
        padded_start = max(0, start_sample - padding_samples)
        padded_end = min(samples.shape[0], end_sample + padding_samples)
        results.append(
            {
                "start": padded_start / sample_rate,
                "end": padded_end / sample_rate,
            }
        )
    return results


def validate_segments(
    segments: Iterable[dict[str, object]], sample_count: int, sample_rate: int
) -> list[dict[str, object]]:
    """Clamp edited segment boundaries and omit empty or unchecked rows."""
    duration = sample_count / sample_rate
    valid = []
    for segment in segments:
        if not bool(segment.get("Behåll", True)):
            continue
        try:
            start = min(max(float(segment["Start (s)"]), 0.0), duration)
            end = min(max(float(segment["Slut (s)"]), 0.0), duration)
        except (KeyError, TypeError, ValueError):
            continue
        if end <= start:
            continue
        valid.append(
            {
                "start": start,
                "end": end,
                "label": str(segment.get("Etikett", "")).strip(),
            }
        )
    return valid