"""Run Bird-MixIT inference in its isolated TensorFlow environment."""

import argparse
import math
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly


MODEL_SAMPLE_RATE = 22_050
CHECKPOINT_PREFIX = "model.ckpt-3223090"
SOURCE_COUNT = 4


def prepare_mono_audio(audio: np.ndarray, sample_rate: int) -> np.ndarray:
    """Downmix audio and resample it to the rate expected by Bird-MixIT."""
    samples = np.asarray(audio, dtype=np.float32)
    if samples.ndim == 1:
        samples = samples[:, np.newaxis]
    if samples.ndim != 2 or samples.shape[0] == 0 or sample_rate <= 0:
        raise ValueError("Ljudet måste innehålla sampel och ha giltig samplingsfrekvens.")
    if not np.all(np.isfinite(samples)):
        raise ValueError("Ljudet innehåller ogiltiga värden.")

    mono = np.mean(samples, axis=1, dtype=np.float32)
    if sample_rate != MODEL_SAMPLE_RATE:
        divisor = math.gcd(sample_rate, MODEL_SAMPLE_RATE)
        mono = resample_poly(
            mono,
            MODEL_SAMPLE_RATE // divisor,
            sample_rate // divisor,
        )
    return np.asarray(mono, dtype=np.float32)


def normalize_sources(output: np.ndarray) -> np.ndarray:
    """Normalize the exported model tensor to shape (samples, sources)."""
    sources = np.asarray(output)
    if sources.ndim == 3 and sources.shape[0] == 1:
        sources = sources[0]
    if sources.ndim != 2:
        raise ValueError(f"Modellen gav oväntad ljudform: {sources.shape}.")
    if sources.shape[1] == SOURCE_COUNT:
        return sources
    if sources.shape[0] == SOURCE_COUNT:
        return sources.T
    raise ValueError(f"Modellen gav inte {SOURCE_COUNT} ljudspår: {sources.shape}.")


def separate_file(input_path: Path, model_dir: Path, output_dir: Path) -> list[Path]:
    import tensorflow.compat.v1 as tf

    tf.disable_v2_behavior()
    input_audio, input_rate = sf.read(input_path, dtype="float32", always_2d=True)
    mono_audio = prepare_mono_audio(input_audio, int(input_rate))

    graph = tf.Graph()
    meta_graph = model_dir / "inference.meta"
    checkpoint = model_dir / CHECKPOINT_PREFIX
    with graph.as_default():
        saver = tf.train.import_meta_graph(str(meta_graph), clear_devices=True)
        input_tensor = graph.get_tensor_by_name("input_audio/receiver_audio:0")
        output_tensor = graph.get_tensor_by_name("denoised_waveforms:0")

    output_dir.mkdir(parents=True, exist_ok=True)
    config = tf.ConfigProto(device_count={"GPU": 0}, intra_op_parallelism_threads=2)
    with tf.Session(graph=graph, config=config) as session:
        saver.restore(session, str(checkpoint))
        model_output = session.run(
            output_tensor,
            feed_dict={input_tensor: mono_audio[np.newaxis, np.newaxis, :]},
        )

    sources = normalize_sources(model_output)
    output_paths = []
    for source_index in range(SOURCE_COUNT):
        output_path = output_dir / f"source_{source_index + 1}.wav"
        sf.write(
            output_path,
            sources[:, source_index],
            MODEL_SAMPLE_RATE,
            subtype="PCM_16",
        )
        output_paths.append(output_path)
    return output_paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Separera fågelljud med Bird-MixIT.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    output_paths = separate_file(
        arguments.input,
        arguments.model_dir,
        arguments.output_dir,
    )
    for output_path in output_paths:
        print(output_path)


if __name__ == "__main__":
    main()