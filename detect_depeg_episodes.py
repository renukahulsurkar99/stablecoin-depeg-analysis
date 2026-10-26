"""
Stablecoin Recovery Dataset
---------------------------

Purpose:
    Identify stablecoin depeg episodes and calculate recovery dynamics
    under both 1-day and 2-day confirmation rules.

Main depeg band:
    0.995 <= price <= 1.005   (±0.5%)

Main recovery definition:
    Recovery begins on the first day the stablecoin returns inside
    the peg band, provided it remains inside the band for the required
    number of consecutive confirmation days.

Outputs:
    1. episodes_confirmation_comparison.csv
       - contains both 1-day and 2-day specifications

    2. recovery_dataset_2day.csv
       - contains the preferred 2-day confirmation specification

Important:
    April 17, 2021 is excluded as a suspected data-quality / thin-liquidity
    observation.

    November 10, 2021 is RETAINED in the main sample.
"""

import pandas as pd
from pathlib import Path
from project_config import DATA_DIR, OUTPUT_DIR, load_price_data


# ============================================================
# SETTINGS
# ============================================================

COINS = ["usdt", "usdc", "dai"]

# Preliminary depeg band: ±0.5%
LOWER = 0.995
UPPER = 1.005

# Local inputs and outputs
PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = DATA_DIR / "merged_prices.csv"
OUTPUT_FOLDER = OUTPUT_DIR
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Exclude only April 17, 2021 for now
EXCLUDED_DATES = {
    pd.Timestamp("2021-04-17"):
        "Simultaneous single-day spike across USDT, USDC and DAI; "
        "suspected thin-liquidity/data-quality observation."
}

# Confirmation rules to compare
CONFIRMATION_RULES = [1, 2]


# ============================================================
# LOAD DATA
# ============================================================

def load_data(path=DATA_PATH):

    df = load_price_data(path)

    df["date"] = pd.to_datetime(df["date"])

    df = (
        df.sort_values("date")
          .reset_index(drop=True)
    )

    return df


# ============================================================
# DEPEG FLAG
# ============================================================

def create_depeg_flag(df, coin):

    """
    True if stablecoin price is outside the chosen peg band.
    """

    return (
        (df[coin] < LOWER) |
        (df[coin] > UPPER)
    )


# ============================================================
# FIND EPISODES WITH CONFIRMATION BUILT IN
# ============================================================

def find_episodes_confirmed(df, coin, confirmation_days):

    """
    Identifies depeg episodes in a single pass.

    An episode begins when price moves outside the peg band.

    It ends only when price returns inside the band AND remains
    inside for confirmation_days consecutive observations.

    A temporary one-day rebound therefore does not automatically
    split one depeg into two episodes.
    """

    flag = create_depeg_flag(df, coin)

    episodes = []

    n = len(df)

    in_episode = False
    start_idx = None
    last_bad_idx = None

    i = 0

    while i < n:

        # ----------------------------------------------------
        # NOT CURRENTLY IN AN EPISODE
        # ----------------------------------------------------

        if not in_episode:

            if flag.iloc[i]:

                in_episode = True
                start_idx = i
                last_bad_idx = i

            i += 1
            continue

        # ----------------------------------------------------
        # CURRENTLY IN AN EPISODE
        # ----------------------------------------------------

        if flag.iloc[i]:

            # Still outside band
            last_bad_idx = i

            i += 1
            continue

        # ----------------------------------------------------
        # PRICE IS INSIDE BAND
        # ----------------------------------------------------

        # Check whether there are enough observations remaining
        confirmation_end_idx = i + confirmation_days - 1

        if confirmation_end_idx >= n:

            # Cannot verify sustained recovery before sample ends
            break

        confirmation_window = flag.iloc[
            i:confirmation_end_idx + 1
        ]

        # If ANY day in confirmation window breaches again,
        # recovery is not yet confirmed
        if confirmation_window.any():

            i += 1
            continue

        # ----------------------------------------------------
        # CONFIRMED RECOVERY
        # ----------------------------------------------------

        recovery_idx = i

        episodes.append({
            "start_idx": start_idx,
            "last_bad_idx": last_bad_idx,
            "recovery_idx": recovery_idx,
            "confirmation_idx": confirmation_end_idx,
            "censored": False
        })

        # Reset
        in_episode = False
        start_idx = None
        last_bad_idx = None

        # Move beyond first recovery observation
        i += 1

    # --------------------------------------------------------
    # HANDLE CENSORED EPISODE
    # --------------------------------------------------------

    if in_episode:

        episodes.append({
            "start_idx": start_idx,
            "last_bad_idx": (
                last_bad_idx
                if last_bad_idx is not None
                else n - 1
            ),
            "recovery_idx": None,
            "confirmation_idx": None,
            "censored": True
        })

    return episodes


