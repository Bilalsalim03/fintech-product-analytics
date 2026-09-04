"""
A/B test: did a £10 first-deposit bonus lift conversion, and was it profitable?
"""
import duckdb
import numpy as np
from scipy import stats

DB_PATH = "data/analytics.duckdb"
BONUS_COST = 10.0          # paid to each treatment user who deposits
TAKE_RATE = 0.01           # revenue as a share of card spend (interchange-style)


def run():
    con = duckdb.connect(DB_PATH, read_only=True)
    with open("sql/ab_test_users.sql") as f:
        df = con.execute(f.read()).df()
    con.close()

    c = df[df.ab_group == "control"]
    t = df[df.ab_group == "treatment"]
    n_c, n_t = len(c), len(t)
    conv_c, conv_t = c.first_deposit.mean(), t.first_deposit.mean()
    lift = conv_t - conv_c

    # Two-proportion z-test
    pooled = (c.first_deposit.sum() + t.first_deposit.sum()) / (n_c + n_t)
    se = np.sqrt(pooled * (1 - pooled) * (1 / n_c + 1 / n_t))
    z = lift / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    ci = (lift - 1.96 * se, lift + 1.96 * se)

    print(f"Control:   n={n_c:,}  deposit rate {conv_c:.1%}")
    print(f"Treatment: n={n_t:,}  deposit rate {conv_t:.1%}")
    print(f"Lift: {lift:+.1%}  (95% CI {ci[0]:+.1%} to {ci[1]:+.1%})   z={z:.2f}  p={p_value:.4f}")

    # Economics: what did the bonus cost, and what did it bring in?
    rev_c = c.spend_90d.mean() * TAKE_RATE
    rev_t = t.spend_90d.mean() * TAKE_RATE
    incremental_rev_per_user = rev_t - rev_c
    cost_per_user = BONUS_COST * conv_t          # bonus paid to every treatment depositor

    print(f"\n90-day revenue per signup:  control £{rev_c:.2f}   treatment £{rev_t:.2f}")
    print(f"Incremental revenue per treated signup: £{incremental_rev_per_user:+.2f}")
    print(f"Bonus cost per treated signup:          £{cost_per_user:.2f}")
    print(f"Net per treated signup over 90 days:    £{incremental_rev_per_user - cost_per_user:+.2f}")

    # How many months of the incremental revenue would it take to pay back the bonus?
    monthly_incremental = incremental_rev_per_user / 3
    if monthly_incremental > 0:
        print(f"Payback period at this rate: {cost_per_user / monthly_incremental:.1f} months")

    return df


if __name__ == "__main__":
    run()