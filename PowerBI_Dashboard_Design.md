# PayFlow Analytics - Power BI Dashboard Design (WITH RFM INTEGRATION)

## Dashboard Overview

**Purpose**: Monitor payment performance, track customer health using RFM segmentation, identify churn risk  
**Users**: CEO, Operations, Customer Success  
**Data Source**: BigQuery payflow_star schema (with RFM embedded in dim_customer)

---

## DATA MODEL

### Tables Used
- `fact_transactions` (417K rows)
- `dim_date` (730 rows)
- `dim_customer` (5K rows) **← INCLUDES ALL RFM METRICS**
- `dim_payment_method` (3 rows)
- `support_tickets` (6.8K rows)

### Key Point: RFM is in dim_customer
The customer dimension includes:
- Basic attributes (business_name, industry, plan, mrr)
- RFM metrics (days_since_last_txn, avg_monthly_txns, avg_monthly_volume)
- RFM scores (recency_score, frequency_score, monetary_score)
- Segment (Champions, Loyal, Whales, At Risk, Dormant, New/Testing)
- Health metrics (health_score, health_status, payment_failure_rate, recent_support_tickets)

**This means EVERY visual can filter by segment or health status.**

---

## PAGE 1: EXECUTIVE OVERVIEW

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│  4 KPI CARDS                                                │
├─────────────────────────────────────────────────────────────┤
│  Line Chart (60%)              │  Donut Chart (40%)         │
├─────────────────────────────────────────────────────────────┤
│  Bar Chart (60%)               │  Table (40%)               │
└─────────────────────────────────────────────────────────────┘
```

### KPIs (Top Row)

**1. Total Transaction Volume**
- Measure: `SUM(fact_transactions[successful_amount])`
- Format: Currency, $23.1M
- Conditional: Trend arrow (up/down vs last month)

**2. Total Fees Earned**
- Measure: `SUM(fact_transactions[fee_earned])`
- Format: Currency, $785K
- Conditional: Trend arrow

**3. Success Rate**
- Measure: `DIVIDE(SUM(is_successful), COUNT(transaction_id))`
- Format: Percentage, 91.7%
- Conditional: Green >95%, Yellow 90-95%, Red <90%

**4. Average Health Score** (NEW - RFM METRIC)
- Measure: `AVERAGE(dim_customer[health_score])`
- Format: Whole number, 68
- Conditional: Green >75, Yellow 60-75, Red <60
- Tooltip: "Customer health based on RFM analysis"

### Visual 1: Monthly Revenue Trend
- Type: Line Chart
- X-axis: dim_date[month_name] + dim_date[year]
- Y-axis: [Total Volume]
- **NEW**: Add segment slicer to filter by customer segment
- Title: "Monthly Transaction Volume"

### Visual 2: Transaction Status Distribution
- Type: Donut Chart
- Legend: fact_transactions[status]
- Values: COUNT(transaction_id)
- Colors: successful (green), failed (red), refunded (orange), disputed (purple)

### Visual 3: Top Merchants by Volume
- Type: Clustered Bar
- Y-axis: dim_customer[business_name]
- X-axis: [Total Volume]
- **NEW**: Show dim_customer[segment] as data label or tooltip
- Top N: 10
- Sort: Descending

### Visual 4: At-Risk Customer Alert (NEW - RFM FOCUSED)
- Type: Table
- Filter: dim_customer[health_status] IN ("At Risk", "Critical")
- Columns:
  - business_name
  - segment
  - health_score
  - mrr
  - days_since_last_txn
- Sort: health_score ascending (worst first)
- Conditional: Red background if health_score < 40
- Title: "Customers Needing Immediate Attention"

### Slicers
- Date range (dim_date[full_date])
- Country (dim_customer[country])
- **NEW**: Segment (dim_customer[segment]) - multi-select

---

## PAGE 2: PAYMENT PERFORMANCE

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│  4 KPI CARDS                                                │
├─────────────────────────────────────────────────────────────┤
│  Column Chart (50%)            │  Line Chart (50%)          │
├─────────────────────────────────────────────────────────────┤
│  Matrix Heatmap (50%)          │  Table (50%)               │
└─────────────────────────────────────────────────────────────┘
```

### KPIs

**1. Card Failure Rate**
```dax
Card Failure = 
CALCULATE(
    [Failure Rate],
    dim_payment_method[payment_method] = "card"
)
```
Format: Percentage, 6.5%

**2. Bank Transfer Failure Rate**
Format: Percentage, 4.3%

