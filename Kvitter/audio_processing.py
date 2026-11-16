"""Optional audio processing used during analysis, never during export."""

import numpy as np
from scipy.signal import butter, sosfiltfilt


def bandpass_filter(
    audio: np.ndarray,
    sample_rate: int,
    low_hz: float = 1000.0,
    high_hz: float = 10000.0,
) -> np.ndarray:
    """Return a filtered copy of audio, preserving its channel layout."""
    nyquist = sample_rate / 2
    if low_hz <= 0 or high_hz <= low_hz or high_hz >= nyquist:
        raise ValueError("Bandpassgränserna måste ligga under ljudets Nyquist-frekvens.")

    sections = butter(
        4,
        (low_hz / nyquist, high_hz / nyquist),
        btype="bandpass",
        output="sos",
    )
    try:
        return sosfiltfilt(sections, audio, axis=0)
    except ValueError as error:
        raise ValueError("Ljudfilen är för kort för det valda bandpassfiltret.") from error