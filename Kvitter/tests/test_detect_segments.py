import unittest

import numpy as np

from detect_segments import detect_segments, validate_segments


class DetectSegmentsTests(unittest.TestCase):
    def test_detects_and_pads_tone_region(self):
        sample_rate = 8000
        time = np.arange(sample_rate * 2) / sample_rate
        audio = np.zeros((len(time), 1), dtype=np.float32)
        active = (time >= 0.5) & (time < 1.0)
        audio[active, 0] = 0.5 * np.sin(2 * np.pi * 1200 * time[active])

        segments = detect_segments(
            audio,
            sample_rate,
            threshold_db=8,
            min_duration=0.1,
            merge_gap=0,
            padding=0.05,
        )

        self.assertEqual(len(segments), 1)
        self.assertLessEqual(segments[0]["start"], 0.46)
        self.assertGreaterEqual(segments[0]["end"], 1.04)

    def test_silence_has_no_candidates(self):
        audio = np.zeros((8000, 2), dtype=np.float32)
        self.assertEqual(detect_segments(audio, 8000), [])

    def test_merges_calls_across_two_second_gap_by_default(self):
        sample_rate = 8000
        time = np.arange(sample_rate * 11) / sample_rate
        audio = np.zeros((len(time), 1), dtype=np.float32)
        for start, end in ((1.0, 5.0), (7.0, 10.0)):
            active = (time >= start) & (time < end)
            audio[active, 0] = 0.5 * np.sin(2 * np.pi * 1200 * time[active])

        merged = detect_segments(audio, sample_rate, padding=0)
        separate = detect_segments(audio, sample_rate, merge_gap=1.5, padding=0)

        self.assertEqual(len(merged), 1)
        self.assertAlmostEqual(merged[0]["start"], 1.0, delta=0.03)
        self.assertAlmostEqual(merged[0]["end"], 10.0, delta=0.03)
        self.assertEqual(len(separate), 2)

    def test_validate_segments_clamps_and_skips_unchecked_or_empty_rows(self):
        rows = [
            {"Behåll": True, "Start (s)": -1, "Slut (s)": 2, "Etikett": "nötskrika"},
            {"Behåll": False, "Start (s)": 0, "Slut (s)": 1, "Etikett": ""},
            {"Behåll": True, "Start (s)": 1, "Slut (s)": 1, "Etikett": ""},
        ]

        result = validate_segments(rows, sample_count=8000, sample_rate=8000)

        self.assertEqual(
            result,
            [{"start": 0.0, "end": 1.0, "label": "nötskrika"}],
        )


if __name__ == "__main__":
    unittest.main()