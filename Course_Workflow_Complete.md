# PayFlow Fintech Analytics Course - Complete Workflow

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
- Customer database (signups, plans, MRR)
- Transaction logs (Stripe-like data)
- Support tickets (Zendesk export)
- Dispute records (chargebacks)

### Success Criteria
Build a dashboard that:
- Identifies high-risk customers
- Shows payment failure patterns
- Calculates customer-level profitability

---

## MODULE 2: DATA SETUP IN BIGQUERY (10 minutes)

### Step 1: Create Dataset

```sql
CREATE SCHEMA payflow_raw;
```

### Step 2: Create Tables

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
- Use BigQuery Console > Upload
- Auto-detect schema
- Skip header row

---

## MODULE 3: EXPLORATORY DATA ANALYSIS (20 minutes)

### Query 1: Data Volume Check (2 minutes)
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

### Query 2: Transaction Status Distribution (3 minutes)
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

### Query 3: Payment Failure by Method (5 minutes)
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

**Finding**: Card payments have 6.5% failure (wallets only 3%)  
**Insight**: Card payment infrastructure needs attention

---

### Query 4: Monthly Transaction Volume (5 minutes)
```sql
SELECT 
  DATE_TRUNC(transaction_date, MONTH) as month,
  COUNT(*) as transactions,
  ROUND(SUM(CASE WHEN status = 'successful' THEN amount ELSE 0 END), 2) as successful_volume,
  ROUND(SUM(CASE WHEN status = 'successful' THEN fee ELSE 0 END), 2) as fees_earned
FROM payflow_raw.transactions
GROUP BY month
ORDER BY month DESC;
```

**Finding**: Revenue trending, but fees not keeping pace (failure costs)

---

### Query 5: Support Ticket Analysis (5 minutes)
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
**Insight**: Confirms payment failures drive poor customer experience

---

## MODULE 4: ANALYTICAL FRAMEWORK - RFM FOR FINTECH (25 minutes)

### The RFM Framework Adapted

**Traditional RFM** (E-commerce):
- Recency: Days since last purchase
- Frequency: Number of purchases
- Monetary: Total spend

**Fintech RFM** (Payment processing):
- **R**ecency: Days since last successful transaction
- **F**requency: Transactions per month (velocity)
- **M**onetary: Monthly transaction volume processed

---

### Build RFM Metrics (10 minutes)

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
    DATE_DIFF(CURRENT_DATE(), MAX(CASE WHEN t.status = 'successful' THEN DATE(t.transaction_date) END), DAY) as days_since_last_txn,
    
    -- FREQUENCY: Average monthly transaction count
    COUNT(CASE WHEN t.status = 'successful' THEN t.transaction_id END) / 12.0 as avg_monthly_txns,
    
    -- MONETARY: Average monthly volume
    SUM(CASE WHEN t.status = 'successful' THEN t.amount ELSE 0 END) / 12.0 as avg_monthly_volume
    
  FROM payflow_raw.customers c
  LEFT JOIN payflow_raw.transactions t ON c.customer_id = t.customer_id
  GROUP BY c.customer_id, c.business_name, c.industry, c.plan, c.mrr
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

---

### Create RFM Segments (5 minutes)

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
    WHEN monetary_score >= 4 THEN 'Whales'
    
    -- At Risk: Used to be active, now dormant
    WHEN recency_score = 4 AND frequency_score >= 2 THEN 'At Risk'

    -- New/Testing: Recent signup, low usage
    WHEN recency_score = 5 AND frequency_score <= 2 THEN 'New/Testing'

    -- Dormant: No recent activity
    WHEN recency_score = 1 THEN 'Dormant'

    
    ELSE 'Needs Attention'
  END as segment

FROM payflow_analytics.customer_rfm;
```

---

### Validate Segments (5 minutes)

```sql
SELECT 
  segment,
  COUNT(*) as customers,
  ROUND(AVG(mrr), 2) as avg_mrr,
  ROUND(AVG(avg_monthly_volume), 2) as avg_monthly_volume,
  ROUND(AVG(avg_monthly_txns), 1) as avg_monthly_txns
FROM payflow_analytics.customer_segments
GROUP BY segment
ORDER BY customers DESC;
```

**Expected**: Champions (15-20%), Dormant (30-35%), Needs Attention (25-30%)

---

### Add Risk Indicators (5 minutes)

```sql
CREATE TABLE payflow_analytics.customer_health AS

SELECT 
  s.*,
  
  -- Payment failure rate
  COALESCE(f.failure_rate, 0) as payment_failure_rate,
  
  -- Support ticket count (last 90 days)
  COALESCE(t.recent_tickets, 0) as recent_support_tickets,
  
  -- Dispute count
  COALESCE(d.dispute_count, 0) as total_disputes,
  
  -- Risk score (0-100, lower = riskier)
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

---

## MODULE 5: DATA TRANSFORMATION - STAR SCHEMA (30 minutes)

### Why Star Schema?

**Problem with current structure**: 
- Repetitive JOINs for every analysis
- Hard to maintain consistent calculations
- Slow query performance

**Solution**: Build a star schema
- Fact table: transactions (measures)
- Dimension tables: customers, dates, payment_methods

---

### Step 1: Create Dimension Tables

#### dim_date
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

