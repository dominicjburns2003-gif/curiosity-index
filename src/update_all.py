"""
Curiosity Index - the daily update. This is what GitHub Actions runs each morning.

Runs every step of the pipeline in order, so the data, results and charts
(and so the live app) are always up to date:

  1. page views up to yesterday          fetch_pageviews.py
  2. new clickstream months, if any      fetch_clickstream.py --new-only
  3. prices, returns and factors         fetch_prices.py
  4. market cap                          fetch_market_cap.py
  5. the monthly panel                   build_features.py
  6. portfolio sorts and their chart     backtest.py, chart_sorts.py
  7. the out-of-sample model             walk_forward.py
  8. the long-only strategy and live picks  strategy.py

If a step fails (e.g. Yahoo Finance is down), the later steps still run on
the last good data, and the update ends with an error so the failure shows
up on GitHub instead of passing silently.

Run it from the project folder:
    python src/update_all.py
    python src/update_all.py --skip-clickstream   # e.g. while the full history downloads
"""

from pathlib import Path
import subprocess
import sys
import time

SRC_DIR = Path(__file__).resolve().parent
STEPS = [
    ["fetch_pageviews.py"],
    ["fetch_clickstream.py", "--new-only"],
    ["fetch_prices.py"],
    ["fetch_market_cap.py"],
    ["build_features.py"],
    ["backtest.py"],
    ["chart_sorts.py"],
    ["walk_forward.py"],
    ["strategy.py"],
]


def main() -> None:
    skip_clickstream = "--skip-clickstream" in sys.argv[1:]
    failed = []
    for step in STEPS:
        if skip_clickstream and step[0] == "fetch_clickstream.py":
            print("== fetch_clickstream.py: skipped\n")
            continue
        print(f"== {' '.join(step)}", flush=True)
        start = time.time()
        result = subprocess.run([sys.executable, str(SRC_DIR / step[0]), *step[1:]])
        status = "ok" if result.returncode == 0 else "FAILED"
        print(f"== {step[0]}: {status} ({time.time() - start:.0f} s)\n", flush=True)
        if result.returncode != 0:
            failed.append(step[0])

    if failed:
        sys.exit(f"Update finished with failures: {', '.join(failed)}")
    print("Update finished: every step ok")


if __name__ == "__main__":
    main()
