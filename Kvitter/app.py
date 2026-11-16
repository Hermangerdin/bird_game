"""Local Streamlit interface for separating and editing bird sounds."""

import hashlib
import io
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from audio_io import SUPPORTED_AUDIO_EXTENSIONS, audio_to_wav_bytes, load_audio
from audio_processing import normalize_audio, selection_time_bounds
from bird_mixit import download_model, model_is_ready


APP_DIR = Path(__file__).resolve().parent
TEST_AUDIO = APP_DIR / "XC1047941 - nötskrika - Garrulus glandarius.wav"
OUTPUT_DIR = APP_DIR / "output" / "bird_mixit"
SEPARATION_MODEL_DIR = APP_DIR / ".models" / "bird_mixit" / "output_sources4"
SEPARATION_PYTHON = APP_DIR / ".venv-separation" / "Scripts" / "python.exe"
MAX_WAVEFORM_POINTS = 100_000
NORMALIZE_TARGET_DB = -1.0

st.set_page_config(page_title="Kvitter | Ljudseparering", page_icon="♫", layout="wide")
st.title("Kvitter")
st.caption("Separera, välj och redigera fågelljud")

source_mode = st.sidebar.radio("Ljudkälla", ("Testljud", "Ladda upp ljudfil"))
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
        st.info("Välj en ljudfil i sidopanelen för att börja.")
        st.stop()
    source_name = upload.name
    source_bytes = upload.getvalue()

source_id = hashlib.sha256(source_bytes).hexdigest()
try:
    original_audio, original_rate = load_audio(io.BytesIO(source_bytes))
except (RuntimeError, ValueError, OSError) as error:
    st.error(f"Kunde inte läsa ljudfilen: {error}")
    st.stop()

original_duration = len(original_audio) / original_rate
metadata = st.columns(3)
metadata[0].metric("Längd", f"{original_duration:.2f} s")
metadata[1].metric("Samplingsfrekvens", f"{original_rate:,} Hz".replace(",", " "))
metadata[2].metric("Kanaler", str(original_audio.shape[1]))

st.subheader("1. Lyssna på originalet")
st.audio(audio_to_wav_bytes(original_audio, original_rate), format="audio/wav")

