import hashlib
import io
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from audio_io import audio_to_wav_bytes, export_segments, load_audio
from audio_processing import bandpass_filter
from detect_segments import detect_segments
from separation_worker import MODEL_SAMPLE_RATE, normalize_sources, prepare_mono_audio


class AudioPipelineTests(unittest.TestCase):
    def test_load_audio_accepts_flac(self):
        audio = np.linspace(-0.2, 0.2, 1600, dtype=np.float32)[:, np.newaxis]
        encoded = io.BytesIO()
        sf.write(encoded, audio, 16000, format="FLAC")
        encoded.seek(0)

        loaded, sample_rate = load_audio(encoded)

        self.assertEqual(sample_rate, 16000)
        self.assertEqual(loaded.shape, audio.shape)
        self.assertTrue(np.allclose(loaded, audio, atol=1e-4))

    def test_separation_input_is_downmixed_and_resampled(self):
        audio = np.ones((48000, 2), dtype=np.float32)
        mono = prepare_mono_audio(audio, 48000)

        self.assertEqual(len(mono), MODEL_SAMPLE_RATE)
        self.assertTrue(np.allclose(mono[100:-100], 1.0, atol=1e-4))

    def test_separation_output_is_normalized_to_samples_by_sources(self):
        output = np.zeros((1, 100, 4), dtype=np.float32)
        sources = normalize_sources(output)

        self.assertEqual(sources.shape, (100, 4))

    def test_bundled_recording_can_be_analyzed_and_exported_without_modification(self):
        project_dir = Path(__file__).resolve().parents[1]
        source = project_dir / "XC1047941 - nötskrika - Garrulus glandarius.wav"
        original_digest = hashlib.sha256(source.read_bytes()).digest()

        audio, sample_rate = load_audio(source)
        filtered = bandpass_filter(audio, sample_rate)
        candidates = detect_segments(filtered, sample_rate, min_duration=0.1)

        self.assertEqual(audio.shape, filtered.shape)
        self.assertEqual(audio.shape[1], 2)
        self.assertTrue(candidates)
        preview_bytes = audio_to_wav_bytes(audio[: sample_rate // 2], sample_rate)
        preview_audio, preview_rate = load_audio(io.BytesIO(preview_bytes))
        self.assertEqual(preview_rate, sample_rate)
        self.assertEqual(preview_audio.shape, (sample_rate // 2, 2))

        with tempfile.TemporaryDirectory() as output_dir:
            clips, manifest = export_segments(
                audio,
                sample_rate,
                source.name,
                [{"start": 0.0, "end": 0.5, "label": "smoketest"}],
                output_dir,
            )

            self.assertEqual(len(clips), 1)
            self.assertTrue(clips[0].is_file())
            self.assertTrue(manifest.is_file())
            clip_audio, clip_rate = load_audio(clips[0])
            self.assertEqual(clip_rate, sample_rate)
            self.assertEqual(len(clip_audio), round(0.5 * sample_rate))

        self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), original_digest)


if __name__ == "__main__":
    unittest.main()