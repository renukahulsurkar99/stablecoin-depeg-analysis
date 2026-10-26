"""Synthetic boundary cases for the sustained-recovery algorithm."""

from pathlib import Path
import tempfile
import unittest

import pandas as pd

from detect_depeg_episodes import find_episodes_confirmed
from project_config import load_price_data


def prices(values):
    return pd.DataFrame({
        "date": pd.date_range("2023-01-01", periods=len(values), freq="D"),
        "usdt": values,
        "usdc": [1.0] * len(values),
        "dai": [1.0] * len(values),
        "bitcoin": [20000.0] * len(values),
    })


class EpisodeDetectionTests(unittest.TestCase):
    def test_prices_at_band_boundaries_do_not_breach(self):
        self.assertEqual(find_episodes_confirmed(prices([0.995, 1.005, 1.0]), "usdt", 2), [])

    def test_two_days_confirm_recovery_at_first_return(self):
        episodes = find_episodes_confirmed(prices([0.98, 1.0, 1.0]), "usdt", 2)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["recovery_idx"], 1)
        self.assertEqual(episodes[0]["confirmation_idx"], 2)
        self.assertFalse(episodes[0]["censored"])

    def test_temporary_rebound_does_not_split_two_day_episode(self):
        df = prices([0.98, 1.0, 0.98, 1.0, 1.0])
        self.assertEqual(len(find_episodes_confirmed(df, "usdt", 1)), 2)
        episodes = find_episodes_confirmed(df, "usdt", 2)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["last_bad_idx"], 2)
        self.assertEqual(episodes[0]["recovery_idx"], 3)

    def test_insufficient_confirmation_is_censored(self):
        ep = find_episodes_confirmed(prices([0.98, 1.0]), "usdt", 2)[0]
        self.assertTrue(ep["censored"])
        self.assertIsNone(ep["recovery_idx"])

    def test_unrecovered_final_breach_is_censored(self):
        ep = find_episodes_confirmed(prices([1.0, 0.98, 0.97]), "usdt", 2)[0]
        self.assertTrue(ep["censored"])
        self.assertEqual(ep["last_bad_idx"], 2)


class PriceValidationTests(unittest.TestCase):
    def load(self, df):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            df.to_csv(path, index=False)
            return load_price_data(path)

    def test_missing_price_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "finite, positive"):
            self.load(prices([1.0, float("nan"), 1.0]))

    def test_duplicate_date_is_rejected(self):
        df = prices([1.0, 1.0, 1.0])
        df.loc[1, "date"] = df.loc[0, "date"]
        with self.assertRaisesRegex(ValueError, "unique"):
            self.load(df)

    def test_calendar_gap_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "without gaps"):
            self.load(prices([1.0, 1.0, 1.0]).drop(index=1))

    def test_nonpositive_price_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "finite, positive"):
            self.load(prices([1.0, 0.0, 1.0]))

    def test_rows_are_sorted_before_use(self):
        df = self.load(prices([1.0, 0.98, 1.0]).iloc[::-1])
        self.assertTrue(df["date"].is_monotonic_increasing)


if __name__ == "__main__":
    unittest.main()