# ============================================================
# CALCULATE EPISODE CHARACTERISTICS
# ============================================================

def build_episode_rows(df, coin, confirmation_days):

    episodes = find_episodes_confirmed(
        df=df,
        coin=coin,
        confirmation_days=confirmation_days
    )

    rows = []

    for ep in episodes:

        start_idx = ep["start_idx"]
        last_bad_idx = ep["last_bad_idx"]

        start_date = df["date"].iloc[start_idx]

        # ----------------------------------------------------
        # EXCLUDE SUSPECTED ARTIFACT
        # ----------------------------------------------------

        if start_date in EXCLUDED_DATES:
            continue

        last_depeg_date = df["date"].iloc[last_bad_idx]

        # ----------------------------------------------------
        # EPISODE DURATION
        # ----------------------------------------------------

        # Number of calendar days spent in the depeg episode,
        # inclusive of start and final breach day
        episode_duration_days = (
            last_depeg_date - start_date
        ).days + 1

        # ----------------------------------------------------
        # MAXIMUM DEVIATION
        # ----------------------------------------------------

        episode_prices = df[coin].iloc[
            start_idx:last_bad_idx + 1
        ]

        deviations = episode_prices - 1.0

        max_dev_idx = deviations.abs().idxmax()

        max_deviation = deviations.loc[max_dev_idx]

        max_deviation_date = df.loc[
            max_dev_idx,
            "date"
        ]

        direction = (
            "Discount"
            if max_deviation < 0
            else "Premium"
        )

        # ----------------------------------------------------
        # RECOVERY INFORMATION
        # ----------------------------------------------------

        if ep["recovery_idx"] is not None:

            recovery_date = df["date"].iloc[
                ep["recovery_idx"]
            ]

            confirmation_date = df["date"].iloc[
                ep["confirmation_idx"]
            ]

            # ELAPSED TIME from depeg start to first sustained
            # return inside band
            recovery_time_days = (
                recovery_date - start_date
            ).days

        else:

            recovery_date = None
            confirmation_date = None
            recovery_time_days = None

        # ----------------------------------------------------
        # BITCOIN VARIABLES AROUND EVENT
        # ----------------------------------------------------

        btc_price_start = df["bitcoin"].iloc[start_idx]

        btc_return_1d = None

        if start_idx > 0:

            btc_prev = df["bitcoin"].iloc[start_idx - 1]

            if pd.notna(btc_prev) and btc_prev != 0:

                btc_return_1d = (
                    btc_price_start - btc_prev
                ) / btc_prev

        # 3-day return before → 3 days after event start
        lo = max(0, start_idx - 3)
        hi = min(len(df) - 1, start_idx + 3)

        btc_before = df["bitcoin"].iloc[lo]
        btc_after = df["bitcoin"].iloc[hi]

        btc_return_around = None

        if (
            pd.notna(btc_before)
            and pd.notna(btc_after)
            and btc_before != 0
        ):
            btc_return_around = (
                btc_after - btc_before
            ) / btc_before

        # ----------------------------------------------------
        # BUILD ROW
        # ----------------------------------------------------

        rows.append({

            "coin": coin.upper(),

            "confirmation_days": confirmation_days,

            "start_date": start_date.date(),

            "last_depeg_date":
                last_depeg_date.date(),

            "episode_duration_days":
                episode_duration_days,

            "recovery_date":
                recovery_date.date()
                if recovery_date is not None
                else None,

            "recovery_time_days":
                recovery_time_days,

            "confirmation_date":
                confirmation_date.date()
                if confirmation_date is not None
                else None,

            "max_deviation_pct":
                round(max_deviation * 100, 3),

            "max_abs_deviation_pct":
                round(abs(max_deviation) * 100, 3),

            "max_deviation_date":
                max_deviation_date.date(),

            "direction":
                direction,

            "btc_return_1d_pct":
                round(btc_return_1d * 100, 2)
                if btc_return_1d is not None
                else None,

            "btc_return_around_event_pct":
                round(btc_return_around * 100, 2)
                if btc_return_around is not None
                else None,

            "censored":
                ep["censored"]
        })

    return rows