**3. Wallet Failure Rate**
Format: Percentage, 3.0%

**4. At-Risk Segment Failure Rate** (NEW - RFM METRIC)
```dax
At Risk Failure = 
CALCULATE(
    [Failure Rate],
    dim_customer[segment] = "At Risk"
)
```
Format: Percentage
Purpose: Shows if At-Risk customers have higher failure rates

### Visual 1: Failure Rate by Payment Method
- Type: Clustered Column
- X-axis: dim_payment_method[payment_method_name]
- Y-axis: [Failure Rate]
- Constant line: 2.5% (industry benchmark)
- Color: Red gradient

### Visual 2: Daily Failure Trend
- Type: Line Chart
- X-axis: dim_date[full_date] (last 30 days)
- Y-axis: [Failure Rate]
- Analytics: 7-day moving average, trend line
- **NEW**: Can be filtered by segment to see failures per segment

### Visual 3: Failure Heatmap
- Type: Matrix
- Rows: dim_customer[country]
- Columns: dim_payment_method[payment_method_name]
- Values: [Failure Rate]
- Conditional formatting: Green (<2%), Yellow (2-4%), Red (>4%)

### Visual 4: High-Failure Merchants (ENHANCED WITH RFM)
- Type: Table
- Columns:
  - business_name
  - **segment** (NEW - shows which segments fail most)
  - **health_score** (NEW)
  - industry
  - total_transactions
  - failed_transactions
  - failure_rate
- Filter: failure_rate > 10% OR failed_transactions > 50
- Sort: failure_rate descending
- Conditional: Red if failure_rate > 15%
- **Insight**: See correlation between segment and failures

### Slicers
- Payment method (card/bank/wallet)
- Industry
- **NEW**: Segment (to analyze failures per segment)

---

## PAGE 3: CUSTOMER HEALTH (RFM DEEP DIVE)

