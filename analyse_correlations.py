import pandas as pd
from pathlib import Path
from project_config import DATA_DIR, OUTPUT_DIR, load_price_data

# ============================================================
# LOAD DATA
# ============================================================

path = DATA_DIR / "merged_prices.csv"

df = load_price_data(path)

df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date").reset_index(drop=True)


# ============================================================
# CREATE DAILY DEVIATIONS (%)
# ============================================================

for coin in ["usdt", "usdc", "dai"]:
    df[f"{coin}_dev_pct"] = (df[coin] - 1) * 100


# ============================================================
# FULL-SAMPLE CORRELATION
# ============================================================

dev_cols = [
    "usdt_dev_pct",
    "usdc_dev_pct",
    "dai_dev_pct"
]

correlation_matrix = df[dev_cols].corr()

print("\n" + "=" * 60)
print("FULL-SAMPLE STABLECOIN DEVIATION CORRELATIONS")
print("=" * 60)

print(correlation_matrix.round(3))

# ============================================================
# DEFINE STRESS AND NORMAL DAYS
# ============================================================

threshold = 0.5  # deviations are already expressed in percentage points

df["stress_day"] = (
    (df["usdt_dev_pct"].abs() > threshold) |
    (df["usdc_dev_pct"].abs() > threshold) |
    (df["dai_dev_pct"].abs() > threshold)
)

normal_df = df[~df["stress_day"]].copy()
stress_df = df[df["stress_day"]].copy()


# ============================================================
# NUMBER OF NORMAL AND STRESS DAYS
# ============================================================

print("\n" + "=" * 60)
print("NUMBER OF OBSERVATIONS")
print("=" * 60)

print("Normal days:", len(normal_df))
print("Stress days:", len(stress_df))


# ============================================================
# NORMAL-PERIOD CORRELATIONS
# ============================================================

print("\n" + "=" * 60)
print("NORMAL-PERIOD CORRELATIONS")
print("=" * 60)

normal_corr = normal_df[dev_cols].corr()

print(normal_corr.round(3))


# ============================================================
# STRESS-PERIOD CORRELATIONS
# ============================================================

print("\n" + "=" * 60)
print("STRESS-PERIOD CORRELATIONS")
print("=" * 60)

stress_corr = stress_df[dev_cols].corr()

print(stress_corr.round(3))


# ============================================================
# CHANGE IN CORRELATION
# ============================================================

print("\n" + "=" * 60)
print("CHANGE IN CORRELATION: STRESS - NORMAL")
print("=" * 60)

change_corr = stress_corr - normal_corr

print(change_corr.round(3))

print("\n" + "=" * 80)
print("ALL STRESS DAYS")
print("=" * 80)

stress_table = stress_df[
    [
        "date",
        "usdt_dev_pct",
        "usdc_dev_pct",
        "dai_dev_pct"
    ]
].copy()

print(stress_table.to_string(index=False))

threshold = 0.5

stress_table["USDT_breach"] = (
    stress_table["usdt_dev_pct"].abs() > threshold
)

stress_table["USDC_breach"] = (
    stress_table["usdc_dev_pct"].abs() > threshold
)

stress_table["DAI_breach"] = (
    stress_table["dai_dev_pct"].abs() > threshold
)

print("\n" + "=" * 80)
print("STRESS DAYS AND BREACHING COINS")
print("=" * 80)

print(stress_table.to_string(index=False))

# ============================================================
# ROBUSTNESS TESTS FOR STRESS CORRELATIONS
# ============================================================

print("\n" + "=" * 80)
print("ROBUSTNESS TESTS: STRESS CORRELATIONS")
print("=" * 80)


# ------------------------------------------------------------
# BASELINE
# ------------------------------------------------------------

baseline_corr = stress_df[dev_cols].corr()

print("\nBASELINE: ALL STRESS DAYS")
print("N =", len(stress_df))
print(baseline_corr.round(3))


# ------------------------------------------------------------
# ROBUSTNESS 1:
# EXCLUDE 17 APRIL 2021
# ------------------------------------------------------------

