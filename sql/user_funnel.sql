-- One row per user with funnel step flags derived from the raw event log.
CREATE OR REPLACE TABLE user_funnel AS
SELECT
    u.user_id,
    u.signup_date,
    u.channel,
    u.country,
    u.device,
    u.age_band,
    u.ab_group,
    MAX(CASE WHEN e.event_type = 'kyc_completed'     THEN 1 ELSE 0 END) AS kyc_completed,
    MAX(CASE WHEN e.event_type = 'first_deposit'     THEN 1 ELSE 0 END) AS first_deposit,
    MAX(CASE WHEN e.event_type = 'first_transaction' THEN 1 ELSE 0 END) AS first_transaction,
    MIN(CASE WHEN e.event_type = 'first_transaction' THEN e.event_time END) AS first_transaction_time
FROM users u
LEFT JOIN events e ON e.user_id = u.user_id
GROUP BY ALL;