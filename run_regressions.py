"""
FINAL STABLECOIN STRESS REGRESSION ANALYSIS
===========================================

Research question:
Are stablecoin deviations from the $1 peg associated with
crypto-market and traditional financial-market stress?

Dependent variables:
    usdt_abs_dev_pct
    usdc_abs_dev_pct
    dai_abs_dev_pct

Primary predictors:
    btc_vol_7d
    vix
    delta_us2y
    delta_us10y

Main specification:
    Business-day baseline:
    only dates where VIX, US2Y and US10Y were genuinely observed.

Robustness:
    1. Full-calendar sample using forward-filled Bloomberg levels.
    2. Replace BTC volatility with absolute BTC daily return.
    3. Exclude the March 2023 SVB stress window.

Inference:
    OLS coefficients with HAC / Newey-West standard errors,
    maxlags = 7.

Outputs:
    - predictor_correlation_matrix.csv
    - vif_diagnostics.csv
    - regression_results_all.csv
    - model_summary_all.csv

"""

import pandas as pd
import numpy as np
from pathlib import Path
from project_config import DATA_DIR, OUTPUT_DIR, load_price_data

import statsmodels.api as sm

from statsmodels.stats.outliers_influence import (
    variance_inflation_factor
)


# ============================================================
# FILE PATHS
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = OUTPUT_DIR / "regression_dataset_full_calendar.csv"
OUTPUT_FOLDER = OUTPUT_DIR / "regression_results"

OUTPUT_FOLDER.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SETTINGS
# ============================================================

DEPENDENT_VARIABLES = {
    "USDT": "usdt_abs_dev_pct",
    "USDC": "usdc_abs_dev_pct",
    "DAI": "dai_abs_dev_pct"
}

MAIN_PREDICTORS = [
    "btc_vol_7d",
    "vix",
    "delta_us2y",
    "delta_us10y"
]

BTC_ABS_RETURN_PREDICTORS = [
    "btc_abs_return_pct",
    "vix",
    "delta_us2y",
    "delta_us10y"
]

HAC_LAGS = 7


# SVB stress window
SVB_START = pd.Timestamp("2023-03-10")
SVB_END = pd.Timestamp("2023-03-14")


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    df = pd.read_csv(DATA_PATH)

    df["date"] = pd.to_datetime(
        df["date"]
    )

    df = (
        df.sort_values("date")
          .reset_index(drop=True)
    )

    return df


# ============================================================
# CREATE BUSINESS-DAY BASELINE
# ============================================================

def create_baseline_sample(df):

    baseline = df[
        (df["vix_observed"] == 1) &
        (df["us2y_observed"] == 1) &
        (df["us10y_observed"] == 1)
    ].copy()

    baseline = baseline.dropna(
        subset=
        list(DEPENDENT_VARIABLES.values())
        + MAIN_PREDICTORS
        + ["btc_abs_return_pct"]
    )

    baseline = (
        baseline
        .sort_values("date")
        .reset_index(drop=True)
    )

    return baseline


# ============================================================
# CORRELATION MATRIX
# ============================================================

def run_correlation_analysis(df):

    variables = [
        "btc_vol_7d",
        "btc_abs_return_pct",
        "vix",
        "delta_us2y",
        "delta_us10y"
    ]

    corr = (
        df[variables]
        .corr()
        .round(3)
    )

    print("\n" + "=" * 90)
    print("PREDICTOR CORRELATION MATRIX")
    print("=" * 90)

    print(corr)

    corr.to_csv(
        OUTPUT_FOLDER /
        "predictor_correlation_matrix.csv"
    )

    return corr


# ============================================================
# VIF
# ============================================================

def calculate_vif(df, predictors):

    X = df[predictors].dropna().copy()

    # Add constant
    X_const = sm.add_constant(X)

    vif_rows = []

    for i, column in enumerate(X_const.columns):

        if column == "const":
            continue

        vif_value = variance_inflation_factor(
            X_const.values,
            i
        )

        vif_rows.append({
            "variable": column,
            "VIF": vif_value
        })

    vif_df = pd.DataFrame(vif_rows)

    print("\n" + "=" * 90)
    print("VIF DIAGNOSTICS")
    print("=" * 90)

    print(
        vif_df
        .round(3)
        .to_string(index=False)
    )

    vif_df.to_csv(
        OUTPUT_FOLDER /
        "vif_diagnostics.csv",
        index=False
    )

    return vif_df


