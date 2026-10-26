"""
Builds the full-calendar regression dataset:
stablecoin deviations + BTC stress variables + Bloomberg VIX/Treasury yields.

IMPORTANT METHODOLOGICAL CHOICE
--------------------------------
Crypto trades 7 days/week, while VIX and Treasury yields are only
observed on traditional financial-market trading days.

For this full-calendar robustness dataset, VIX and Treasury LEVELS are
forward-filled across weekends and holidays. Therefore, on non-trading
days, these variables represent the LAST AVAILABLE market reading,
not a newly observed value.

Observed-value flags are retained:
    vix_observed
    us2y_observed
    us10y_observed

These equal:
    1 = Bloomberg observation exists on that date
    0 = value was missing and subsequently forward-filled

IMPORTANT:
Treasury yield CHANGES are calculated AFTER forward-filling the yield
levels. The changes themselves are NOT forward-filled.

Example:
    Friday    US10Y = 4.20
    Saturday  US10Y = 4.20
    Sunday    US10Y = 4.20
    Monday    US10Y = 4.30

Then:
    Saturday delta = 0.00
    Sunday   delta = 0.00
    Monday   delta = +0.10

Input files:
    merged_prices.csv
    BloombergDataValues.xlsx

Output:
    regression_dataset_full_calendar.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
from project_config import DATA_DIR, OUTPUT_DIR, load_price_data


# ============================================================
# FILE PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
CRYPTO_PATH = DATA_DIR / "merged_prices.csv"
BLOOMBERG_PATH = DATA_DIR / "BloombergDataValues.xlsx"
OUTPUT_PATH = OUTPUT_DIR / "regression_dataset_full_calendar.csv"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD CRYPTO DATA
# ============================================================

def load_crypto():

    df = load_price_data(CRYPTO_PATH)

    df["date"] = pd.to_datetime(df["date"])

    df = (
        df.sort_values("date")
          .reset_index(drop=True)
    )

    return df


# ============================================================
# ADD STABLECOIN FEATURES
# ============================================================

def add_stablecoin_features(df):

    for coin in ["usdt", "usdc", "dai"]:

        # Signed deviation from $1 in percentage points
        df[f"{coin}_dev_pct"] = (
            (df[coin] - 1.0) * 100
        )

        # Absolute deviation magnitude
        df[f"{coin}_abs_dev_pct"] = (
            df[f"{coin}_dev_pct"].abs()
        )

    return df


# ============================================================
# ADD BITCOIN STRESS VARIABLES
# ============================================================

def add_btc_features(df):

    # Daily log return, %
    df["btc_return_pct"] = (
        np.log(
            df["bitcoin"] /
            df["bitcoin"].shift(1)
        ) * 100
    )

    # Absolute daily return
    df["btc_abs_return_pct"] = (
        df["btc_return_pct"].abs()
    )

    # 7-day rolling volatility of BTC daily returns
    df["btc_vol_7d"] = (
        df["btc_return_pct"]
        .rolling(window=7)
        .std()
    )

    return df


# ============================================================
# LOAD BLOOMBERG DATA
# ============================================================

def load_bloomberg():

    xls = pd.ExcelFile(BLOOMBERG_PATH)

    # VIX
    vix = pd.read_excel(
        xls,
        sheet_name="VIX_raw",
        header=None,
        names=["date", "vix"]
    )

    # 2-Year Treasury yield
    us2y = pd.read_excel(
        xls,
        sheet_name="US2Y_raw",
        header=None,
        names=["date", "us2y"]
    )

    # 10-Year Treasury yield
    us10y = pd.read_excel(
        xls,
        sheet_name="US10Y_raw",
        header=None,
        names=["date", "us10y"]
    )

    # Clean each Bloomberg dataset
    for d in [vix, us2y, us10y]:

        d["date"] = pd.to_datetime(
            d["date"],
            errors="coerce"
        )

        d.dropna(
            subset=["date"],
            inplace=True
        )

        d.sort_values(
            "date",
            inplace=True
        )

        d.reset_index(
            drop=True,
            inplace=True
        )

    # Merge Bloomberg series together
    bb = (
        vix
        .merge(
            us2y,
            on="date",
            how="outer"
        )
        .merge(
            us10y,
            on="date",
            how="outer"
        )
        .sort_values("date")
        .reset_index(drop=True)
    )

    return bb


# ============================================================
# BUILD FULL-CALENDAR DATASET
# ============================================================

def build_full_calendar_dataset():

    # --------------------------------------------------------
    # Load and prepare crypto data
    # --------------------------------------------------------

    crypto = load_crypto()

    crypto = add_stablecoin_features(
        crypto
    )

    crypto = add_btc_features(
        crypto
    )

    # --------------------------------------------------------
    # Load Bloomberg
    # --------------------------------------------------------

    bloomberg = load_bloomberg()

    # --------------------------------------------------------
    # Merge on full crypto calendar
    # --------------------------------------------------------

    merged = crypto.merge(
        bloomberg,
        on="date",
        how="left"
    )

    # --------------------------------------------------------
    # Print missing values before forward-fill
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("MISSING VALUES BEFORE FORWARD-FILL")
    print("=" * 80)

    print(
        merged[
            ["vix", "us2y", "us10y"]
        ]
        .isna()
        .sum()
    )

    # --------------------------------------------------------
    # Record whether Bloomberg values were actually observed
    # --------------------------------------------------------

    for col in [
        "vix",
        "us2y",
        "us10y"
    ]:

        merged[f"{col}_observed"] = (
            merged[col]
            .notna()
            .astype(int)
        )

    # --------------------------------------------------------
    # Forward-fill LEVELS only
    # --------------------------------------------------------

    for col in [
        "vix",
        "us2y",
        "us10y"
    ]:

        merged[col] = (
            merged[col]
            .ffill()
        )

    # --------------------------------------------------------
    # Calculate Treasury changes AFTER forward-fill
    # --------------------------------------------------------

    merged["delta_us2y"] = (
        merged["us2y"]
        .diff()
    )

    merged["delta_us10y"] = (
        merged["us10y"]
        .diff()
    )

    # --------------------------------------------------------
    # Optional yield-curve spread
    # --------------------------------------------------------
    # We create it for inspection, but do NOT assume it belongs
    # in the final regression yet.

    merged["yield_curve_10y_2y"] = (
        merged["us10y"] -
        merged["us2y"]
    )

    # --------------------------------------------------------
    # Print missing values after forward-fill
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("MISSING VALUES AFTER FORWARD-FILL")
    print("=" * 80)

    print(
        merged.isna().sum()
    )

    # --------------------------------------------------------
    # Drop rows that genuinely cannot be used
    # --------------------------------------------------------

    before_len = len(merged)

    regression_df = merged.dropna(
        subset=[
            "btc_return_pct",
            "btc_abs_return_pct",
            "btc_vol_7d",
            "vix",
            "us2y",
            "us10y",
            "delta_us2y",
            "delta_us10y"
        ]
    ).copy()

    regression_df = (
        regression_df
        .reset_index(drop=True)
    )

    after_len = len(regression_df)

    # --------------------------------------------------------
    # Final sample information
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("FINAL FULL-CALENDAR REGRESSION SAMPLE")
    print("=" * 80)

    print(
        "Rows before final drop:",
        before_len
    )

    print(
        "Rows after final drop:",
        after_len
    )

    print(
        "Rows dropped:",
        before_len - after_len
    )

    print(
        "Start date:",
        regression_df["date"].min()
    )

    print(
        "End date:",
        regression_df["date"].max()
    )

    # --------------------------------------------------------
    # Count observed vs forward-filled Bloomberg values
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("BLOOMBERG OBSERVED VS FORWARD-FILLED")
    print("=" * 80)

    for col in [
        "vix",
        "us2y",
        "us10y"
    ]:

        observed_col = f"{col}_observed"

        n_observed = (
            regression_df[observed_col]
            .sum()
        )

        n_total = len(regression_df)

        n_forward_filled = (
            n_total - n_observed
        )

        print(
            f"{col}: "
            f"observed={n_observed}, "
            f"forward-filled={n_forward_filled}, "
            f"total={n_total}"
        )

    # --------------------------------------------------------
    # Summary statistics
    # --------------------------------------------------------

    variables_to_describe = [

        # Stablecoin deviations
        "usdt_abs_dev_pct",
        "usdc_abs_dev_pct",
        "dai_abs_dev_pct",

        # BTC stress
        "btc_return_pct",
        "btc_abs_return_pct",
        "btc_vol_7d",

        # Traditional stress
        "vix",

        # Treasury levels
        "us2y",
        "us10y",

        # Treasury daily changes
        "delta_us2y",
        "delta_us10y",

        # Yield curve
        "yield_curve_10y_2y"
    ]

    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    print(
        regression_df[
            variables_to_describe
        ]
        .describe()
        .round(4)
    )

    # --------------------------------------------------------
    # Preview March 2023 specifically
    # --------------------------------------------------------

    march_2023 = regression_df[
        (
            regression_df["date"] >=
            pd.Timestamp("2023-03-09")
        )
        &
        (
            regression_df["date"] <=
            pd.Timestamp("2023-03-14")
        )
    ]

    print("\n" + "=" * 80)
    print("MARCH 2023 CHECK")
    print("=" * 80)

    print(
        march_2023[
            [
                "date",
                "usdt_abs_dev_pct",
                "usdc_abs_dev_pct",
                "dai_abs_dev_pct",
                "vix",
                "vix_observed",
                "us2y",
                "us2y_observed",
                "us10y",
                "us10y_observed"
            ]
        ]
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    regression_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print("\n" + "=" * 80)
    print("SAVED SUCCESSFULLY")
    print("=" * 80)

    print(
        OUTPUT_PATH
    )

    return regression_df


# ============================================================
# MAIN
# ============================================================

def main():

    build_full_calendar_dataset()


if __name__ == "__main__":
    main()
