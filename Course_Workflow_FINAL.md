# PayFlow Fintech Analytics Course - Complete Workflow (RFM INTEGRATED)

## Course Duration: 2 Hours

---

## MODULE 1: PROBLEM STATEMENT & SETUP (15 minutes)

### The Business Context

**Company**: PayFlow - A payment processing platform (like Stripe)  
**Size**: 5,000 merchants, processing $23M annually  
**Problem**: CEO has 3 urgent questions:

1. **Why is our payment failure rate 5%?** (Industry standard is 2-3%)
2. **Which customers are at risk of churning?** (High support tickets + payment issues)
3. **Are we profitable on all customer segments?** (Some plans may be losers)

### Your Role
You're the data analyst. You have 4 data sources:
- **Customer database** (Internal CRM): Signups, plans, MRR, industry
- **Transaction logs** (Stripe): Payments, refunds, disputes, fees
- **Support tickets** (Zendesk): Customer support requests, satisfaction
- **Dispute records** (Stripe): Chargebacks, reasons, outcomes

### Success Criteria
Build a dashboard that:
- Identifies high-risk customers using RFM segmentation
- Shows payment failure patterns by customer segment
- Calculates customer-level health scores

---

## MODULE 2: DATA SETUP IN BIGQUERY (10 minutes)

### Step 1: Create Schemas

```sql
-- Raw data layer
CREATE SCHEMA payflow_raw;

-- Analytics layer (for RFM calculations)
CREATE SCHEMA payflow_analytics;

-- Star schema layer (final dimensional model)
CREATE SCHEMA payflow_star;
```

### Step 2: Create Tables in payflow_raw

```sql
CREATE TABLE payflow_raw.customers (
  customer_id STRING,
  business_name STRING,
  industry STRING,
  signup_date DATE,
  plan STRING,
  mrr INT64,
  country STRING,
  employee_size STRING
);

CREATE TABLE payflow_raw.transactions (
  transaction_id STRING,
  customer_id STRING,
  transaction_date TIMESTAMP,
  amount FLOAT64,
  currency STRING,
  status STRING,
  payment_method STRING,
  fee FLOAT64
);

CREATE TABLE payflow_raw.support_tickets (
  ticket_id STRING,
  customer_id STRING,
  created_at TIMESTAMP,
  resolved_at TIMESTAMP,
  category STRING,
  priority STRING,
  satisfaction_score INT64
);

CREATE TABLE payflow_raw.disputes (
  dispute_id STRING,
  transaction_id STRING,
  customer_id STRING,
  created_date DATE,
  reason STRING,
  status STRING,
  amount FLOAT64
);
```

### Step 3: Upload CSVs
1. BigQuery Console → payflow_raw dataset
2. Upload each CSV:
   - customers.csv → customers table
   - transactions.csv → transactions table
   - support_tickets.csv → support_tickets table
   - disputes.csv → disputes table
3. Auto-detect schema, skip header row

### Step 4: Verify Data
```sql
SELECT 
  'customers' as table_name, COUNT(*) as rows FROM payflow_raw.customers
UNION ALL
SELECT 'transactions', COUNT(*) FROM payflow_raw.transactions
UNION ALL
SELECT 'support_tickets', COUNT(*) FROM payflow_raw.support_tickets
UNION ALL
SELECT 'disputes', COUNT(*) FROM payflow_raw.disputes;
```

**Expected**: 5K customers, 417K transactions, 6.8K tickets, 3.1K disputes

---

## MODULE 3: EXPLORATORY DATA ANALYSIS (20 minutes)

### Query 1: Transaction Status Distribution
```sql
SELECT 
  status,
  COUNT(*) as transaction_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM payflow_raw.transactions
GROUP BY status
ORDER BY transaction_count DESC;
```

**Finding**: 91.7% successful, 5.1% failed (PROBLEM: should be 2-3%)

---

