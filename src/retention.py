"""
Cohort retention: what fraction of each signup cohort is still transacting
N months later?
"""
import duckdb
import numpy as np
import matplotlib.pyplot as plt

DB_PATH = "data/analytics.duckdb"
DATA_END = np.datetime64("2026-08")   # last month in the data


def run():
    con = duckdb.connect(DB_PATH, read_only=True)
    with open("sql/cohort_retention.sql") as f:
        df = con.execute(f.read()).df()
    con.close()

    table = df.pivot(index="cohort_month", columns="month_number", values="retention_pct")

    # Blank out cells that are in the future
    for cohort in table.index:
        for m in table.columns:
            if np.datetime64(cohort, "M") + np.timedelta64(int(m), "M") >= DATA_END:
                table.loc[cohort, m] = np.nan
    table = table.dropna(how="all").dropna(axis=1, how="all")            

    print("Retention (% of cohort transacting in month N after signup):")
    print(table.round(0).fillna("").to_string())

    # Average curve across cohorts, using only observed cells
    curve = table.mean(axis=0, skipna=True)
    print("\nAverage retention by month:")
    for m in [1, 3, 6, 9]:
        if m in curve.index:
            print(f"  month {m}: {curve[m]:.1f}%")

    # Heatmap
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(table.values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(table.columns)))
    ax.set_xticklabels(table.columns)
    ax.set_yticks(range(len(table.index)))
    ax.set_yticklabels([str(c)[:7] for c in table.index])
    ax.set_xlabel("Months since signup")
    ax.set_ylabel("Signup cohort")
    ax.set_title("Cohort retention (% still transacting)")
    for i in range(table.shape[0]):
        for j in range(table.shape[1]):
            v = table.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.0f}", ha="center", va="center",
                        fontsize=7, color="white" if v > 50 else "black")
    fig.colorbar(im, ax=ax, label="%")
    fig.tight_layout()
    fig.savefig("results/cohort_retention.png", dpi=150)
    return table


if __name__ == "__main__":
    run()