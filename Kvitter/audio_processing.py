"""Audio processing helpers for Bird-MixIT source editing."""

from collections.abc import Mapping

import numpy as np


def selection_time_bounds(
    selection: Mapping[str, object],
) -> tuple[float, float] | None:
    """Return the time interval from a Plotly box selection or selected points."""
    boxes = selection.get("box")
    if isinstance(boxes, list):
        for box in reversed(boxes):
            if not isinstance(box, Mapping):
                continue
            coordinates = box.get("x")
            if not isinstance(coordinates, list) or len(coordinates) != 2:
                continue
            try:
                start, end = (float(value) for value in coordinates)
            except (TypeError, ValueError):
                continue
            if np.isfinite(start) and np.isfinite(end) and start != end:
                return min(start, end), max(start, end)

    points = selection.get("points")
    if isinstance(points, list):
        times = []
        for point in points:
            if not isinstance(point, Mapping) or point.get("x") is None:
                continue
            try:
                time = float(point["x"])
            except (TypeError, ValueError):
                continue
            if np.isfinite(time):
                times.append(time)
        if len(times) >= 2 and min(times) != max(times):
            return min(times), max(times)
    return None


def normalize_audio(audio: np.ndarray, target_db: float = -1.0) -> np.ndarray:
    """Remove per-channel DC offset and apply linked peak gain to the target level."""
    samples = np.asarray(audio, dtype=np.float32)
    if samples.ndim not in (1, 2) or samples.shape[0] == 0:
        raise ValueError("Ljudet måste innehålla sampel i en eller två dimensioner.")
    if not np.all(np.isfinite(samples)):
        raise ValueError("Ljudet innehåller ogiltiga värden.")
    if not np.isfinite(target_db) or target_db > 0:
        raise ValueError("Normaliseringens toppnivå måste vara högst 0 dBFS.")

    centered = samples - np.mean(samples)
    peak = float(np.max(np.abs(centered)))
    if peak == 0:
        return np.asarray(centered, dtype=np.float32)

    target_peak = 10 ** (target_db / 20)
    return np.asarray(centered * (target_peak / peak), dtype=np.float32)