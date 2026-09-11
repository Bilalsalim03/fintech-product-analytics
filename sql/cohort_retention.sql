-- Monthly cohort retention for users who made at least one transaction.
-- Months are counted from each user's own signup date, not the calendar.
WITH cohorts AS (
    SELECT user_id, signup_date, DATE_TRUNC('month', signup_date) AS cohort_month
    FROM user_funnel
    WHERE first_transaction = 1
),
sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM cohorts
    GROUP BY cohort_month
),
activity AS (
    SELECT DISTINCT
        c.user_id,
        c.cohort_month,
        CAST(FLOOR(DATE_DIFF('day', c.signup_date, t.txn_date) / 30) AS INTEGER) AS month_number
    FROM transactions t
    JOIN cohorts c ON c.user_id = t.user_id
)
SELECT
    a.cohort_month,
    a.month_number,
    s.cohort_size,
    COUNT(*)                                          AS active_users,
    ROUND(100.0 * COUNT(*) / s.cohort_size, 1)        AS retention_pct
FROM activity a
JOIN sizes s ON s.cohort_month = a.cohort_month
GROUP BY a.cohort_month, a.month_number, s.cohort_size
ORDER BY a.cohort_month, a.month_number;