### Query 2: Payment Failure by Method
```sql
SELECT 
  payment_method,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
  ROUND(AVG(CASE WHEN status = 'failed' THEN 1.0 ELSE 0 END) * 100, 2) as failure_rate_pct
FROM payflow_raw.transactions
GROUP BY payment_method
ORDER BY failure_rate_pct DESC;
```

**Finding**: Card payments: 6.5% failure | Wallets: 3% failure  
**Insight**: Card payment infrastructure needs attention

---

### Query 3: Monthly Transaction Volume
```sql
SELECT 
  DATE_TRUNC(transaction_date, MONTH) as month,
  COUNT(*) as transactions,
  ROUND(SUM(CASE WHEN status = 'successful' THEN amount ELSE 0 END), 2) as successful_volume,
  ROUND(SUM(CASE WHEN status = 'successful' THEN fee ELSE 0 END), 2) as fees_earned
FROM payflow_raw.transactions
GROUP BY month
ORDER BY month DESC
LIMIT 12;
```

**Finding**: Revenue growing, but fees not keeping pace due to failures

---

### Query 4: Support Ticket Analysis
```sql
SELECT 
  category,
  COUNT(*) as ticket_count,
  ROUND(AVG(satisfaction_score), 2) as avg_satisfaction,
  ROUND(AVG(TIMESTAMP_DIFF(resolved_at, created_at, HOUR)), 1) as avg_resolution_hours
FROM payflow_raw.support_tickets
GROUP BY category
ORDER BY ticket_count DESC;
```

**Finding**: "payment_failure" is #1 category (2,322 tickets) with low satisfaction (2.8/5)

---

### Query 5: Customer Problem Indicators
```sql
SELECT 
  c.customer_id,
  c.business_name,
  c.industry,
  c.plan,
  COUNT(t.transaction_id) as total_txns,
  SUM(CASE WHEN t.status = 'failed' THEN 1 ELSE 0 END) as failed_txns,
  COUNT(s.ticket_id) as support_tickets,
  COUNT(d.dispute_id) as disputes
FROM payflow_raw.customers c
LEFT JOIN payflow_raw.transactions t ON c.customer_id = t.customer_id
LEFT JOIN payflow_raw.support_tickets s ON c.customer_id = s.customer_id
LEFT JOIN payflow_raw.disputes d ON c.customer_id = d.customer_id
GROUP BY c.customer_id, c.business_name, c.industry, c.plan
HAVING failed_txns > 10
ORDER BY failed_txns DESC, support_tickets DESC
LIMIT 20;
```

**Finding**: High-failure customers also have high support tickets → correlation → churn risk

---

## MODULE 4: RFM FRAMEWORK FOR FINTECH (25 minutes)

### Understanding RFM

**Traditional RFM** (E-commerce):
- Recency: Days since last purchase
- Frequency: Number of purchases
- Monetary: Total spend

**PayFlow RFM** (Payment processing):
- **R**ecency: Days since last **successful transaction**
- **F**requency: **Transactions per month** (velocity)
- **M**onetary: **Monthly transaction volume** processed

**Why adapt?** We care about payment activity, not purchases. A merchant with recent successful transactions is engaged. A merchant who stopped processing = churn risk.

---

### Step 1: Calculate RFM Metrics