**THIS IS THE PRIMARY RFM PAGE**

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│  4 KPI CARDS (all RFM-based)                               │
├─────────────────────────────────────────────────────────────┤
│  RFM Scatter Plot (60%)        │  Segment Donut (40%)       │
├─────────────────────────────────────────────────────────────┤
│  Customer Health Table (full width)                         │
└─────────────────────────────────────────────────────────────┘
```

### KPIs (All RFM Metrics)

**1. Champions Count**
```dax
Champions Count = 
CALCULATE(
    COUNTROWS(dim_customer),
    dim_customer[segment] = "Champions"
)
```
Format: Whole number
Color: Green

**2. At Risk Count**
```dax
At Risk Count = 
CALCULATE(
    COUNTROWS(dim_customer),
    dim_customer[segment] = "At Risk"
)
```
Format: Whole number
Color: Orange

**3. Dormant Count**
```dax
Dormant Count = 
CALCULATE(
    COUNTROWS(dim_customer),
    dim_customer[segment] = "Dormant"
)
```
Format: Whole number
Color: Red

**4. At-Risk MRR**
```dax
At Risk MRR = 
CALCULATE(
    SUM(dim_customer[mrr]),
    dim_customer[segment] IN {"At Risk", "Dormant"}
)
```
Format: Currency
Color: Red
Tooltip: "Revenue at risk of churn"

### Visual 1: RFM Segmentation Scatter Plot (PRIMARY VISUAL)
- Type: Scatter Chart
- **X-axis**: dim_customer[recency_score]
- **Y-axis**: dim_customer[frequency_score]
- **Size**: dim_customer[avg_monthly_volume]
- **Legend/Color**: dim_customer[segment]
- Color scheme:
  - Champions: #02C39A (green)
  - Loyal: #00A896 (teal)
  - Whales: #028090 (blue)
  - At Risk: #F9E795 (yellow)
  - Dormant: #F96167 (red)
  - New/Testing: #97BC62 (light green)
- X-axis range: 0-5
- Y-axis range: 0-5
- Title: "RFM Customer Segmentation"
- Tooltip: Add business_name, mrr, health_score

**THIS VISUAL SHOWS THE RFM FRAMEWORK VISUALLY**

### Visual 2: Customer Distribution by Segment
- Type: Donut Chart
- Legend: dim_customer[segment]
- Values: COUNT(customer_id)
- Same color scheme as scatter
- Data labels: Percentage + Count
- Title: "Customer Segments"

### Visual 3: Customer Health Scorecard (DETAILED TABLE)
- Type: Table
- Columns (in order):
  1. business_name
  2. industry
  3. plan
  4. mrr
  5. **segment** (RFM segment)
  6. **health_score** (0-100)
  7. **recency_score** (1-5)
  8. **frequency_score** (1-5)
  9. **monetary_score** (1-5)
  10. payment_failure_rate (%)
  11. recent_support_tickets (count)
  12. days_since_last_txn
- Conditional formatting:
  - **health_score**: Green >70, Yellow 40-70, Red <40
  - **segment**: Color-coded by segment
  - payment_failure_rate: Red if >10%
  - recent_support_tickets: Red if >5
- Sort: health_score ascending (show worst customers first)
- Title: "Customer Health Dashboard"

**THIS TABLE IS THE ACTIONABLE OUTPUT - CS team uses this daily**

### Visual 4: MRR by Segment (NEW)
- Type: Clustered Bar
- Y-axis: dim_customer[segment]
- X-axis: SUM(mrr)
- Sort: Descending by MRR
- Data labels: On
- Title: "MRR Distribution by Segment"

### Slicers
- **Segment** (multi-select) - PRIMARY FILTER
- Health status (Healthy/At Risk/Critical)
- Plan (Starter/Growth/Pro)
- Industry

---

## PAGE 4: SUPPORT & OPERATIONS

### Layout
```
┌─────────────────────────────────────────────────────────────┐
│  4 KPI CARDS                                                │
├─────────────────────────────────────────────────────────────┤
│  Bar Chart (50%)               │  Line Chart (50%)          │
├─────────────────────────────────────────────────────────────┤
│  Column Chart (40%)            │  Table (60%)               │
└─────────────────────────────────────────────────────────────┘
```

### KPIs

**1. Open Tickets (Last 7 Days)**
```dax
Tickets L7D = 
CALCULATE(
    COUNTROWS(support_tickets),
    support_tickets[created_at] >= TODAY() - 7
)
```

**2. Avg Resolution Time**
```dax
Avg Resolution Hours = 
AVERAGE(
    DATEDIFF(
        support_tickets[created_at],
        support_tickets[resolved_at],
        HOUR
    )
)
```
Format: Decimal, 18.5 hours

**3. Avg Satisfaction Score**
```dax
Avg Satisfaction = AVERAGE(support_tickets[satisfaction_score])
```
Format: Decimal, 3.8/5.0

**4. Dispute Rate**
```dax
Dispute Rate = 
DIVIDE(
    COUNTROWS(disputes),
    COUNTROWS(fact_transactions),
    0
)
```
Format: Percentage, 0.76%

### Visual 1: Tickets by Category
- Type: Clustered Bar
- Y-axis: support_tickets[category]
- X-axis: COUNT(ticket_id)
- Sort: Descending
- **NEW**: Color by segment (if ticket linked to customer)

### Visual 2: Ticket Volume Trend
- Type: Line Chart
- X-axis: support_tickets[created_at] by week
- Y-axis: COUNT(ticket_id)
- Analytics: 4-week moving average

### Visual 3: Satisfaction Distribution
- Type: Clustered Column
- X-axis: support_tickets[satisfaction_score] (1-5)
- Y-axis: COUNT(ticket_id)
- Color gradient: Red (1) to Green (5)

### Visual 4: Recent High-Priority Tickets (ENHANCED WITH RFM)
- Type: Table
- Columns:
  - ticket_id
  - customer business_name
  - **segment** (NEW - see which segments create tickets)
  - **health_score** (NEW)
  - category
  - priority
  - created_at
  - resolution_hours
  - satisfaction_score
- Filter: priority IN ("urgent", "high") AND created_at >= TODAY()-7
- Sort: created_at descending
- Conditional:
  - Priority urgent: Red background
  - Resolution >24h: Yellow background
  - **health_score <40: Red text**

### Visual 5: Tickets by Segment (NEW - RFM ANALYSIS)
- Type: Clustered Column
- X-axis: dim_customer[segment]
- Y-axis: COUNT(support_tickets)
- Purpose: See which segments need most support
- Expected: At Risk and Dormant should have higher ticket rates

### Slicers
- Category
- Priority
- **Segment** (NEW - filter support by customer segment)

---

## CROSS-FILTERING BEHAVIOR

**Because RFM is embedded in dim_customer, segments work across ALL pages:**

**Example User Flow**:
1. User goes to Page 3 (Customer Health)
2. User clicks "At Risk" segment in donut chart
3. **Page 1** updates: Shows only At Risk customer revenue, filters top merchants table
4. **Page 2** updates: Shows failure rates for At Risk customers only
5. **Page 4** updates: Shows support tickets from At Risk customers only

**This is the POWER of integrated star schema - segment is a dimension that filters everything.**

---

## DAX MEASURES (Complete List)

### Core Transaction Metrics
```dax
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

