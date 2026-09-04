
SELECT
    channel,
    COUNT(*)                          AS signups,
    SUM(kyc_completed)                AS kyc,
    SUM(first_deposit)                AS deposit,
    SUM(first_transaction)            AS transacting,
    ROUND(100.0 * SUM(kyc_completed) / COUNT(*), 1)                    AS pct_kyc,
    ROUND(100.0 * SUM(first_deposit) / SUM(kyc_completed), 1)          AS pct_deposit_given_kyc,
    ROUND(100.0 * SUM(first_transaction) / SUM(first_deposit), 1)      AS pct_txn_given_deposit,
    ROUND(100.0 * SUM(first_transaction) / COUNT(*), 1)                AS pct_end_to_end
FROM user_funnel
GROUP BY channel
ORDER BY pct_end_to_end DESC;