import pandas as pd
from pathlib import Path
from project_config import DATA_DIR, OUTPUT_DIR, load_price_data
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================================================
# LOAD DAILY PRICE DATA
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
path = DATA_DIR / "merged_prices.csv"
OUTPUT_PATH = OUTPUT_DIR / "march_2023_event_study.png"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

df = load_price_data(path)

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)


# ============================================================
# CREATE DEVIATION VARIABLES
# ============================================================

for coin in ["usdt", "usdc", "dai"]:
    df[f"{coin}_dev_pct"] = (df[coin] - 1) * 100


# ============================================================
# DEFINE MARCH 2023 EVENT WINDOW
# ============================================================

event_date = pd.Timestamp("2023-03-11")

start_date = event_date - pd.Timedelta(days=7)
end_date = event_date + pd.Timedelta(days=7)

event_df = df[
    (df["date"] >= start_date) &
    (df["date"] <= end_date)
].copy()

# Event time:
# March 11 = 0
# March 10 = -1
# March 12 = +1, etc.

event_df["event_day"] = (
    event_df["date"] - event_date
).dt.days


# ============================================================
# PRINT EVENT WINDOW
# ============================================================

print("\n" + "=" * 80)
print("MARCH 2023 EVENT WINDOW")
print("=" * 80)

print(
    event_df[
        [
            "date",
            "event_day",
            "usdt",
            "usdc",
            "dai",
            "usdt_dev_pct",
            "usdc_dev_pct",
            "dai_dev_pct"
        ]
    ].to_string(index=False)
)


# ============================================================
# PLOT DEVIATIONS
# ============================================================

plt.figure(figsize=(11, 6))

plt.plot(
    event_df["event_day"],
    event_df["usdt_dev_pct"],
    marker="o",
    label="USDT"
)

plt.plot(
    event_df["event_day"],
    event_df["usdc_dev_pct"],
    marker="o",
    label="USDC"
)

plt.plot(
    event_df["event_day"],
    event_df["dai_dev_pct"],
    marker="o",
    label="DAI"
)


# $1 peg
plt.axhline(
    0,
    linewidth=1
)

# ±0.5% depeg thresholds
plt.axhline(
    0.5,
    linestyle="--",
    linewidth=1,
    label="+0.5% threshold"
)

plt.axhline(
    -0.5,
    linestyle="--",
    linewidth=1,
    label="-0.5% threshold"
)

# Event date
plt.axvline(
    0,
    linestyle=":",
    linewidth=1.5,
    label="11 March 2023"
)


plt.xlabel("Days Relative to 11 March 2023")
plt.ylabel("Deviation from $1 Peg (%)")

plt.title(
    "Stablecoin Deviations Around the March 2023 Stress Event"
)

plt.legend()
plt.grid(alpha=0.2)

plt.tight_layout()
plt.savefig(OUTPUT_PATH, dpi=200)
plt.close()