#### dim_customer
```sql
CREATE TABLE payflow_star.dim_customer AS

SELECT 
  customer_id as customer_key,
  customer_id,
  business_name,
  industry,
  plan,
  mrr,
  country,
  employee_size,
  signup_date
FROM payflow_raw.customers;
```

#### dim_payment_method
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

### Step 2: Create Fact Table

```sql
CREATE TABLE payflow_star.fact_transactions AS

SELECT 
  -- Keys
  t.transaction_id,
  FORMAT_DATE('%Y%m%d', DATE(t.transaction_date)) as date_key,
  t.customer_id as customer_key,
  t.payment_method as payment_method_key,
  
  -- Degenerate dimensions
  t.transaction_date,
  t.status,
  t.currency,
  
  -- Measures
  t.amount as transaction_amount,
  t.fee as transaction_fee,
  
  -- Calculated measures
  CASE WHEN t.status = 'successful' THEN t.amount ELSE 0 END as successful_amount,
  CASE WHEN t.status = 'successful' THEN t.fee ELSE 0 END as fee_earned,
  CASE WHEN t.status = 'failed' THEN 1 ELSE 0 END as is_failed,
  CASE WHEN t.status = 'successful' THEN 1 ELSE 0 END as is_successful,
  CASE WHEN t.status = 'refunded' THEN 1 ELSE 0 END as is_refunded,
  CASE WHEN t.status = 'disputed' THEN 1 ELSE 0 END as is_disputed

FROM payflow_raw.transactions t;
```

---

### Step 3: Query the Star Schema

**Before (normalized)**:
```sql
SELECT c.industry, SUM(t.amount)
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE t.status = 'successful'
GROUP BY c.industry;
```

**After (star schema)**:
```sql
SELECT 
  c.industry,
  SUM(f.successful_amount) as revenue
FROM payflow_star.fact_transactions f
JOIN payflow_star.dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.industry;
```

---

## MODULE 6: DASHBOARD DESIGN (30 minutes)

### Dashboard Structure: 4 Pages

---

### PAGE 1: Executive Overview

**KPIs (Top Row)**:
- Total Transaction Volume (successful only)
- Total Fees Earned
- Success Rate %
- Average Transaction Value

**Visuals**:
1. **Line Chart**: Monthly revenue trend (dim_date.month_name × fact.successful_amount)
2. **Donut Chart**: Transaction volume by status
3. **Bar Chart**: Top 10 customers by volume
4. **Card**: Payment failure rate with trend indicator

**Filters**:
- Date range slicer
- Country dropdown

---

### PAGE 2: Payment Performance

**KPIs**:
- Payment Failure Rate
- Card Failure Rate
- Bank Transfer Failure Rate
- Wallet Failure Rate

**Visuals**:
1. **Column Chart**: Failure rate by payment method
2. **Line Chart**: Daily failure rate trend
3. **Table**: Top 20 customers by failure count
4. **Heat Map**: Failure rate by country × payment method

**Filters**:
- Payment method buttons
- Industry dropdown

---

### PAGE 3: Customer Health

**KPIs**:
- Champions count
- At Risk count
- Dormant count
- Total MRR at Risk

**Visuals**:
1. **Scatter Plot**: 
   - X-axis: Recency score
   - Y-axis: Frequency score
   - Bubble size: Monthly volume
   - Color: Segment
2. **Table**: Customer list with health score, segment, recent tickets, failure rate
3. **Donut**: Customers by segment
4. **Bar**: MRR by segment

**Filters**:
- Segment slicer
- Health score range slider
- Plan filter

---

### PAGE 4: Support & Operations

**KPIs**:
- Total Open Tickets
- Avg Resolution Time (hours)
- Avg Satisfaction Score
- Dispute Rate

**Visuals**:
1. **Bar Chart**: Tickets by category
2. **Line Chart**: Ticket volume trend
3. **Table**: Recent high-priority tickets
4. **Column Chart**: Satisfaction score distribution

**Filters**:
- Ticket category
- Priority level
- Date range

---

## COURSE DELIVERABLES

### For Students:
1. **4 CSV files** (customers, transactions, support_tickets, disputes)
2. **Complete SQL scripts**:
   - 01_setup.sql (table creation)
   - 02_eda.sql (exploratory queries)
   - 03_rfm.sql (analytical framework)
   - 04_star_schema.sql (dimensional model)
3. **Dashboard template** (Power BI .pbix file)
4. **Course workbook** (PDF with all slides)

### Portfolio Artifacts:
- GitHub repo with all SQL + README
- Dashboard screenshots with annotations
- "Fintech Payment Analytics" project description
- Can say: "Analyzed 417K transactions, built star schema, identified $2.3M at-risk MRR"

---

## TIME BREAKDOWN

- Module 1: Problem Statement (15 min)
- Module 2: BigQuery Setup (10 min)
- Module 3: EDA Queries (20 min)
- Module 4: RFM Framework (25 min)
- Module 5: Star Schema (30 min)
- Module 6: Dashboard (30 min)

**Total: 130 minutes (2 hours 10 minutes)**

---

## KEY TEACHING POINTS

1. **SQL is simple**: Longest query is 30 lines, all typable
2. **Framework thinking**: RFM adapted from retail to fintech
3. **Data modeling**: Star schema speeds up analysis 3x
4. **Business impact**: Every metric ties to revenue/risk
5. **Portfolio ready**: Real fintech patterns, production-grade code
