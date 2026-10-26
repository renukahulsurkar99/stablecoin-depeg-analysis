# Methodology and limitations

## Depeg and recovery definitions

A breach occurs when a daily stablecoin price is strictly below $0.995 or above $1.005. Values exactly on the boundaries remain inside the band. Percentage deviation is `(price - 1) * 100`; the absolute deviation is its magnitude.

An episode begins at a breach. Recovery is dated to the first return inside the band that is followed by the required number of consecutive in-band observations, counting that first return. The main recovery specification requires two days. A one-day return followed by a fresh breach therefore does not split a two-day-confirmation episode. The confirmation date is recorded separately from the recovery date.

Elapsed recovery time is the number of calendar days from the episode start to the recovery date. An episode without sufficient confirmation at the end of the sample is marked as censored, with recovery time left missing. Episode duration is the inclusive span from the first breach through the last breach and can include temporary in-band days. It is not necessarily a count of out-of-band observations.

Premium/discount classification follows the sign of the largest absolute deviation within the episode. An episode that changes direction is classified by that most extreme observation.

## Date exclusions and robustness

The episode analysis excludes episodes starting on 17 April 2021, which the dissertation code treats as a suspected simultaneous price-data anomaly. That interpretation is an explicit assumption, not an independently verified data correction. The exclusion is based on the start date rather than removal of that date from every analysis.

The main episode sample retains 10 November 2021. The recovery analysis separately reports sensitivity to excluding the DAI episode starting on that date. The correlation script includes additional combinations of April, November and March exclusions. The regression specifications retain their own defined samples and do not automatically inherit episode exclusions.

The older recovery implementation is not included because its recovery-date convention and exclusions differ from the preferred confirmation approach.

## Regression design

Each coin's absolute deviation is regressed separately on Bitcoin seven-day rolling log-return volatility, VIX and daily changes in two-year and ten-year Treasury yields. Bitcoin daily log returns are measured in percent. Treasury changes are percentage-point changes in the supplied percent-unit yields.

The baseline retains dates on which all three traditional market indicators are observed. The full-calendar comparison forward-fills their levels over non-observation dates. Yield changes are calculated after the levels are filled: a weekend with unchanged filled levels has zero daily yield change. Leading missing observations and the initial volatility warm-up are removed where required.

The model sets are:

1. Observed-market-day baseline using BTC volatility.
2. Full-calendar sample using BTC volatility and forward-filled levels.
3. Baseline replacing BTC volatility with absolute daily BTC return.
4. Baseline excluding 10–14 March 2023.
5. Full-calendar sample excluding 10–14 March 2023.

All three coins are fitted under each specification, giving 15 models. Inference uses HAC/Newey–West standard errors with seven observation lags. In the observed-day sample, lags refer to retained observations, not seven calendar days. Predictor correlations and variance inflation factors are exported as diagnostics.

## Interpretation limits

- These are contemporaneous associations, without an identification strategy for causation or an out-of-sample forecasting evaluation.
- Daily observations cannot resolve intraday extremes or the exact time of recovery.
- Several coin-level episodes share the same market shock and are not independent market events.
- Small stress and recovery samples make estimates sensitive to individual observations and exclusion choices.
- Ordinary R-squared is modest in the supplied baseline results. Significant coefficients should not be presented as strong predictive performance.
- Forward-filled market indicators represent the last available reading, rather than newly observed weekend conditions.
- The event-window chart is descriptive. It does not estimate abnormal returns or a causal event effect.
- Bitcoin returns calculated from three days before to three days after an episode use future information. They are descriptive event measures, not predictors available at episode onset.
- Input validation checks structure and completeness. It cannot establish source accuracy or data-sharing rights.
