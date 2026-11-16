"""Local Streamlit interface for finding and exporting bird-sound clips."""

import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from audio_io import (
    SUPPORTED_AUDIO_EXTENSIONS,
    audio_to_wav_bytes,
    export_segments,
    load_audio,
)
from audio_processing import bandpass_filter
from bird_mixit import download_model, model_is_ready
from detect_segments import detect_segments, validate_segments


APP_DIR = Path(__file__).resolve().parent
TEST_AUDIO = APP_DIR / "XC1047941 - nötskrika - Garrulus glandarius.wav"
OUTPUT_DIR = APP_DIR / "output"
PREVIEW_SECONDS = 30.0
SEPARATION_MODEL_DIR = APP_DIR / ".models" / "bird_mixit" / "output_sources4"
SEPARATION_PYTHON = APP_DIR / ".venv-separation" / "Scripts" / "python.exe"

st.set_page_config(page_title="Kvitter | Fågelklippare", page_icon="♫", layout="wide")
st.title("Kvitter")
st.caption("Hitta, granska och exportera fågelljudsklipp")

source_mode = st.sidebar.radio("Ljudkälla", ("Testljud", "Ladda upp ljudfil"))
source_name = ""
source_bytes = b""

if source_mode == "Testljud":
    if not TEST_AUDIO.is_file():
        st.error(f"Testljudet saknas: {TEST_AUDIO.name}")
        st.stop()
    source_name = TEST_AUDIO.name
    source_bytes = TEST_AUDIO.read_bytes()
else:
    upload = st.sidebar.file_uploader(
        "Välj ljudfil",
        type=SUPPORTED_AUDIO_EXTENSIONS,
        help="Stöder bland annat WAV, FLAC, MP3, OGG, AIFF, AU och CAF.",
    )
    if upload is None:
        st.info("Välj en WAV-fil i sidopanelen för att börja.")
        st.stop()
    source_name = upload.name
    source_bytes = upload.getvalue()

source_id = hashlib.sha256(source_bytes).hexdigest()
try:
    audio, sample_rate = load_audio(io.BytesIO(source_bytes))
except (RuntimeError, ValueError, OSError) as error:
    st.error(f"Kunde inte läsa ljudfilen: {error}")
    st.stop()

duration = len(audio) / sample_rate
channels = audio.shape[1]
metadata = st.columns(4)
metadata[0].metric("Längd", f"{duration:.2f} s")
metadata[1].metric("Samplingsfrekvens", f"{sample_rate:,} Hz".replace(",", " "))
metadata[2].metric("Kanaler", str(channels))
metadata[3].metric("Upplösning", "Flyttal under analys")

with st.expander("Lyssna på originalet", expanded=False):
    st.audio(source_bytes, format="audio/wav")

mode = st.radio("Arbetsläge", ("Klippning", "Bird-MixIT-separering"), horizontal=True)

preview_start = 0.0
if duration > PREVIEW_SECONDS:
    preview_start = st.slider(
        "Visa tidsfönster från (sekunder)",
        min_value=0.0,
        max_value=max(0.0, duration - PREVIEW_SECONDS),
        value=0.0,
        step=max(0.1, min(5.0, duration / 1000)),
    )
preview_end = min(duration, preview_start + PREVIEW_SECONDS)
first_frame = int(preview_start * sample_rate)
last_frame = min(len(audio), int(preview_end * sample_rate))
preview = audio[first_frame:last_frame]

