"""
Funnel analysis: conversion by step, overall and by channel.
"""
import duckdb
import matplotlib.pyplot as plt

DB_PATH = "data/analytics.duckdb"


def run():
    con = duckdb.connect(DB_PATH, read_only=True)
    with open("sql/funnel_by_channel.sql") as f:
        by_channel = con.execute(f.read()).df()

    overall = con.execute("""
        SELECT COUNT(*) AS signups, SUM(kyc_completed) AS kyc,
               SUM(first_deposit) AS deposit, SUM(first_transaction) AS transacting
        FROM user_funnel
    """).df().iloc[0]
    con.close()

    print("Overall funnel:")
    print(f"  signups     {overall.signups:>7,}")
    print(f"  kyc         {overall.kyc:>7,}  ({overall.kyc / overall.signups:.1%} of signups)")
    print(f"  deposit     {overall.deposit:>7,}  ({overall.deposit / overall.kyc:.1%} of kyc)")
    print(f"  transacting {overall.transacting:>7,}  ({overall.transacting / overall.deposit:.1%} of deposit)")
    print("\nBy channel:")
    print(by_channel.to_string(index=False))

    # Chart: end-to-end and step conversion by channel
    fig, ax = plt.subplots(figsize=(8, 4.5))
    steps = ["pct_kyc", "pct_deposit_given_kyc", "pct_txn_given_deposit"]
    labels = ["Signup → KYC", "KYC → Deposit", "Deposit → Transaction"]
    x = range(len(by_channel))
    w = 0.25
    for i, (s, lab) in enumerate(zip(steps, labels)):
        ax.bar([xi + i * w for xi in x], by_channel[s], width=w, label=lab)
    ax.set_xticks([xi + w for xi in x])
    ax.set_xticklabels(by_channel.channel)
    ax.set_ylabel("Step conversion (%)")
    ax.set_title("Funnel step conversion by acquisition channel")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig("results/funnel_by_channel.png", dpi=150)
    return by_channel


if __name__ == "__main__":
    run()