```sql
CREATE TABLE payflow_analytics.customer_rfm AS

WITH rfm_base AS (
  SELECT 
    c.customer_id,
    c.business_name,
    c.industry,
    c.plan,
    c.mrr,
    
    -- RECENCY: Days since last successful transaction
    DATE_DIFF(
      CURRENT_DATE(), 
      MAX(CASE WHEN t.status = 'successful' THEN DATE(t.transaction_date) END), 
      DAY
    ) as days_since_last_txn,
    
    -- FREQUENCY: Transactions per month (avg over customer lifetime)
    COUNT(CASE WHEN t.status = 'successful' THEN t.transaction_id END) / 
      GREATEST(DATE_DIFF(CURRENT_DATE(), c.signup_date, DAY) / 30.0, 1) as avg_monthly_txns,
    
    -- MONETARY: Monthly transaction volume
    SUM(CASE WHEN t.status = 'successful' THEN t.amount ELSE 0 END) / 
      GREATEST(DATE_DIFF(CURRENT_DATE(), c.signup_date, DAY) / 30.0, 1) as avg_monthly_volume
    
  FROM payflow_raw.customers c
  LEFT JOIN payflow_raw.transactions t ON c.customer_id = t.customer_id
  GROUP BY c.customer_id, c.business_name, c.industry, c.plan, c.mrr, c.signup_date
)

SELECT 
  *,
  
  -- Score Recency (1-5, higher = better)
  CASE 
    WHEN days_since_last_txn IS NULL THEN 1  -- Never transacted
    WHEN days_since_last_txn <= 7 THEN 5
    WHEN days_since_last_txn <= 30 THEN 4
    WHEN days_since_last_txn <= 60 THEN 3
    WHEN days_since_last_txn <= 90 THEN 2
    ELSE 1
  END as recency_score,
  
  -- Score Frequency (1-5)
  CASE 
    WHEN avg_monthly_txns >= 100 THEN 5
    WHEN avg_monthly_txns >= 50 THEN 4
    WHEN avg_monthly_txns >= 20 THEN 3
    WHEN avg_monthly_txns >= 5 THEN 2
    ELSE 1
  END as frequency_score,
  
  -- Score Monetary (1-5)
  CASE 
    WHEN avg_monthly_volume >= 10000 THEN 5
    WHEN avg_monthly_volume >= 5000 THEN 4
    WHEN avg_monthly_volume >= 2000 THEN 3
    WHEN avg_monthly_volume >= 500 THEN 2
    ELSE 1
  END as monetary_score

FROM rfm_base;
```

**Teaching point**: Each metric gets scored 1-5. Score 5 = best performance. This makes it easy to compare customers.

---

### Step 2: Create Customer Segments

```sql
CREATE TABLE payflow_analytics.customer_segments AS

SELECT 
  *,
  
  CASE 
    -- Champions: Active, frequent, high value
    WHEN recency_score >= 4 AND frequency_score >= 4 AND monetary_score >= 4 THEN 'Champions'
    
    -- Loyal: Good recency and frequency
    WHEN recency_score >= 4 AND frequency_score >= 3 THEN 'Loyal'
    
    -- Whales: High value but infrequent (large transaction sizes)
    WHEN monetary_score >= 4 AND frequency_score <= 2 THEN 'Whales'
    
    -- At Risk: Used to be active, now dormant
    WHEN recency_score = 4 AND frequency_score >= 2 THEN 'At Risk'

    -- New/Testing: Recent signup, low usage
    WHEN recency_score >= 3 AND frequency_score <= 2 AND monetary_score <= 2 THEN 'New/Testing'

    -- Dormant: No recent activity
    WHEN recency_score = 1 THEN 'Dormant'

    
    ELSE 'Needs Attention'
  END as segment

FROM payflow_analytics.customer_rfm;
```

**Teaching point**: Segments group customers by behavior patterns. "At Risk" = was active but going quiet = churn warning.

---

### Step 3: Validate Segments

```sql
SELECT 
  segment,
  COUNT(*) as customers,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) as pct_of_customers,
  SUM(mrr) as total_mrr,
  ROUND(AVG(avg_monthly_volume), 2) as avg_monthly_volume,
  ROUND(AVG(avg_monthly_txns), 1) as avg_monthly_txns
FROM payflow_analytics.customer_segments
GROUP BY segment
ORDER BY total_mrr DESC;
```

**Expected distribution**:
- Champions: 15-20% (highest MRR)
- Dormant: 30-35% (signed up but inactive)
- At Risk: 10-15% (need immediate attention)
- Loyal: 15-20%
- New/Testing: 15-20%

---

### Step 4: Add Health Scoring

