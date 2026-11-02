-- COMMERCIAL METRICS ENGINE
-- Calculates KPIs directly in the DB to optimize BI performance

-- 1. Customer Retention & Churn Analysis
-- COMMERCIAL METRICS ENGINE (FIXED FOR SCENARIO DATE)
-- We anchor 'now' to 2026-08-06 to match the project scenario

-- 1. Customer Retention & Churn Analysis
WITH customer_activity AS (
    SELECT 
        c.customer_id,
        c.segment,
        c.signup_date,
        MAX(t.transaction_date) as last_txn_date,
        COUNT(t.transaction_id) as total_txns,
        SUM(t.amount_kes) as total_revenue
    FROM Dim_Customer c
    LEFT JOIN Fact_Transactions t ON c.customer_id = t.customer_id AND t.status = 'Success'
    GROUP BY c.customer_id
),
churn_flags AS (
    SELECT 
        *,
        CASE 
            -- FIXED: Using specific scenario date instead of 'now'
            WHEN julianday('2026-08-06') - julianday(last_txn_date) > 30 THEN 'Churned'
            ELSE 'Active'
        END as current_status,
        -- Payment Velocity: Avg days between refills
        (julianday('2026-08-06') - julianday(signup_date)) / NULLIF(total_txns, 0) as avg_days_between_refills
    FROM customer_activity
)

SELECT 
    segment,
    current_status,
    COUNT(*) as customer_count,
    ROUND(AVG(total_revenue), 2) as avg_ltv,
    ROUND(AVG(avg_days_between_refills), 1) as avg_refill_cycle_days
FROM churn_flags
GROUP BY segment, current_status
ORDER BY segment, current_status;

-- 2. Agent Performance Quality Check (Fraud Detection)
SELECT 
    a.agent_id,
    a.name,
    COUNT(DISTINCT c.customer_id) as activations,
    SUM(CASE WHEN cf.current_status = 'Churned' THEN 1 ELSE 0 END) as early_churners,
    ROUND(100.0 * SUM(CASE WHEN cf.current_status = 'Churned' THEN 1 ELSE 0 END) / COUNT(DISTINCT c.customer_id), 2) as churn_rate_pct
FROM Dim_Agent a
JOIN Dim_Customer c ON a.agent_id = c.agent_id
JOIN (
    SELECT customer_id, 
           -- FIXED: Anchored to scenario date 2026-08-06
           CASE WHEN julianday('2026-08-06') - julianday(MAX(transaction_date)) > 30 THEN 'Churned' ELSE 'Active' END as current_status
    FROM Fact_Transactions 
    WHERE status = 'Success'
    GROUP BY customer_id
) cf ON c.customer_id = cf.customer_id
GROUP BY a.agent_id
HAVING churn_rate_pct > 20; -- Flag agents with >20% churn