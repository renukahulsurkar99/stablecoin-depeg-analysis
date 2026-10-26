"""Project paths and validation for daily cryptocurrency prices."""

import os
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("STABLECOIN_DATA_DIR", PROJECT_DIR / "data"))
OUTPUT_DIR = Path(os.environ.get("STABLECOIN_OUTPUT_DIR", PROJECT_DIR / "outputs"))


def load_price_data(path):
    """Require complete, unique daily observations before detecting episodes."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing input: {path}. See data/README.md for the required format."
        )
    df = pd.read_csv(path)
    required = ["date", "usdt", "usdc", "dai", "bitcoin"]
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if df.empty:
        raise ValueError("Price data must contain at least one daily observation.")
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    if df["date"].isna().any() or df["date"].duplicated().any():
        raise ValueError("Dates must be non-missing and unique.")
    if not df["date"].eq(df["date"].dt.normalize()).all():
        raise ValueError("Use daily dates without intraday timestamps.")
    df = df.sort_values("date").reset_index(drop=True)
    if not df["date"].diff().dropna().eq(pd.Timedelta(days=1)).all():
        raise ValueError("Price data must have consecutive daily dates without gaps.")
    for coin in required[1:]:
        df[coin] = pd.to_numeric(df[coin], errors="raise")
        if not np.isfinite(df[coin]).all() or (df[coin] <= 0).any():
            raise ValueError(f"{coin} prices must be finite, positive and non-missing.")
    return df