st.subheader("2. Separera med Bird-MixIT")
st.caption(
    "Modellen skapar fyra uppskattade ljudspår, inte säkert ett spår per fågel. "
    "Ett spår kan innehålla flera fåglar, bakgrundsljud eller artefakter."
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
            status.success("Modellen hämtades och kontrollsummorna stämmer.")
            st.rerun()
        except (OSError, ValueError) as error:
            st.error(f"Modellen kunde inte hämtas: {error}")

if not SEPARATION_PYTHON.is_file():
    st.info("Installera den separata TensorFlow-miljön en gång:")
    st.code("setup_separation.bat", language="text")

separated_files: list[Path] = []
if st.session_state.get("separated_source_id") == source_id:
    separated_files = [
        Path(path)
        for path in st.session_state.get("separated_files", [])
        if Path(path).is_file()
    ]

if model_ready and SEPARATION_PYTHON.is_file():
    if st.button(
        "Separera inspelningen",
        type="primary",
        disabled=bool(separated_files),
    ):
        output_dir = OUTPUT_DIR / f"{Path(source_name).stem}_{source_id[:10]}"
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
                generated_files = sorted(output_dir.glob("source_*.wav"))
                if len(generated_files) != 4:
                    st.error(
                        f"Modellen skulle skapa fyra spår men skapade "
                        f"{len(generated_files)}."
                    )
                else:
                    st.session_state["separated_files"] = [
                        str(path) for path in generated_files
                    ]
                    st.session_state["separated_source_id"] = source_id
                    st.rerun()
        except (OSError, subprocess.SubprocessError) as error:
            st.error(f"Separeringen kunde inte starta eller slutföras: {error}")

if not separated_files:
    st.info("Separera inspelningen för att välja ett modellspår och redigera det.")
    st.stop()

source_options = [path.stem.replace("_", " ") for path in separated_files]
selected_label = st.selectbox("Välj ett av de fyra modellspåren", source_options)
selected_path = separated_files[source_options.index(selected_label)]
track_id = f"{source_id}_{selected_path.stem}"
track_bytes = selected_path.read_bytes()
try:
    model_audio, model_rate = load_audio(io.BytesIO(track_bytes))
except (RuntimeError, ValueError, OSError) as error:
    st.error(f"Kunde inte läsa det separerade ljudspåret: {error}")
    st.stop()

processed_key = f"processed_audio_{track_id}"
if st.session_state.get("active_track_id") != track_id:
    st.session_state["active_track_id"] = track_id
    st.session_state.pop("selection_start", None)
    st.session_state.pop("selection_end", None)

processed_audio = st.session_state.get(processed_key, model_audio)
normalized = processed_key in st.session_state
track_duration = len(processed_audio) / model_rate
editable_duration = min(original_duration, track_duration)
if editable_duration <= 0:
    st.error("Originalet och modellspåret måste båda innehålla ljud.")
    st.stop()

st.subheader("3. Välj och normalisera ljudet")
comparison_columns = st.columns(2)
with comparison_columns[0]:
    st.markdown("**Före normalisering**")
    st.audio(audio_to_wav_bytes(model_audio, model_rate), format="audio/wav")
with comparison_columns[1]:
    st.markdown("**Efter normalisering**")
    if normalized:
        st.audio(audio_to_wav_bytes(processed_audio, model_rate), format="audio/wav")
    else:
        st.info("Normalisera ljudet för att jämföra resultatet här.")
if normalized:
    st.success("Normaliserat till -1 dBFS med borttagen DC-offset.")
else:
    st.caption(
        "Normalisering tar bort DC-offset och ställer toppnivån till -1 dBFS, "
        "som standard i Audacity."
    )
if st.button("Normalisera", disabled=normalized):
    try:
        st.session_state[processed_key] = normalize_audio(
            model_audio,
            target_db=NORMALIZE_TARGET_DB,
        )
        st.rerun()
    except ValueError as error:
        st.error(f"Kunde inte normalisera ljudet: {error}")

st.subheader("4. Markera och klipp en sammanhängande del")
st.caption(
    "Dra från start till slut över vågformen för att markera en del, precis som "
    "i Audacity. Välj Markera, Zooma eller Panorera med knapparna. Den markerade "
    "delen visas på bilden; du kan finjustera start och slut nedan."
)
start_key = f"start_input_{track_id}"
end_key = f"end_input_{track_id}"
default_end = min(5.0, editable_duration)
if start_key not in st.session_state:
    st.session_state[start_key] = st.session_state.get("selection_start", 0.0)
if end_key not in st.session_state:
    st.session_state[end_key] = st.session_state.get("selection_end", default_end)
marked_start = float(st.session_state[start_key])
marked_end = float(st.session_state[end_key])

mode_key = f"waveform_mode_{track_id}"
if mode_key not in st.session_state:
    st.session_state[mode_key] = "select"
mode_controls = st.columns(3)
for column, (mode, label) in zip(
    mode_controls,
    (("select", "Markera"), ("zoom", "Zooma"), ("pan", "Panorera")),
):
    with column:
        if st.button(
            label,
            key=f"{mode_key}_{mode}",
            type="primary" if st.session_state[mode_key] == mode else "secondary",
            use_container_width=True,
        ):
            st.session_state[mode_key] = mode
            st.rerun()

plot_step = max(1, len(processed_audio) // MAX_WAVEFORM_POINTS)
plot_audio = processed_audio[::plot_step, 0]
plot_times = np.arange(len(plot_audio)) * plot_step / model_rate
figure = go.Figure(
    go.Scattergl(
        x=plot_times,
        y=plot_audio,
        mode="lines",
        line={"width": 1, "color": "#2d8a68"},
        hovertemplate="Aika: %{x:.3f} s<br>Amplitudi: %{y:.4f}<extra></extra>",
    )
)
figure.add_vrect(
    x0=marked_start,
    x1=marked_end,
    fillcolor="rgba(45, 138, 104, 0.22)",
    line_width=0,
    layer="below",
)
for boundary, label in ((marked_start, "Start"), (marked_end, "Slut")):
    figure.add_vline(
        x=boundary,
        line={"color": "#176b4d", "width": 2, "dash": "dash"},
        annotation_text=label,
        annotation_position="top",
        layer="below",
    )
figure.update_layout(
    height=300,
    margin={"l": 35, "r": 20, "t": 15, "b": 35},
    xaxis_title="Tid (sekunder)",
    yaxis_title="Amplitudi",
    dragmode=st.session_state[mode_key],
    selectdirection="h",
    showlegend=False,
    uirevision=track_id,
)
figure.update_xaxes(range=[0, editable_duration], fixedrange=False)
waveform_columns = st.columns([1, 3])
with waveform_columns[0]:
    st.markdown("**Spela markerad del**")
    marked_clip = processed_audio[
        round(marked_start * model_rate) : round(marked_end * model_rate)
    ]
    if len(marked_clip):
        st.audio(audio_to_wav_bytes(marked_clip, model_rate), format="audio/wav")
    else:
        st.caption("Markera en del av vågformen för att spela upp den.")
with waveform_columns[1]:
    chart_event = st.plotly_chart(
        figure,
        key=f"waveform_{track_id}",
        on_select="rerun",
        selection_mode="box",
        config={"scrollZoom": True, "displayModeBar": True},
    )

selection_bounds = selection_time_bounds(chart_event.selection)
if selection_bounds is not None:
    start, end = selection_bounds
    selection_signature = (round(start, 6), round(end, 6))
    if end - start >= 1 / model_rate:
        signature_key = f"selection_signature_{track_id}"
        if st.session_state.get(signature_key) != selection_signature:
            st.session_state["selection_start"] = max(0.0, min(start, editable_duration))
            st.session_state["selection_end"] = max(0.0, min(end, editable_duration))
            st.session_state[f"start_input_{track_id}"] = st.session_state[
                "selection_start"
            ]
            st.session_state[f"end_input_{track_id}"] = st.session_state[
                "selection_end"
            ]
            st.session_state[signature_key] = selection_signature
            st.rerun()

boundary_columns = st.columns(2)
start_time = boundary_columns[0].number_input(
    "Start (sekunder)",
    min_value=0.0,
    max_value=editable_duration,
    step=0.001,
    format="%.3f",
    key=start_key,
)
end_time = boundary_columns[1].number_input(
    "Slut (sekunder)",
    min_value=0.0,
    max_value=editable_duration,
    step=0.001,
    format="%.3f",
    key=end_key,
)
if start_time >= end_time:
    st.error("Sluttiden måste vara större än starttiden.")
    st.stop()

original_clip = original_audio[
    round(start_time * original_rate) : round(end_time * original_rate)
]
processed_clip = processed_audio[
    round(start_time * model_rate) : round(end_time * model_rate)
]
if not len(original_clip) or not len(processed_clip):
    st.error("Den markerade delen är för kort för att spelas upp.")
    st.stop()

st.subheader("5. Jämför samma del och hämta")
play_columns = st.columns(2)
with play_columns[0]:
    st.markdown("**Original**")
    st.audio(audio_to_wav_bytes(original_clip, original_rate), format="audio/wav")
with play_columns[1]:
    st.markdown("**Valt modellspår**")
    st.audio(audio_to_wav_bytes(processed_clip, model_rate), format="audio/wav")

export_name = (
    f"{Path(source_name).stem}_{selected_path.stem}_"
    f"{round(start_time * 1000)}-{round(end_time * 1000)}ms.wav"
)
st.download_button(
    "Hämta markerat ljud",
    data=audio_to_wav_bytes(processed_clip, model_rate),
    file_name=export_name,
    mime="audio/wav",
    type="primary",
)
