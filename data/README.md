# Local data inputs

The repository contains analysis code and synthetic tests. It does not distribute the dissertation's source datasets or generated research tables.

## Cryptocurrency prices

Supply `merged_prices.csv` in this directory, or pass its directory to `run_analysis.py --data-dir`.

| Column | Definition |
| --- | --- |
| `date` | Daily date in `YYYY-MM-DD` format |
| `usdt` | USDT price in US dollars |
| `usdc` | USDC price in US dollars |
| `dai` | DAI price in US dollars |
| `bitcoin` | Bitcoin price in US dollars |

The supplied dissertation input covers 1 January 2021–9 August 2026. Prices must be numeric, finite, positive and non-missing. Dates must be unique and consecutive with one observation per calendar day. Rows are sorted before analysis.

These validations prevent a missing observation from being treated as a return inside the peg band, or separated calendar dates from being counted as consecutive confirmation days. They do not verify whether the provider's prices accurately represent the market.

The provider, retrieval method, observation timezone and precise daily price convention were not documented in the supplied code. Do not assume that these are intraday minima or exchange-specific prices. To reproduce the original research, use the original authorised input. A replacement source needs its own provenance and can produce different results.

Record the provider, ticker identifiers, retrieval date, timezone, daily price convention, cleaning/merge steps and permitted uses with any replacement data. The code does not download or merge provider-specific feeds.

## Traditional market indicators

The complete regression workflow additionally expects `BloombergDataValues.xlsx` with three sheets:

| Sheet | Columns, without a header row | Units |
| --- | --- | --- |
| `VIX_raw` | Date, VIX level | Index points |
| `US2Y_raw` | Date, US two-year Treasury yield | Percent, e.g. `4.20` |
| `US10Y_raw` | Date, US ten-year Treasury yield | Percent, e.g. `4.30` |

Each sheet should contain unique daily observations for its market series. Include the original observation dates, leaving weekends and holidays absent rather than fabricating observations. The preparation script merges these onto the crypto calendar, records observed-value flags and forward-fills levels. Treasury changes are then calculated by differencing those filled levels.

The filename identifies the original Bloomberg export format. Obtain and use this data only through an authorised source. Public-sharing permissions for the supplied workbook have not been established. The enriched regression dataset also embeds those observations and is therefore kept out of the repository.

If replacing these series with a different source, document the change, ensure the formats and units agree, and treat the outputs as a new replication rather than identical original results.

## Generated outputs

With valid local inputs, the scripts create:

- `episodes_confirmation_comparison.csv`: one-day and two-day episode specifications.
- `recovery_dataset_2day.csv`: the preferred recovery specification.
- `severity_recovery_analysis.png`: recovery versus severity.
- `march_2023_event_study.png`: daily deviations around 11 March 2023.
- `regression_dataset_full_calendar.csv`: aligned features and market observations.
- `regression_results/`: detailed coefficients, concise comparison, model summaries, predictor correlations and VIF diagnostics.

Correlation-analysis tables and model summaries are also printed to the console. Generated files are ignored by Git. Review source-data publication terms before sharing results outside your local environment.