```sql
CREATE TABLE payflow_analytics.customer_health AS

SELECT 
  s.*,
  
  -- Payment failure rate (last 90 days)
  COALESCE(f.failure_rate, 0) as payment_failure_rate,
  
  -- Support tickets (last 90 days)
  COALESCE(t.recent_tickets, 0) as recent_support_tickets,
  
  -- Disputes (all time)
  COALESCE(d.dispute_count, 0) as total_disputes,
  
  -- Health score (0-100)
  CAST(
    (s.recency_score * 20) + 
    (s.frequency_score * 20) +
    (s.monetary_score * 20) +
    CASE WHEN COALESCE(f.failure_rate, 0) > 0.10 THEN -20 ELSE 0 END +
    CASE WHEN COALESCE(t.recent_tickets, 0) > 5 THEN -15 ELSE 0 END +
    CASE WHEN COALESCE(d.dispute_count, 0) > 2 THEN -15 ELSE 0 END
  AS INT64) as health_score

FROM payflow_analytics.customer_segments s

LEFT JOIN (
  SELECT 
    customer_id,
    AVG(CASE WHEN status = 'failed' THEN 1.0 ELSE 0 END) as failure_rate
  FROM payflow_raw.transactions
  WHERE transaction_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
  GROUP BY customer_id
) f ON s.customer_id = f.customer_id

LEFT JOIN (
  SELECT 
    customer_id,
    COUNT(*) as recent_tickets
  FROM payflow_raw.support_tickets
  WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY)
  GROUP BY customer_id
) t ON s.customer_id = t.customer_id

LEFT JOIN (
  SELECT 
    customer_id,
    COUNT(*) as dispute_count
  FROM payflow_raw.disputes
  GROUP BY customer_id
) d ON s.customer_id = d.customer_id;
```

**Health Score Formula**:
- Base: R(20) + F(20) + M(20) = max 100
- Penalty: -20 if failure rate >10%
- Penalty: -15 if tickets >5
- Penalty: -15 if disputes >2

**Health Status**:
- 70-100 = Healthy (green)
- 40-69 = At Risk (yellow)
- 0-39 = Critical (red)

---

### Step 5: Validate Health Scores

```sql
SELECT 
  CASE 
    WHEN health_score >= 70 THEN 'Healthy'
    WHEN health_score >= 40 THEN 'At Risk'
    ELSE 'Critical'
  END as health_status,
  COUNT(*) as customers,
  SUM(mrr) as total_mrr,
  ROUND(AVG(payment_failure_rate) * 100, 1) as avg_failure_rate_pct
FROM payflow_analytics.customer_health
GROUP BY health_status
ORDER BY 
  CASE health_status 
    WHEN 'Healthy' THEN 1 
    WHEN 'At Risk' THEN 2 
    ELSE 3 
  END;
```

**Expected**: Mix of all three statuses with At Risk + Critical representing churn candidates.

---

## MODULE 5: STAR SCHEMA TRANSFORMATION (30 minutes)

### Why Star Schema?

**Current state**: RFM metrics in `payflow_analytics`, raw data in `payflow_raw`  
**Problem**: Dashboard needs to JOIN multiple schemas, complex queries  
**Solution**: Build star schema with RFM embedded in customer dimension

---

### Step 1: Create dim_date

```sql
CREATE TABLE payflow_star.dim_date AS

WITH date_spine AS (
  SELECT DATE_ADD('2023-01-01', INTERVAL day_offset DAY) as date_day
  FROM UNNEST(GENERATE_ARRAY(0, 730)) as day_offset  -- 2 years
)

SELECT 
  FORMAT_DATE('%Y%m%d', date_day) as date_key,
  date_day as full_date,
  EXTRACT(YEAR FROM date_day) as year,
  EXTRACT(MONTH FROM date_day) as month,
  FORMAT_DATE('%B', date_day) as month_name,
  EXTRACT(DAY FROM date_day) as day,
  EXTRACT(DAYOFWEEK FROM date_day) as day_of_week,
  FORMAT_DATE('%A', date_day) as day_name,
  EXTRACT(QUARTER FROM date_day) as quarter,
  CASE WHEN EXTRACT(DAYOFWEEK FROM date_day) IN (1,7) THEN TRUE ELSE FALSE END as is_weekend
FROM date_spine;
```