# ============================================================
# BUILD FULL COMPARISON DATASET
# ============================================================

def build_comparison_dataset(df):

    all_rows = []

    for confirmation_days in CONFIRMATION_RULES:

        for coin in COINS:

            rows = build_episode_rows(
                df=df,
                coin=coin,
                confirmation_days=confirmation_days
            )

            all_rows.extend(rows)

    result = pd.DataFrame(all_rows)

    if not result.empty:

        result = (
            result.sort_values(
                [
                    "confirmation_days",
                    "coin",
                    "start_date"
                ]
            )
            .reset_index(drop=True)
        )

    return result


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_summary(result):

    print("\n" + "=" * 90)
    print("RECOVERY DATASET")
    print("=" * 90)

    print(
        result.to_string(index=False)
    )

    print("\n" + "=" * 90)
    print("EPISODE COUNTS")
    print("=" * 90)

    print(
        result.groupby(
            ["confirmation_days", "coin"]
        ).size()
    )

    print("\n" + "=" * 90)
    print("RECOVERY TIME SUMMARY")
    print("=" * 90)

    print(
        result.groupby(
            "confirmation_days"
        )["recovery_time_days"].describe()
    )

    print("\n" + "=" * 90)
    print("RECOVERY BY DIRECTION")
    print("=" * 90)

    print(
        result.groupby(
            ["confirmation_days", "direction"]
        )["recovery_time_days"].agg(
            ["count", "mean", "median", "min", "max"]
        )
    )

    print("\n" + "=" * 90)
    print("CENSORED EPISODES")
    print("=" * 90)

    print(
        result.groupby(
            "confirmation_days"
        )["censored"].sum()
    )


# ============================================================
# MAIN
# ============================================================

def main():

    df = load_data()

    result = build_comparison_dataset(df)

    print_summary(result)

    # --------------------------------------------------------
    # SAVE FULL 1-DAY VS 2-DAY COMPARISON
    # --------------------------------------------------------

    comparison_path = (
        OUTPUT_FOLDER /
        "episodes_confirmation_comparison.csv"
    )

    result.to_csv(
        comparison_path,
        index=False
    )

    print(
        f"\nSaved comparison dataset to:\n"
        f"{comparison_path}"
    )

    # --------------------------------------------------------
    # SAVE PREFERRED 2-DAY SPECIFICATION
    # --------------------------------------------------------

    recovery_2day = (
        result[
            result["confirmation_days"] == 2
        ]
        .copy()
        .reset_index(drop=True)
    )

    recovery_2day_path = (
        OUTPUT_FOLDER /
        "recovery_dataset_2day.csv"
    )

    recovery_2day.to_csv(
        recovery_2day_path,
        index=False
    )

    print(
        f"\nSaved preferred 2-day recovery dataset to:\n"
        f"{recovery_2day_path}"
    )

    print("\n" + "=" * 90)
    print("METHODOLOGY SETTINGS")
    print("=" * 90)

    print(
        f"Peg band: {LOWER} to {UPPER}"
    )

    print(
        f"Confirmation rules tested: "
        f"{CONFIRMATION_RULES}"
    )

    print(
        f"Excluded dates: "
        f"{list(EXCLUDED_DATES.keys())}"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()

##CONFIRMED and FREEZED ALGORITHM
