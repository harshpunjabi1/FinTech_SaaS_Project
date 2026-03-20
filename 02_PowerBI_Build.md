# Power BI Dashboard Build - Complete Steps

## CONNECT & MODEL (10 MIN)

1. Power BI Desktop → Get Data → Google BigQuery
2. Sign in
3. Select: fact_transactions, dim_customer, dim_date, dim_payment_method
4. Load

5. Model View:
   - Drag fact_transactions[date_key] → dim_date[date_key]
   - Drag fact_transactions[customer_key] → dim_customer[customer_key]  
   - Drag fact_transactions[payment_method_key] → dim_payment_method[payment_method_key]
   - Right-click dim_date → Mark as date table → full_date

6. Create _Measures table:
   - Home → Enter Data → Name: _Measures
   - Create column "x" → Load

## CREATE MEASURES (5 MIN)

Click _Measures → New Measure:

```dax
Total Volume USD = SUM(fact_transactions[successful_amount_usd])
```

```dax
Success Rate = DIVIDE(SUM(fact_transactions[is_successful]), COUNT(fact_transactions[transaction_id]), 0)
```

```dax
Failure Rate = DIVIDE(SUM(fact_transactions[is_failed]), COUNT(fact_transactions[transaction_id]), 0)
```

```dax
Avg Health Score = AVERAGE(dim_customer[health_score])
```

```dax
At Risk MRR = CALCULATE(SUM(dim_customer[mrr]), dim_customer[segment] = "At Risk")
```

## BUILD PAGE (30 MIN)

### KPI 1: Total Volume
1. Insert → Card
2. Drag [Total Volume USD] to Fields
3. Position: Top-left (0.5", 0.5")
4. Size: 2.3" × 1"
5. Format → Callout value:
   - Display units: Millions
   - Decimal places: 1
   - Font: 32pt Bold
6. Format → Category label:
   - Text: "Total Volume (USD)"
   - Font: 12pt

### KPI 2: Success Rate
1. Insert → Card
2. Field: [Success Rate]
3. Position: (3.1", 0.5")
4. Format → Callout value:
   - Value: Percentage
   - Decimal: 1
5. Conditional formatting:
   - Callout value → Background color → Rules
   - If >= 0.95: Green (#02C39A)
   - If >= 0.90: Yellow (#F9E795)
   - Else: Red (#F96167)

### KPI 3: Avg Health Score
1. Insert → Card
2. Field: [Avg Health Score]
3. Position: (5.7", 0.5")
4. Format: Whole number
5. Label: "Customer Health"

### KPI 4: At Risk MRR
1. Insert → Card
2. Field: [At Risk MRR]
3. Position: (8.3", 0.5")
4. Format: Currency, thousands
5. Callout value color: Red

### Line Chart: Revenue Trend
1. Insert → Line chart
2. Position: (0.5", 2.0"), Size: (5", 3")
3. X-axis: dim_date[month_name]
4. Y-axis: [Total Volume USD]
5. Format:
   - Title: "Monthly Revenue Trend"
   - Data labels: On
   - Y-axis: Currency
   - Line color: #028090

### Donut: Transaction Status
1. Insert → Donut chart
2. Position: (5.8", 2.0"), Size: (4.7", 3")
3. Legend: fact_transactions[status]
4. Values: COUNT of transaction_id
5. Format → Data colors:
   - successful: #02C39A
   - failed: #F96167
   - refunded: #F9E795
   - disputed: #6D2E46
6. Data labels: Category + Percentage

### Column Chart: Failure by Method
1. Insert → Clustered column chart
2. Position: (0.5", 5.3"), Size: (5", 2.5")
3. X-axis: dim_payment_method[payment_method_name]
4. Y-axis: [Failure Rate]
5. Format:
   - Y-axis: Percentage
   - Data labels: On
   - Columns: Red (#F96167)
6. Analytics → Constant line:
   - Value: 0.025
   - Name: "Benchmark"
   - Color: Orange
   - Style: Dashed

### Scatter: RFM Segmentation
1. Insert → Scatter chart
2. Position: (5.8", 5.3"), Size: (4.7", 2.5")
3. X-axis: dim_customer[recency_score]
4. Y-axis: dim_customer[frequency_score]
5. Size: dim_customer[avg_monthly_volume]
6. Legend: dim_customer[segment]
7. Format → Data colors:
   - Champions: #02C39A
   - Loyal: #00A896
   - Whales: #028090
   - At Risk: #F96167
   - Dormant: #B85042
   - New/Testing: #97BC62
8. X/Y axis: Range 0-5

### Table: At-Risk Customers
1. Insert → Table
2. Position: (0.5", 8.2"), Size: (9.5", 2.3")
3. Columns: business_name, segment, health_score, mrr, recency_score, frequency_score, monetary_score, payment_failure_rate, recent_support_tickets
4. Filters pane → Add filter:
   - health_score is less than 40
5. Sort: health_score ascending
6. Conditional formatting → health_score:
   - Background color:
     - <40: Red
     - 40-69: Yellow
     - >=70: Green

### Slicers
1. Insert → Slicer
2. Field: dim_date[full_date]
3. Position: (11", 0.5")
4. Slicer settings: Between
5. Style: Dropdown

6. Insert → Slicer
7. Field: dim_customer[segment]
8. Position: (11", 2.5")
9. Style: Dropdown (multi-select)

## TEST (5 MIN)

1. Click "At Risk" in scatter plot
2. Verify: All visuals filter to At Risk customers
3. Reset
4. Use date slicer
5. Verify: All visuals update

DONE.
