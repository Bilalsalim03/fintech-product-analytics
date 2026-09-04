-- One row per user in the experiment, with the outcome and 90-day spend.
WITH spend AS (
    SELECT
        f.user_id,
        SUM(t.amount) AS spend_90d
    FROM user_funnel f
    JOIN transactions t
      ON t.user_id = f.user_id
     AND t.txn_date < f.signup_date + INTERVAL 90 DAY
    GROUP BY f.user_id
)
SELECT
    f.user_id,
    f.ab_group,
    f.first_deposit,
    COALESCE(s.spend_90d, 0) AS spend_90d
FROM user_funnel f
LEFT JOIN spend s ON s.user_id = f.user_id
WHERE f.ab_group IN ('control', 'treatment');