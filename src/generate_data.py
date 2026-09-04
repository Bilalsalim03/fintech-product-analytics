"""
Simulate a fintech app's sign-up funnel, transactions, and an A/B test.

Produces data/users.csv, data/events.csv, data/transactions.csv.

"""
import numpy as np
import pandas as pd

SEED = 42
N_USERS = 20_000
START = pd.Timestamp("2025-09-01")
END = pd.Timestamp("2026-08-31")
DAYS = (END - START).days

rng = np.random.default_rng(SEED)


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def logit(p):
    return np.log(p / (1 - p))


def make_users():
    signup_day = rng.integers(0, DAYS, N_USERS)
    users = pd.DataFrame({
        "user_id": np.arange(1, N_USERS + 1),
        "signup_date": START + pd.to_timedelta(signup_day, "D"),
        "channel": rng.choice(["organic", "paid_social", "referral", "app_store"], N_USERS, p=[.35, .30, .15, .20]),
        "country": rng.choice(["UK", "PL", "PT", "ES"], N_USERS, p=[.40, .25, .15, .20]),
        "device": rng.choice(["ios", "android"], N_USERS, p=[.55, .45]),
        "age_band": rng.choice(["18-24", "25-34", "35-44", "45+"], N_USERS, p=[.30, .40, .20, .10]),
    })
    # A/B test: users who signed up in Mar-Apr 2026 were randomised to a £10 first-deposit bonus
    in_window = (users.signup_date >= "2026-03-01") & (users.signup_date < "2026-05-01")
    users["ab_group"] = np.where(in_window, rng.choice(["control", "treatment"], N_USERS), "not_in_test")
    return users


def make_funnel(users):
    n = len(users)
    # KYC completion: referral users better, paid social worse, android slightly worse
    kyc_x = (logit(0.70)
             + np.where(users.channel == "referral", 0.4, 0)
             + np.where(users.channel == "paid_social", -0.3, 0)
             + np.where(users.device == "android", -0.15, 0))
    kyc = rng.random(n) < sigmoid(kyc_x)

    # First deposit: referral better, youngest worse, treatment group gets the bonus effect
    dep_x = (logit(0.55)
             + np.where(users.channel == "referral", 0.5, 0)
             + np.where(users.age_band == "18-24", -0.3, 0)
             + np.where(users.ab_group == "treatment", 0.35, 0))
    deposit = kyc & (rng.random(n) < sigmoid(dep_x))

    # First transaction: most depositors transact
    first_txn = deposit & (rng.random(n) < 0.80)

    users["kyc_completed"] = kyc
    users["first_deposit"] = deposit
    users["first_transaction"] = first_txn

    # Event timestamps
    rows = []
    for u in users.itertuples():
        t = u.signup_date
        rows.append((u.user_id, "signup", t))
        if u.kyc_completed:
            t = t + pd.Timedelta(days=int(rng.integers(0, 4)))
            rows.append((u.user_id, "kyc_completed", t))
        if u.first_deposit:
            t = t + pd.Timedelta(days=int(rng.integers(0, 8)))
            rows.append((u.user_id, "first_deposit", t))
        if u.first_transaction:
            t = t + pd.Timedelta(days=int(rng.integers(0, 6)))
            rows.append((u.user_id, "first_transaction", t))
    events = pd.DataFrame(rows, columns=["user_id", "event_type", "event_time"])
    return users, events


def make_transactions(users):
    """Monthly activity with a churn hazard that depends on user attributes."""
    active = users[users.first_transaction]
    rows = []
    for u in active.itertuples():
        # Monthly churn probability
        churn_x = (logit(0.12)
                   + np.where(u.channel == "referral", -0.5, 0)
                   + np.where(u.channel == "paid_social", 0.4, 0)
                   + np.where(u.age_band == "18-24", 0.3, 0)
                   + np.where(u.ab_group == "treatment", -0.15, 0))
        p_churn = sigmoid(churn_x)
        # Transactions per month
        lam = 6.0 * (1.3 if u.country == "UK" else 1.0) * (0.8 if u.age_band == "45+" else 1.0)

        month = 0
        alive = True
        while alive:
            month_start = u.signup_date + pd.DateOffset(months=month)
            if month_start > END:
                break
            n_txn = rng.poisson(lam)
            for _ in range(n_txn):
                d = month_start + pd.Timedelta(days=int(rng.integers(0, 30)))
                if d > END:
                    continue
                amount = float(np.round(rng.lognormal(3.0, 0.8), 2))
                cat = rng.choice(["groceries", "transport", "eating_out", "shopping", "bills", "transfer"],
                                 p=[.25, .15, .20, .20, .10, .10])
                rows.append((u.user_id, d, amount, cat))
            month += 1
            alive = rng.random() >= p_churn
    return pd.DataFrame(rows, columns=["user_id", "txn_date", "amount", "category"])


if __name__ == "__main__":
    users = make_users()
    users, events = make_funnel(users)
    transactions = make_transactions(users)

    users.drop(columns=["kyc_completed", "first_deposit", "first_transaction"]).to_csv("data/users.csv", index=False)
    events.to_csv("data/events.csv", index=False)
    transactions.to_csv("data/transactions.csv", index=False)

    print(f"users: {len(users):,}   events: {len(events):,}   transactions: {len(transactions):,}")
    print(f"KYC {users.kyc_completed.mean():.1%}  deposit {users.first_deposit.mean():.1%}  first txn {users.first_transaction.mean():.1%}")