# ============================================================
# RUN ONE REGRESSION
# ============================================================

def run_model(
    df,
    dependent,
    predictors,
    coin,
    specification
):

    model_df = df[
        [dependent] +
        predictors
    ].dropna().copy()

    y = model_df[dependent]

    X = model_df[predictors]

    X = sm.add_constant(X)

    model = sm.OLS(
        y,
        X
    )

    results = model.fit(
        cov_type="HAC",
        cov_kwds={
            "maxlags": HAC_LAGS
        }
    )

    coefficient_rows = []

    conf_int = results.conf_int()

    for variable in results.params.index:

        coefficient_rows.append({

            "coin": coin,
            "specification": specification,

            "dependent_variable":
                dependent,

            "variable":
                variable,

            "coefficient":
                results.params[variable],

            "hac_std_error":
                results.bse[variable],

            "t_stat":
                results.tvalues[variable],

            "p_value":
                results.pvalues[variable],

            "ci_lower":
                conf_int.loc[variable, 0],

            "ci_upper":
                conf_int.loc[variable, 1],

            "n_obs":
                int(results.nobs),

            "r_squared":
                results.rsquared,

            "adj_r_squared":
                results.rsquared_adj
        })

    coefficient_df = pd.DataFrame(
        coefficient_rows
    )

    model_summary = {
        "coin": coin,
        "specification": specification,
        "dependent_variable": dependent,
        "n_obs": int(results.nobs),
        "r_squared": results.rsquared,
        "adj_r_squared": results.rsquared_adj,
        "aic": results.aic,
        "bic": results.bic
    }

    return (
        results,
        coefficient_df,
        model_summary
    )


# ============================================================
# PRINT MODEL
# ============================================================

def print_model_results(
    results,
    coin,
    specification
):

    print("\n" + "=" * 90)

    print(
        f"{coin} — {specification}"
    )

    print("=" * 90)

    print(results.summary())


# ============================================================
# RUN MODEL SET
# ============================================================