Avg Transaction = AVERAGE(fact_transactions[successful_amount])
```

### RFM Segment Metrics
```dax
Champions Count = 
CALCULATE(COUNTROWS(dim_customer), dim_customer[segment] = "Champions")

Loyal Count = 
CALCULATE(COUNTROWS(dim_customer), dim_customer[segment] = "Loyal")

Whales Count = 
CALCULATE(COUNTROWS(dim_customer), dim_customer[segment] = "Whales")

At Risk Count = 
CALCULATE(COUNTROWS(dim_customer), dim_customer[segment] = "At Risk")

Dormant Count = 
CALCULATE(COUNTROWS(dim_customer), dim_customer[segment] = "Dormant")

New Testing Count = 
CALCULATE(COUNTROWS(dim_customer), dim_customer[segment] = "New/Testing")
```

### Health Score Metrics
```dax
Avg Health Score = AVERAGE(dim_customer[health_score])

Healthy Count = 
CALCULATE(COUNTROWS(dim_customer), dim_customer[health_status] = "Healthy")

At Risk Status Count = 
CALCULATE(COUNTROWS(dim_customer), dim_customer[health_status] = "At Risk")

Critical Count = 
CALCULATE(COUNTROWS(dim_customer), dim_customer[health_status] = "Critical")

At Risk MRR = 
CALCULATE(
    SUM(dim_customer[mrr]),
    dim_customer[segment] IN {"At Risk", "Dormant"}
)
```

### Payment Method Specific
```dax
Card Failure = 
CALCULATE([Failure Rate], dim_payment_method[payment_method] = "card")

Bank Failure = 
CALCULATE([Failure Rate], dim_payment_method[payment_method] = "bank_transfer")

Wallet Failure = 
CALCULATE([Failure Rate], dim_payment_method[payment_method] = "wallet")
```

### Support Metrics
```dax
Tickets L7D = 
CALCULATE(
    COUNTROWS(support_tickets),
    support_tickets[created_at] >= TODAY() - 7
)

Avg Resolution Hours = 
AVERAGE(DATEDIFF(support_tickets[created_at], support_tickets[resolved_at], HOUR))

Avg Satisfaction = AVERAGE(support_tickets[satisfaction_score])
```

---

## COLOR PALETTE

### Primary Colors (Teal Trust Theme)
- Primary: #028090 (Teal)
- Secondary: #00A896 (Seafoam)
- Accent: #02C39A (Mint)

### Segment Colors (MUST USE CONSISTENTLY)
- Champions: #02C39A (Green)
- Loyal: #00A896 (Teal)
- Whales: #028090 (Blue)
- At Risk: #F9E795 (Yellow)
- Dormant: #F96167 (Red)
- New/Testing: #97BC62 (Light Green)

### Health Status Colors
- Healthy: #02C39A (Green)
- At Risk: #F9E795 (Yellow)
- Critical: #F96167 (Red)

### Transaction Status Colors
- Successful: #02C39A (Green)
- Failed: #F96167 (Red)
- Refunded: #F9E795 (Yellow)
- Disputed: #6D2E46 (Purple)

---

## DESIGN SPECIFICATIONS

### Typography
- Page title: 24pt, Bold, Navy (#1E2761)
- Visual title: 14pt, Bold, Dark Gray
- KPI value: 32pt, Bold
- KPI label: 12pt, Regular
- Body text: 11pt
- Data labels: 10pt

### Layout
- Page size: 16:9 (1920×1080)
- Margins: 20px all sides
- Visual spacing: 15px between elements
- Grid: 12-column layout

### Visual Guidelines
- Card backgrounds: White with subtle shadow
- Table alternate rows: Light gray (#F5F5F5)
- Hover effects: Enabled
- Tooltips: Enabled with additional context
- Drill-through: Enabled where applicable

---

## FINAL DELIVERABLE

Complete Power BI dashboard with:
- ✅ 4 pages (Overview, Performance, Health, Support)
- ✅ RFM segmentation fully integrated
- ✅ Customer health scoring visible throughout
- ✅ Cross-filtering enabled across all pages
- ✅ Actionable customer health table
- ✅ Executive KPIs with health metrics
- ✅ Professional design with consistent colors
- ✅ Published to Power BI Service with scheduled refresh

**This dashboard turns RFM analysis into daily operational tool.**
