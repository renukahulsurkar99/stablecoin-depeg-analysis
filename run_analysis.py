"""Run the dissertation analyses in dependency order using local inputs."""

import argparse
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).parent / "data")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "outputs")
    parser.add_argument(
        "--crypto-only", action="store_true",
        help="Run episode, recovery, correlation and event analyses without Bloomberg data."
    )
    args = parser.parse_args()
    data_dir = args.data_dir.resolve()
    output_dir = args.output_dir.resolve()
    required = ["merged_prices.csv"]
    if not args.crypto_only:
        required.append("BloombergDataValues.xlsx")
    for name in required:
        if not (data_dir / name).is_file():
            parser.error(f"Missing {data_dir / name}. See data/README.md.")
    output_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["STABLECOIN_DATA_DIR"] = str(data_dir)
    env["STABLECOIN_OUTPUT_DIR"] = str(output_dir)
    env.setdefault("MPLCONFIGDIR", str(output_dir / ".matplotlib"))
    scripts = [
        "detect_depeg_episodes.py", "analyse_recovery.py",
        "analyse_correlations.py", "plot_march_2023_event.py",
    ]
    if not args.crypto_only:
        scripts.extend(["prepare_regression_data.py", "run_regressions.py"])
    for script in scripts:
        print(f"\nRunning {script}", flush=True)
        subprocess.run([sys.executable, str(Path(__file__).parent / script)], env=env, check=True)
    print(f"\nAnalysis complete. Results: {output_dir}")


if __name__ == "__main__":
    main()
