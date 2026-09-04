"""
Fintech product analytics: funnel, retention, A/B test.
Run:  python main.py
Regenerates the data, rebuilds the database, runs every analysis.
"""
import subprocess
import sys

from src.etl import build_database
from src import funnel, retention, ab_test


def main():
    print("=== Generating data ===")
    subprocess.run([sys.executable, "src/generate_data.py"], check=True)

    print("\n=== Building database ===")
    for table, n in build_database().items():
        print(f"  {table:15s} {n:>10,}")

    print("\n=== Funnel ===")
    funnel.run()

    print("\n=== Retention ===")
    retention.run()

    print("\n=== A/B test ===")
    ab_test.run()

    print("\nCharts saved to results/.")


if __name__ == "__main__":
    main()