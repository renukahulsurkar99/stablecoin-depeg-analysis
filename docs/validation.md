# Validation

The publication version was checked on 26 October 2026 using Python 3.13 and the versions in `requirements.txt`.

## Automated checks

Run from the repository root:

```bash
python -m unittest discover -s tests -v
```

All ten tests pass. Test prices are synthetic and contain no source-data extracts.

## Full local reproduction

All six analysis scripts completed through `run_analysis.py` using the original dissertation inputs held outside the repository. Generated results were compared with the supplied saved results:

| Output | Comparison |
| --- | --- |
| Episode-confirmation comparison | Matched, including dates, durations and censoring |
| Preferred two-day recovery dataset | Matched |
| Full-calendar regression dataset | Matched |
| Model summaries | Matched |
| Complete regression coefficients | Matched, including HAC standard errors, p-values and confidence intervals |
| Concise regression comparison | Matched |
| Predictor correlation matrix | Matched |
| VIF diagnostics | Matched |

Floating-point comparisons used relative tolerance `1e-8` and absolute tolerance `1e-10`. Labels and table structures were also compared. Charts were regenerated and inspected, with selected annotations used to make the recovery scatter plot legible.

Separately, an independent NumPy least-squares calculation reproduced all 15 saved OLS coefficient sets and R-squared values. This is a numerical cross-check, not independent verification of source prices or the economic specification.

## Changes made for publication

- Retained the six preferred analyses and omitted the conflicting legacy recovery implementation.
- Replaced draft filenames with descriptive names and corrected the correlation filename spelling.
- Added configurable input/output paths and a runner that respects script dependencies.
- Added validation for required price columns, positive finite prices, unique daily dates and complete calendar spacing.
- Added focused synthetic tests for recovery behaviour and data validation.
- Reduced overlapping annotations in the recovery chart while retaining every plotted observation.
- Removed a docstring claim about optional log-transformed models, which were not implemented.
- Added source-data requirements, methodology notes and explicit limitations.

The main research definitions, samples, predictors and regression settings were preserved. No raw datasets, source-derived CSV results, machine-specific logs or caches are distributed in this repository.

## Limits of these checks

Reproducing outputs confirms consistency with the supplied implementation and inputs. It does not validate the original provider's data accuracy, establish redistribution rights, prove causal claims or demonstrate out-of-sample predictive performance. Original input provenance is incomplete, as described in the data guide.
