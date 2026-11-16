import hashlib
import io
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

from audio_io import audio_to_wav_bytes, load_audio
from audio_processing import normalize_audio, selection_time_bounds
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

    def test_normalize_removes_dc_offset_and_sets_peak_to_minus_one_db(self):
        audio = np.array([[-0.2, -0.1], [0.4, 0.3], [0.1, -0.2]], dtype=np.float32)

        normalized = normalize_audio(audio)

        self.assertAlmostEqual(float(np.mean(normalized)), 0.0, places=7)
        self.assertAlmostEqual(
            float(np.max(np.abs(normalized))),
            10 ** (-1 / 20),
            places=6,
        )
        self.assertAlmostEqual(
            float(np.max(np.abs(normalized[:, 0])) / np.max(np.abs(normalized[:, 1]))),
            float(
                np.max(np.abs(audio - np.mean(audio)), axis=0)[0]
                / np.max(np.abs(audio - np.mean(audio)), axis=0)[1]
            ),
            places=5,
        )

    def test_normalize_preserves_silence(self):
        silence = np.zeros((100, 1), dtype=np.float32)
        self.assertTrue(np.array_equal(normalize_audio(silence), silence))

    def test_normalize_rejects_invalid_values_and_positive_peak_target(self):
        with self.assertRaises(ValueError):
            normalize_audio(np.array([0.0, np.nan], dtype=np.float32))
        with self.assertRaises(ValueError):
            normalize_audio(np.ones(10, dtype=np.float32), target_db=0.1)

    def test_drag_box_bounds_set_exact_audio_selection(self):
        selection = {
            "box": [{"x": [2.125, 4.875], "y": [-0.5, 0.5]}],
            "points": [],
        }

        self.assertEqual(selection_time_bounds(selection), (2.125, 4.875))

    def test_selection_bounds_support_reverse_drag_and_selected_points(self):
        reverse_box = {"box": [{"x": [5.0, 1.0]}]}
        selected_points = {"points": [{"x": 1.25}, {"x": 3.75}]}

        self.assertEqual(selection_time_bounds(reverse_box), (1.0, 5.0))
        self.assertEqual(selection_time_bounds(selected_points), (1.25, 3.75))
        self.assertIsNone(selection_time_bounds({"box": [], "points": []}))

    def test_bundled_recording_round_trips_as_wav_without_modification(self):
        project_dir = Path(__file__).resolve().parents[1]
        source = project_dir / "XC1047941 - nötskrika - Garrulus glandarius.wav"
        original_digest = hashlib.sha256(source.read_bytes()).digest()

        audio, sample_rate = load_audio(source)
        preview_bytes = audio_to_wav_bytes(audio[: sample_rate // 2], sample_rate)
        preview_audio, preview_rate = load_audio(io.BytesIO(preview_bytes))

        self.assertEqual(preview_rate, sample_rate)
        self.assertEqual(preview_audio.shape, (sample_rate // 2, audio.shape[1]))
        self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), original_digest)


if __name__ == "__main__":
    unittest.main()