figure, (wave_axis, spec_axis) = plt.subplots(
    2,
    1,
    figsize=(12, 6),
    sharex=False,
    gridspec_kw={"height_ratios": (1, 1.4)},
)
plot_step = max(1, len(preview) // 100_000)
plot_times = preview_start + np.arange(0, len(preview), plot_step) / sample_rate
for channel in range(min(channels, 2)):
    wave_axis.plot(
        plot_times,
        preview[::plot_step, channel],
        linewidth=0.45,
        label=f"Kanal {channel + 1}",
    )
wave_axis.set_ylabel("Amplitud")
wave_axis.legend(loc="upper right", ncol=min(channels, 2))
wave_axis.grid(alpha=0.2)

nfft = min(2048, max(64, 2 ** int(np.floor(np.log2(max(64, len(preview)))))))
noverlap = min(nfft - 1, nfft * 3 // 4)
spec_axis.specgram(
    preview[:, 0],
    NFFT=nfft,
    Fs=sample_rate,
    noverlap=noverlap,
    xextent=(preview_start, preview_end),
    cmap="magma",
    vmin=-100,
    vmax=0,
)
spec_axis.set_ylim(0, min(12_000, sample_rate / 2))
spec_axis.set_ylabel("Frekvens (Hz)")
spec_axis.set_xlabel("Tid (sekunder)")
spec_axis.set_title("Spektrogram, kanal 1")
figure.tight_layout()
st.pyplot(figure, width="stretch")
plt.close(figure)

if mode == "Bird-MixIT-separering":
    st.subheader("Separera fågelljud")
    st.warning(
        "Bird-MixIT skapar fyra uppskattade ljudspår, inte ett säkert spår per fågel. "
        "Ett spår kan innehålla flera fåglar, bakgrundsljud eller artefakter. "
        "Modellen använder mono och 22,05 kHz; originalet ändras inte."
    )

    model_ready = model_is_ready(SEPARATION_MODEL_DIR)
    if not model_ready:
        st.caption("Bird-MixIT-modellen är cirka 108 MiB och hämtas bara om du begär det.")
        if st.button("Hämta Bird-MixIT-modellen"):
            progress = st.progress(0.0)
            status = st.empty()

            def update_download(done: int, total: int, filename: str) -> None:
                progress.progress(min(done / total, 1.0))
                status.write(f"Hämtar {filename}: {done / total:.0%}")

            try:
                download_model(SEPARATION_MODEL_DIR, update_download)
                model_ready = True
                status.success("Modellen hämtades och kontrollsummorna stämmer.")
            except (OSError, ValueError) as error:
                st.error(f"Modellen kunde inte hämtas: {error}")

    if not SEPARATION_PYTHON.is_file():
        st.info("Separering körs i en egen TensorFlow-miljö för att lämna klippningen orörd.")
        st.code("setup_separation.bat", language="text")

    if model_ready and SEPARATION_PYTHON.is_file():
        if st.button("Separera inspelningen", type="primary"):
            output_dir = (
                OUTPUT_DIR
                / "bird_mixit"
                / f"{Path(source_name).stem}_{source_id[:10]}"
            )
            try:
                with tempfile.TemporaryDirectory(prefix="kvitter-separation-") as temp_dir:
                    input_path = Path(temp_dir) / f"input{Path(source_name).suffix.lower()}"
                    input_path.write_bytes(source_bytes)
                    environment = os.environ.copy()
                    environment["TF_CPP_MIN_LOG_LEVEL"] = "2"
                    with st.spinner("Bird-MixIT separerar ljudet. Det kan ta en stund."):
                        result = subprocess.run(
                            [
                                str(SEPARATION_PYTHON),
                                str(APP_DIR / "separation_worker.py"),
                                "--input",
                                str(input_path),
                                "--model-dir",
                                str(SEPARATION_MODEL_DIR),
                                "--output-dir",
                                str(output_dir),
                            ],
                            capture_output=True,
                            text=True,
                            timeout=1800,
                            check=False,
                            env=environment,
                        )
                if result.returncode != 0:
                    st.error("Separeringen misslyckades.")
                    st.code(result.stderr[-4000:] or result.stdout[-4000:])
                else:
                    st.session_state["separated_files"] = sorted(
                        output_dir.glob("source_*.wav")
                    )
                    st.session_state["separated_source_id"] = source_id
            except (OSError, subprocess.SubprocessError) as error:
                st.error(f"Separeringen kunde inte starta eller slutföras: {error}")

    if st.session_state.get("separated_source_id") == source_id:
        separated_files = st.session_state.get("separated_files", [])
        if separated_files:
            st.write("Lyssna på spåren var för sig och hämta de som är användbara.")
            for source_path in separated_files:
                with st.expander(source_path.stem.replace("_", " "), expanded=True):
                    source_bytes_out = source_path.read_bytes()
                    st.audio(source_bytes_out, format="audio/wav")
                    st.download_button(
                        "Hämta spår",
                        source_bytes_out,
                        file_name=source_path.name,
                        mime="audio/wav",
                        key=f"download_{source_id}_{source_path.stem}",
                    )
                    st.caption(f"Sparat i `{source_path.parent.relative_to(APP_DIR)}`")
    st.stop()

st.subheader("Hitta ljudhändelser")
settings = st.columns(4)
threshold_db = settings[0].slider(
    "Tröskel över bakgrund (dB)", min_value=3.0, max_value=30.0, value=8.0, step=1.0
)
min_duration = settings[1].slider(
    "Minsta längd (s)", min_value=0.03, max_value=1.0, value=0.12, step=0.01
)
merge_gap = settings[2].slider(
    "Slå ihop vid tystnad upp till (s)",
    min_value=0.0,
    max_value=10.0,
    value=2.5,
    step=0.1,
)
padding = settings[3].slider(
    "Marginal före/efter (s)", min_value=0.0, max_value=0.5, value=0.1, step=0.01
)

can_filter = sample_rate > 22_000
use_filter = st.checkbox(
    "Använd bandpass 1-10 kHz vid detektion (exporten behåller originalet)",
    value=False,
    disabled=not can_filter,
)
if not can_filter:
    st.caption("Bandpassanalys kräver en samplingsfrekvens över 22 kHz.")
st.caption(
    "Sammanfogningen styrs bara av tystnadstid, inte fågelidentitet. "
    "Om en annan fågel låter i mellanrummet kan även dess läte hamna i samma klipp."
)

if st.button("Hitta klipp", type="primary"):
    try:
        analysis_audio = (
            bandpass_filter(audio, sample_rate) if use_filter else audio
        )
        st.session_state["segments"] = detect_segments(
            analysis_audio,
            sample_rate,
            threshold_db=threshold_db,
            min_duration=min_duration,
            merge_gap=merge_gap,
            padding=padding,
        )
        st.session_state["segments_source_id"] = source_id
    except ValueError as error:
        st.error(f"Kunde inte analysera ljudet: {error}")

if st.session_state.get("segments_source_id") != source_id:
    st.session_state.pop("segments", None)
    st.session_state["segments_source_id"] = source_id

segments = st.session_state.get("segments")
if segments is None:
    st.info("Justera inställningarna och välj Hitta klipp för att skapa förslag.")
elif not segments:
    st.warning("Inga ljudhändelser hittades. Prova en lägre tröskel eller kortare minsta längd.")
else:
    st.write(f"{len(segments)} förslag hittades. Granska gränser och etiketter före export.")
    table_data = [
        {
            "Behåll": True,
            "Start (s)": round(segment["start"], 3),
            "Slut (s)": round(segment["end"], 3),
            "Etikett": "",
        }
        for segment in segments
    ]
    edited = st.data_editor(
        pd.DataFrame(table_data),
        hide_index=True,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "Behåll": st.column_config.CheckboxColumn("Behåll", default=True),
            "Start (s)": st.column_config.NumberColumn(
                "Start (s)", min_value=0.0, max_value=duration, step=0.01, format="%.3f"
            ),
            "Slut (s)": st.column_config.NumberColumn(
                "Slut (s)", min_value=0.0, max_value=duration, step=0.01, format="%.3f"
            ),
            "Etikett": st.column_config.TextColumn("Etikett / artnamn"),
        },
        key=f"segments_editor_{source_id}",
    )
    valid_segments = validate_segments(
        edited.to_dict(orient="records"), len(audio), sample_rate
    )

    if valid_segments:
        clip_labels = [
            f"{index + 1}: {segment['start']:.3f} - {segment['end']:.3f} s"
            for index, segment in enumerate(valid_segments)
        ]
        preview_choice = st.selectbox("Förhandslyssna på godkänt klipp", clip_labels)
        chosen_index = clip_labels.index(preview_choice)
        chosen = valid_segments[chosen_index]
        clip_audio = audio[
            round(float(chosen["start"]) * sample_rate) : round(
                float(chosen["end"]) * sample_rate
            )
        ]
        st.audio(audio_to_wav_bytes(clip_audio, sample_rate), format="audio/wav")

    if st.button("Exportera godkända klipp", disabled=not valid_segments):
        try:
            exported, manifest = export_segments(
                audio,
                sample_rate,
                source_name,
                valid_segments,
                OUTPUT_DIR,
            )
            st.success(f"{len(exported)} klipp exporterades till mappen output.")
            st.write(f"Tids- och etikettlista: `{manifest.name}`")
            for path in exported:
                st.write(f"- `{path.name}`")
        except (OSError, RuntimeError, ValueError) as error:
            st.error(f"Exporten misslyckades: {error}")

st.caption("Detekteringen identifierar varken arter eller individer. Granska klipp och märk arter manuellt.")