def run_model_set(
    df,
    predictors,
    specification
):

    coefficient_tables = []
    summary_rows = []

    for coin, dependent in (
        DEPENDENT_VARIABLES.items()
    ):

        results, coef_df, model_summary = (
            run_model(
                df=df,
                dependent=dependent,
                predictors=predictors,
                coin=coin,
                specification=specification
            )
        )

        print_model_results(
            results,
            coin,
            specification
        )

        coefficient_tables.append(
            coef_df
        )

        summary_rows.append(
            model_summary
        )

    coefficients = pd.concat(
        coefficient_tables,
        ignore_index=True
    )

    summary_df = pd.DataFrame(
        summary_rows
    )

    return coefficients, summary_df


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_data()

    baseline_df = create_baseline_sample(
        df
    )

    full_calendar_df = df.copy()

    # --------------------------------------------------------
    # Sample information
    # --------------------------------------------------------

    print("\n" + "=" * 90)
    print("SAMPLE INFORMATION")
    print("=" * 90)

    print(
        "Full-calendar observations:",
        len(full_calendar_df)
    )

    print(
        "Business-day baseline observations:",
        len(baseline_df)
    )

    print(
        "Baseline start:",
        baseline_df["date"].min()
    )

    print(
        "Baseline end:",
        baseline_df["date"].max()
    )

    # --------------------------------------------------------
    # Diagnostics on baseline
    # --------------------------------------------------------

    run_correlation_analysis(
        baseline_df
    )

    calculate_vif(
        baseline_df,
        MAIN_PREDICTORS
    )

    # ========================================================
    # MODEL 1
    # BASELINE BUSINESS-DAY MODEL
    # ========================================================

    baseline_coef, baseline_summary = (
        run_model_set(
            df=baseline_df,
            predictors=MAIN_PREDICTORS,
            specification=(
                "Baseline business-day "
                "BTC volatility"
            )
        )
    )

    # ========================================================
    # MODEL 2
    # FULL CALENDAR ROBUSTNESS
    # ========================================================

    full_coef, full_summary = (
        run_model_set(
            df=full_calendar_df,
            predictors=MAIN_PREDICTORS,
            specification=(
                "Full-calendar forward-filled "
                "BTC volatility"
            )
        )
    )

    # ========================================================
    # MODEL 3
    # BTC ABSOLUTE RETURN ROBUSTNESS
    # ========================================================

    absret_coef, absret_summary = (
        run_model_set(
            df=baseline_df,
            predictors=BTC_ABS_RETURN_PREDICTORS,
            specification=(
                "Baseline business-day "
                "BTC absolute return"
            )
        )
    )

    # ========================================================
    # MODEL 4
    # EXCLUDE SVB WINDOW
    # ========================================================

    baseline_no_svb = baseline_df[
        ~(
            (baseline_df["date"] >= SVB_START)
            &
            (baseline_df["date"] <= SVB_END)
        )
    ].copy()

    print("\n" + "=" * 90)
    print("SVB EXCLUSION ROBUSTNESS")
    print("=" * 90)

    print(
        "Baseline N:",
        len(baseline_df)
    )

    print(
        "N after excluding "
        "10–14 March 2023:",
        len(baseline_no_svb)
    )

    nosvb_coef, nosvb_summary = (
        run_model_set(
            df=baseline_no_svb,
            predictors=MAIN_PREDICTORS,
            specification=(
                "Baseline excluding "
                "SVB window"
            )
        )
    )

    # ========================================================
    # MODEL 5
    # FULL CALENDAR EXCLUDING SVB
    # ========================================================

    full_no_svb = full_calendar_df[
        ~(
            (full_calendar_df["date"] >= SVB_START)
            &
            (full_calendar_df["date"] <= SVB_END)
        )
    ].copy()

    full_nosvb_coef, full_nosvb_summary = (
        run_model_set(
            df=full_no_svb,
            predictors=MAIN_PREDICTORS,
            specification=(
                "Full-calendar excluding "
                "SVB window"
            )
        )
    )

    # ========================================================
    # COMBINE COEFFICIENT TABLES
    # ========================================================

    all_coefficients = pd.concat(
        [
            baseline_coef,
            full_coef,
            absret_coef,
            nosvb_coef,
            full_nosvb_coef
        ],
        ignore_index=True
    )

    all_summaries = pd.concat(
        [
            baseline_summary,
            full_summary,
            absret_summary,
            nosvb_summary,
            full_nosvb_summary
        ],
        ignore_index=True
    )

    # --------------------------------------------------------
    # Round display copy
    # --------------------------------------------------------

    display_coefficients = (
        all_coefficients.copy()
    )

    numeric_columns = [
        "coefficient",
        "hac_std_error",
        "t_stat",
        "p_value",
        "ci_lower",
        "ci_upper",
        "r_squared",
        "adj_r_squared"
    ]

    display_coefficients[
        numeric_columns
    ] = (
        display_coefficients[
            numeric_columns
        ]
        .round(5)
    )

    # --------------------------------------------------------
    # Print concise coefficient comparison
    # --------------------------------------------------------

    print("\n" + "=" * 90)
    print("FINAL COEFFICIENT COMPARISON")
    print("=" * 90)

    comparison = display_coefficients[
        display_coefficients["variable"] !=
        "const"
    ][
        [
            "coin",
            "specification",
            "variable",
            "coefficient",
            "hac_std_error",
            "p_value",
            "adj_r_squared",
            "n_obs"
        ]
    ]

    print(
        comparison.to_string(index=False)
    )

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    all_coefficients.to_csv(
        OUTPUT_FOLDER /
        "regression_results_all.csv",
        index=False
    )

    all_summaries.to_csv(
        OUTPUT_FOLDER /
        "model_summary_all.csv",
        index=False
    )

    comparison.to_csv(
        OUTPUT_FOLDER /
        "regression_results_concise.csv",
        index=False
    )

    print("\n" + "=" * 90)
    print("FILES SAVED")
    print("=" * 90)

    print(
        OUTPUT_FOLDER /
        "regression_results_all.csv"
    )

    print(
        OUTPUT_FOLDER /
        "model_summary_all.csv"
    )

    print(
        OUTPUT_FOLDER /
        "regression_results_concise.csv"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
