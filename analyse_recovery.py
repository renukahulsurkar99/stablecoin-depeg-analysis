import pandas as pd
from pathlib import Path
from project_config import DATA_DIR, OUTPUT_DIR, load_price_data
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================================================
# LOAD FINAL 2-DAY RECOVERY DATASET
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
path = OUTPUT_DIR / "episodes_confirmation_comparison.csv"
OUTPUT_PATH = OUTPUT_DIR / "severity_recovery_analysis.png"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)


df = pd.read_csv(path)

print("\nDataset:")
print(df.to_string(index=False))
# Make sure we are using ONLY the preferred 2-day specification
if "confirmation_days" in df.columns:
    df = df[df["confirmation_days"] == 2].copy()

print("Number of episodes:", len(df))
print("Confirmation rules:", df["confirmation_days"].unique())


# ============================================================
# RECOVERY TIME DESCRIPTIVE STATISTICS
# ============================================================

print("\n========================================")
print("RECOVERY TIME")
print("========================================")
print(
    df["recovery_time_days"].describe()
)


# ============================================================
# DEPEG SEVERITY DESCRIPTIVE STATISTICS
# ============================================================

print("\n========================================")
print("DEPEG SEVERITY")
print("========================================")

print(
    df["max_abs_deviation_pct"].describe()
)


# ============================================================
# SEVERITY VS RECOVERY CORRELATION
# ============================================================

correlation = df[
    "max_abs_deviation_pct"
].corr(
    df["recovery_time_days"]
)

print("\n========================================")
print("SEVERITY VS RECOVERY")
print("========================================")

print(
    "Correlation:",
    round(correlation, 3)
)


# ============================================================
# RECOVERY BY DIRECTION
# ============================================================

print("\n========================================")
print("RECOVERY BY DIRECTION")
print("========================================")

direction_stats = (
    df.groupby("direction")[
        "recovery_time_days"
    ]
    .agg([
        "count",
        "mean",
        "median",
        "std",
        "min",
        "max"
    ])
)

print(direction_stats)


# ============================================================
# SCATTER PLOT
# ============================================================

plt.figure(figsize=(9, 6))

plt.scatter(
    df["max_abs_deviation_pct"],
    df["recovery_time_days"]
)

# Label the four largest deviations to keep the chart readable.
# All episodes remain plotted; the accompanying CSV preserves every label.
for index, (_, row) in enumerate(
    df.nlargest(min(4, len(df)), "max_abs_deviation_pct").iterrows()
):
    plt.annotate(
        f'{row["coin"]} {row["start_date"]}',
        (row["max_abs_deviation_pct"], row["recovery_time_days"]),
        fontsize=8,
        xytext=(
            -8,
            14 if row["recovery_time_days"] <= 1 else -18 - (index % 2) * 16
        ),
        ha="right",
        textcoords="offset points"
    )

plt.xlabel("Maximum Absolute Deviation (%)")
plt.ylabel("Recovery Time (Days)")

plt.title(
    "Stablecoin Depeg Severity and Recovery Time"
)

plt.tight_layout()

plt.savefig(OUTPUT_PATH, dpi=200)
plt.close()

# ============================================================
# ROBUSTNESS CHECK:
# EXCLUDE DAI 10 NOVEMBER 2021
# ============================================================

df["start_date"] = pd.to_datetime(df["start_date"])

robust_df = df[
    ~(
        (df["coin"] == "DAI") &
        (df["start_date"] == pd.Timestamp("2021-11-10"))
    )
].copy()

print("\n========================================")
print("ROBUSTNESS: EXCLUDING DAI 10 NOV 2021")
print("========================================")

print("Number of episodes:", len(robust_df))

robust_corr = robust_df[
    "max_abs_deviation_pct"
].corr(
    robust_df["recovery_time_days"]
)

print(
    "Severity-recovery correlation:",
    round(robust_corr, 3)
)

print("\nRecovery by direction:")

print(
    robust_df.groupby("direction")[
        "recovery_time_days"
    ]
    .agg([
        "count",
        "mean",
        "median",
        "std",
        "min",
        "max"
    ])
)
