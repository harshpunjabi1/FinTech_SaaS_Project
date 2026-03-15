# BigQuery Setup Instructions - PayFlow Analytics

## Prerequisites
- Google Cloud account
- BigQuery access
- 4 CSV files downloaded

---

## Step 1: Create Project

1. Go to https://console.cloud.google.com
2. Click "Select a project" → "NEW PROJECT"
3. Project name: `payflow-analytics`
4. Click CREATE

---

## Step 2: Enable BigQuery API

1. Search "BigQuery API" in console
2. Click ENABLE
3. Wait 10 seconds for activation

---

## Step 3: Create Datasets

```sql
-- Raw data layer
CREATE SCHEMA payflow_raw
OPTIONS(
  location="us"
);

-- Analytics layer
CREATE SCHEMA payflow_analytics
OPTIONS(
  location="us"
);

-- Star schema layer
CREATE SCHEMA payflow_star
OPTIONS(
  location="us"
);
```

---

## Step 4: Create Tables in payflow_raw

### customers table
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
```

### transactions table
```sql
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
```

### support_tickets table
```sql
CREATE TABLE payflow_raw.support_tickets (
  ticket_id STRING,
  customer_id STRING,
  created_at TIMESTAMP,
  resolved_at TIMESTAMP,
  category STRING,
  priority STRING,
  satisfaction_score INT64
);
```

### disputes table
```sql
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

---

## Step 5: Load CSV Data

### Method: BigQuery Console Upload

For each table:

1. Click on table name in Explorer
2. Click "+" or "Create table"
3. Source: Upload
4. Select file: Choose corresponding CSV
   - `customers.csv` → `customers` table
   - `transactions.csv` → `transactions` table
   - `support_tickets.csv` → `support_tickets` table
   - `disputes.csv` → `disputes` table
5. File format: CSV
6. **Important**: 
   - Auto-detect schema: ✓
   - Header rows to skip: 1
7. Click CREATE TABLE
8. Wait for upload (transactions may take 2-3 minutes)

---

## Step 6: Verify Data Loaded

```sql
SELECT 
  'customers' as table_name, 
  COUNT(*) as row_count
FROM payflow_raw.customers

UNION ALL

SELECT 
  'transactions', 
  COUNT(*)
FROM payflow_raw.transactions

UNION ALL

SELECT 
  'support_tickets', 
  COUNT(*)
FROM payflow_raw.support_tickets

UNION ALL

SELECT 
  'disputes', 
  COUNT(*)
FROM payflow_raw.disputes;
```

**Expected Results:**
- customers: 5,000
- transactions: ~417,000
- support_tickets: ~6,800
- disputes: ~3,100

---

## Step 7: Test Query

```sql
SELECT 
  status,
  COUNT(*) as count,
  ROUND(SUM(amount), 2) as total_amount
FROM payflow_raw.transactions
GROUP BY status
ORDER BY count DESC;
```

Should return successful, failed, refunded, disputed with counts.

---

## Troubleshooting

### Error: "Schema mismatch"
- Solution: Delete table, recreate with auto-detect enabled

### Error: "Permission denied"
- Solution: Check you're logged in with correct Google account

### Upload very slow
- Normal for transactions.csv (30 MB, 417K rows)
- Takes 2-5 minutes

### Query quota exceeded
- Unlikely - dataset is small
- Free tier: 1 TB query processing/month
- This course uses <1 GB total

---

## Cost Information

**This project stays in free tier:**
- Storage: ~35 MB total (free up to 10 GB)
- Queries: <500 MB processed (free up to 1 TB)
- **Total cost: $0**

---

## Ready for Course

Once all 4 tables show correct row counts, you're ready for Module 3: Exploratory Data Analysis!