stress_excl_april = stress_df[
    stress_df["date"] != pd.Timestamp("2021-04-17")
].copy()

corr_excl_april = stress_excl_april[dev_cols].corr()

print("\nEXCLUDING 17 APRIL 2021")
print("N =", len(stress_excl_april))
print(corr_excl_april.round(3))


# ------------------------------------------------------------
# ROBUSTNESS 2:
# EXCLUDE 17 APRIL 2021 AND 10 NOVEMBER 2021
# ------------------------------------------------------------

excluded_dates = [
    pd.Timestamp("2021-04-17"),
    pd.Timestamp("2021-11-10")
]

stress_excl_both = stress_df[
    ~stress_df["date"].isin(excluded_dates)
].copy()

corr_excl_both = stress_excl_both[dev_cols].corr()

print("\nEXCLUDING 17 APRIL AND 10 NOVEMBER 2021")
print("N =", len(stress_excl_both))
print(corr_excl_both.round(3))


# ------------------------------------------------------------
# USDC-DAI COMPARISON
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("USDC-DAI CORRELATION COMPARISON")
print("=" * 80)

print(
    "Normal period:",
    round(normal_corr.loc["usdc_dev_pct", "dai_dev_pct"], 3)
)

print(
    "All stress days:",
    round(baseline_corr.loc["usdc_dev_pct", "dai_dev_pct"], 3)
)

print(
    "Stress excluding 17 April:",
    round(corr_excl_april.loc["usdc_dev_pct", "dai_dev_pct"], 3)
)

print(
    "Stress excluding 17 April + 10 November:",
    round(corr_excl_both.loc["usdc_dev_pct", "dai_dev_pct"], 3)
)

# ============================================================
# ROBUSTNESS: EXCLUDE MARCH 2023 STRESS EVENT
# ============================================================

march_event_dates = [
    pd.Timestamp("2023-03-11"),
    pd.Timestamp("2023-03-12")
]

stress_no_march = stress_df[
    ~stress_df["date"].isin(march_event_dates)
].copy()

corr_no_march = stress_no_march[dev_cols].corr()

print("\n" + "=" * 80)
print("ROBUSTNESS: EXCLUDING MARCH 11-12, 2023")
print("=" * 80)

print("N =", len(stress_no_march))
print(corr_no_march.round(3))


# ============================================================
# ROBUSTNESS: EXCLUDE APRIL 17 + MARCH 2023
# ============================================================

exclude_dates = [
    pd.Timestamp("2021-04-17"),
    pd.Timestamp("2023-03-11"),
    pd.Timestamp("2023-03-12")
]

stress_no_april_march = stress_df[
    ~stress_df["date"].isin(exclude_dates)
].copy()

corr_no_april_march = stress_no_april_march[dev_cols].corr()

print("\n" + "=" * 80)
print("EXCLUDING APRIL 17, 2021 + MARCH 11-12, 2023")
print("=" * 80)

print("N =", len(stress_no_april_march))
print(corr_no_april_march.round(3))


# ============================================================
# USDC-DAI SUMMARY
# ============================================================

print("\n" + "=" * 80)
print("USDC-DAI ROBUSTNESS SUMMARY")
print("=" * 80)

print(
    "Normal period:",
    round(normal_corr.loc["usdc_dev_pct", "dai_dev_pct"], 3)
)

print(
    "All stress days:",
    round(baseline_corr.loc["usdc_dev_pct", "dai_dev_pct"], 3)
)

print(
    "Stress excluding April 17:",
    round(corr_excl_april.loc["usdc_dev_pct", "dai_dev_pct"], 3)
)

print(
    "Stress excluding March 2023:",
    round(corr_no_march.loc["usdc_dev_pct", "dai_dev_pct"], 3)
)

print(
    "Stress excluding April 17 + March 2023:",
    round(
        corr_no_april_march.loc[
            "usdc_dev_pct",
            "dai_dev_pct"
        ],
        3
    )
)