---

### Step 2: Create dim_customer WITH RFM

**THIS IS THE KEY INTEGRATION STEP**

```sql
CREATE TABLE payflow_star.dim_customer AS

SELECT 
  -- Basic customer attributes
  c.customer_id as customer_key,
  c.customer_id,
  c.business_name,
  c.industry,
  c.plan,
  c.mrr,
  c.country,
  c.employee_size,
  c.signup_date,
  
  -- RFM Metrics (from analytics layer)
  h.days_since_last_txn,
  h.avg_monthly_txns,
  h.avg_monthly_volume,
  
  -- RFM Scores
  h.recency_score,
  h.frequency_score,
  h.monetary_score,
  
  -- Segment
  h.segment,
  
  -- Health Indicators
  h.payment_failure_rate,
  h.recent_support_tickets,
  h.total_disputes,
  h.health_score,
  
  -- Health Status (derived)
  CASE 
    WHEN h.health_score >= 70 THEN 'Healthy'
    WHEN h.health_score >= 40 THEN 'At Risk'
    ELSE 'Critical'
  END as health_status

FROM payflow_raw.customers c
LEFT JOIN payflow_analytics.customer_health h 
  ON c.customer_id = h.customer_id;
```

**Teaching point**: "We're embedding ALL the RFM analysis INTO the customer dimension. Now every query can filter by segment or health score without complex JOINs."

---

### Step 3: Create dim_payment_method

```sql
CREATE TABLE payflow_star.dim_payment_method AS

SELECT 
  payment_method as payment_method_key,
  payment_method,
  CASE 
    WHEN payment_method = 'card' THEN 'Credit/Debit Card'
    WHEN payment_method = 'bank_transfer' THEN 'Bank Transfer'
    WHEN payment_method = 'wallet' THEN 'Digital Wallet'
  END as payment_method_name
FROM (SELECT DISTINCT payment_method FROM payflow_raw.transactions);
```

---

### Step 4: Create fact_transactions

```sql
CREATE TABLE payflow_star.fact_transactions AS

SELECT 
  -- Keys (for JOINs)
  t.transaction_id,
  FORMAT_DATE('%Y%m%d', DATE(t.transaction_date)) as date_key,
  t.customer_id as customer_key,
  t.payment_method as payment_method_key,
  
  -- Degenerate dimensions (kept in fact for detail)
  t.transaction_date,
  t.status,
  t.currency,
  
  -- Measures (numeric facts)
  t.amount as transaction_amount,
  t.fee as transaction_fee,
  
  -- Calculated measures (for easier aggregation)
  CASE WHEN t.status = 'successful' THEN t.amount ELSE 0 END as successful_amount,
  CASE WHEN t.status = 'successful' THEN t.fee ELSE 0 END as fee_earned,
  CASE WHEN t.status = 'failed' THEN 1 ELSE 0 END as is_failed,
  CASE WHEN t.status = 'successful' THEN 1 ELSE 0 END as is_successful,
  CASE WHEN t.status = 'refunded' THEN 1 ELSE 0 END as is_refunded,
  CASE WHEN t.status = 'disputed' THEN 1 ELSE 0 END as is_disputed

FROM payflow_raw.transactions t;
```

---

### Step 5: Verify Star Schema

```sql
-- Test: Can we query transactions by segment?
SELECT 
  c.segment,
  COUNT(f.transaction_id) as total_txns,
  SUM(f.successful_amount) as total_volume,
  AVG(CASE WHEN f.is_failed = 1 THEN 1.0 ELSE 0 END) * 100 as failure_rate_pct
FROM payflow_star.fact_transactions f
JOIN payflow_star.dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.segment
ORDER BY total_volume DESC;
```

**Expected result**: Champions have highest volume, At Risk have elevated failure rates

---

### Query Comparison (Before vs After)

**Before** (without RFM integration):
```sql
-- Multi-schema JOINs required
SELECT c.business_name, h.segment, h.health_score
FROM payflow_raw.customers c
JOIN payflow_analytics.customer_health h ON c.customer_id = h.customer_id
WHERE h.health_score < 40;
```

**After** (with RFM in star schema):
```sql
-- Simple single-table query
SELECT business_name, segment, health_score
FROM payflow_star.dim_customer
WHERE health_score < 40;
```

---

## MODULE 6: POWER BI DASHBOARD (30 minutes)

### Connect to BigQuery

1. Power BI Desktop → Get Data → Google BigQuery
2. Sign in with Google
3. Navigate to `payflow-analytics` project
4. Select from `payflow_star`:
   - ✓ fact_transactions
   - ✓ dim_date
   - ✓ dim_customer
   - ✓ dim_payment_method
5. Also select from `payflow_raw`:
   - ✓ support_tickets (for support metrics)
6. Click Load

---

### Create Relationships

Model view:
1. fact_transactions[date_key] → dim_date[date_key] (Many-to-One)
2. fact_transactions[customer_key] → dim_customer[customer_key] (Many-to-One)
3. fact_transactions[payment_method_key] → dim_payment_method[payment_method_key] (Many-to-One)
4. support_tickets[customer_id] → dim_customer[customer_id] (Many-to-One)

Mark dim_date as date table (date column: full_date)

---

### Create Measures

```dax
// Core Metrics
Total Volume = SUM(fact_transactions[successful_amount])

Total Fees = SUM(fact_transactions[fee_earned])

Success Rate = 
DIVIDE(
    SUM(fact_transactions[is_successful]),
    COUNT(fact_transactions[transaction_id]),
    0
)

Failure Rate = 
DIVIDE(
    SUM(fact_transactions[is_failed]),
    COUNT(fact_transactions[transaction_id]),
    0
)

// RFM Metrics
Champions Count = 
CALCULATE(
    COUNTROWS(dim_customer),
    dim_customer[segment] = "Champions"
)

At Risk Count = 
CALCULATE(
    COUNTROWS(dim_customer),
    dim_customer[segment] = "At Risk"
)

Dormant Count = 
CALCULATE(
    COUNTROWS(dim_customer),
    dim_customer[segment] = "Dormant"
)

At Risk MRR = 
CALCULATE(
    SUM(dim_customer[mrr]),
    dim_customer[segment] IN {"At Risk", "Dormant"}
)

Avg Health Score = 
AVERAGE(dim_customer[health_score])

// Support Metrics
Avg Resolution Hours = 
AVERAGE(
    DATEDIFF(
        support_tickets[created_at],
        support_tickets[resolved_at],
        HOUR
    )
)
```

---

### PAGE 1: Executive Overview

**KPIs** (4 cards across top):
1. Total Volume
2. Total Fees
3. Success Rate (green if >95%, red if <90%)
4. Avg Health Score (NEW - shows overall customer health)

**Visuals**:
1. Line chart: Monthly revenue trend (dim_date[month_name] × Total Volume)
2. Donut: Transaction status distribution
3. Bar: Top 10 merchants by volume
4. Table: At-Risk merchants (filter: health_status = "At Risk" OR "Critical")

---

### PAGE 2: Payment Performance

**KPIs**:
1. Card Failure Rate
2. Bank Failure Rate
3. Wallet Failure Rate
4. Avg Transaction Value

**Visuals**:
1. Column chart: Failure rate by payment method (with 2.5% target line)
2. Line chart: Daily failure rate trend
3. Matrix: Failure rate heatmap (country × payment method)
4. Table: High-failure merchants WITH segment column (NEW - see which segments fail most)

---

### PAGE 3: Customer Health (RFM Deep Dive)

**KPIs**:
1. Champions Count
2. At Risk Count
3. Dormant Count
4. At Risk MRR

**Visuals**:
1. **Scatter chart** (PRIMARY VISUAL):
   - X-axis: dim_customer[recency_score]
   - Y-axis: dim_customer[frequency_score]
   - Size: dim_customer[avg_monthly_volume]
   - Legend/Color: dim_customer[segment]
   - Shows RFM segmentation visually

2. **Donut chart**: Customers by segment
   - Legend: dim_customer[segment]
   - Values: COUNT of customer_id

3. **Table**: Customer health scorecard
   - Columns: business_name, industry, plan, mrr, segment, health_score, payment_failure_rate, recent_support_tickets, days_since_last_txn
   - Conditional formatting: 
     - Health score: Green >70, Yellow 40-70, Red <40
     - Failure rate: Red >10%
   - Sort: health_score ascending (worst first)

4. **Bar chart**: MRR by segment
   - Shows revenue concentration

**Slicers**:
- Segment (multi-select)
- Health status (Healthy/At Risk/Critical)
- Plan

---

### PAGE 4: Support & Operations

**KPIs**:
1. Open Tickets (last 7 days)
2. Avg Resolution Time
3. Avg Satisfaction
4. Dispute Rate

**Visuals**:
1. Bar chart: Tickets by category
2. Line chart: Weekly ticket volume
3. Column chart: Satisfaction distribution
4. Table: Recent high-priority tickets WITH segment (NEW - see which segments need most support)

**NEW Visual**: Tickets by customer segment
- Shows which segments create most support load
- At Risk customers should have higher ticket rates

---

### Cross-Filtering Magic

**Key insight**: Because RFM is in dim_customer, ALL pages can filter by segment/health.

**Example workflow**:
1. User clicks "At Risk" segment on Page 3
2. Page 1 updates to show only At Risk customer volumes
3. Page 2 shows failure rates for At Risk customers only
4. Page 4 shows support tickets from At Risk customers

**This is the power of integrated star schema.**

---

## DELIVERABLES

Students complete the course with:

1. **4 CSV files** (customers, transactions, support_tickets, disputes)
2. **BigQuery star schema** with RFM embedded
3. **4-page Power BI dashboard** with full RFM integration
4. **SQL scripts**:
   - 01_setup.sql (table creation)
   - 02_eda.sql (exploratory queries)
   - 03_rfm.sql (RFM framework)
   - 04_star_schema.sql (dimensional model with RFM)
5. **Documentation**:
   - RFM framework explanation
   - Health scoring methodology
   - Dashboard user guide

---

## PORTFOLIO TALKING POINTS

"Analyzed 417K payment transactions for fintech platform processing $23M annually"

"Built dimensional data warehouse using star schema in BigQuery"

"Created RFM-based customer segmentation framework adapted for payment processing"

"Developed health scoring system with predictive churn indicators"

"Identified $2.3M in at-risk MRR using segment-based analysis"

"Designed 4-page executive dashboard with integrated customer health metrics"

---

## TIME BREAKDOWN

- Module 1: Problem Statement (15 min)
- Module 2: BigQuery Setup (10 min)
- Module 3: EDA (20 min)
- Module 4: RFM Framework (25 min)
- Module 5: Star Schema with RFM Integration (30 min)
- Module 6: Power BI Dashboard (30 min)

**Total: 130 minutes (2 hours 10 minutes)**

---

## KEY TEACHING POINTS

1. **RFM is not just theory** - it's embedded in the data model for real use
2. **Star schema enables insights** - can answer "which At Risk customers have high failures?" in one query
3. **Health scores are actionable** - <40 = call today, 40-70 = monitor, >70 = maintain
4. **Dashboard reflects reality** - every visual can slice by customer health
5. **This is production-grade** - same approach used by real fintechs

---

## SUCCESS CRITERIA

By end of course, students can:
- ✅ Explain RFM framework and why it predicts churn
- ✅ Adapt RFM to different business models (not just e-commerce)
- ✅ Write SQL to calculate RFM scores and segments
- ✅ Build star schema with analytical frameworks integrated
- ✅ Create dashboard that surfaces actionable customer insights
- ✅ Present findings to executive stakeholders

**THE GOAL**: Turn payment data into customer intelligence, intelligence into retention, retention into revenue.
