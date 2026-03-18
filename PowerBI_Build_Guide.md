# Power BI Dashboard Build Guide - PayFlow Analytics (WITH RFM)

## PREREQUISITES
- Power BI Desktop installed
- BigQuery star schema created (with RFM in dim_customer)
- Google Cloud credentials

---

## PART 1: CONNECT & MODEL (15 minutes)

### Connect to BigQuery
1. Power BI Desktop → Get Data → Google BigQuery
2. Sign in with Google account
3. Navigate to `payflow-analytics` project
4. **Select from payflow_star**:
   - ✓ fact_transactions
   - ✓ dim_date  
   - ✓ dim_customer (**includes ALL RFM fields**)
   - ✓ dim_payment_method
5. **Select from payflow_raw**:
   - ✓ support_tickets
6. Click "Load" (wait 60 seconds)

### Create Relationships (Model View)
1. fact_transactions[date_key] → dim_date[date_key] (Many-to-One)
2. fact_transactions[customer_key] → dim_customer[customer_key] (Many-to-One)
3. fact_transactions[payment_method_key] → dim_payment_method[payment_method_key] (Many-to-One)
4. support_tickets[customer_id] → dim_customer[customer_id] (Many-to-One)

Mark dim_date as date table (date column: full_date)

### Verify RFM Fields in dim_customer
Expand dim_customer in Fields pane - should see:
- ✓ recency_score
- ✓ frequency_score
- ✓ monetary_score
- ✓ segment
- ✓ health_score
- ✓ health_status
- ✓ payment_failure_rate
- ✓ recent_support_tickets

**If these aren't there, your star schema wasn't built correctly. Go back to BigQuery.**

---

## PART 2: CREATE MEASURES (10 minutes)

Create new table for measures:
1. Home → Enter Data
2. Name: `_Measures`
3. Add one column "Placeholder" with value "x"
4. Load

Now create measures (click _Measures, then New Measure):

```dax
// CORE METRICS
Total Volume = SUM(fact_transactions[successful_amount])

Total Fees = SUM(fact_transactions[fee_earned])

Success Rate = DIVIDE(SUM(fact_transactions[is_successful]), COUNT(fact_transactions[transaction_id]), 0)

Failure Rate = DIVIDE(SUM(fact_transactions[is_failed]), COUNT(fact_transactions[transaction_id]), 0)

Avg Transaction = AVERAGE(fact_transactions[successful_amount])

// RFM SEGMENT COUNTS
Champions Count = CALCULATE(COUNTROWS(dim_customer), dim_customer[segment] = "Champions")

Loyal Count = CALCULATE(COUNTROWS(dim_customer), dim_customer[segment] = "Loyal")

At Risk Count = CALCULATE(COUNTROWS(dim_customer), dim_customer[segment] = "At Risk")

Dormant Count = CALCULATE(COUNTROWS(dim_customer), dim_customer[segment] = "Dormant")

// HEALTH METRICS
Avg Health Score = AVERAGE(dim_customer[health_score])

At Risk MRR = CALCULATE(SUM(dim_customer[mrr]), dim_customer[segment] IN {"At Risk", "Dormant"})

// PAYMENT METHOD SPECIFIC
Card Failure = CALCULATE([Failure Rate], dim_payment_method[payment_method] = "card")

Bank Failure = CALCULATE([Failure Rate], dim_payment_method[payment_method] = "bank_transfer")

Wallet Failure = CALCULATE([Failure Rate], dim_payment_method[payment_method] = "wallet")

// SUPPORT METRICS
Avg Resolution Hours = AVERAGE(DATEDIFF(support_tickets[created_at], support_tickets[resolved_at], HOUR))

Avg Satisfaction = AVERAGE(support_tickets[satisfaction_score])

Tickets L7D = CALCULATE(COUNTROWS(support_tickets), support_tickets[created_at] >= TODAY()-7)
```

---

## PART 3: PAGE 1 - EXECUTIVE OVERVIEW (15 minutes)

### KPI Cards (4 across top)

**Card 1: Total Volume**
- Visual: Card
- Field: [Total Volume]
- Position: (0.5", 0.5"), Size: (2.3", 1")
- Format: Currency, millions, 1 decimal
- Label: "Total Transaction Volume"

**Card 2: Total Fees**
- Duplicate Card 1
- Field: [Total Fees]
- Position: (3.1", 0.5")
- Format: Currency, thousands
- Label: "Total Fees Earned"

**Card 3: Success Rate**
- Field: [Success Rate]
- Position: (5.7", 0.5")
- Format: Percentage, 1 decimal
- Conditional formatting:
  - Rules: If >= 0.95 → Green, >= 0.90 → Yellow, < 0.90 → Red

**Card 4: Avg Health Score (RFM)**
- Field: [Avg Health Score]
- Position: (8.3", 0.5")
- Format: Whole number
- Conditional: >= 75 Green, >= 60 Yellow, < 60 Red
- Label: "Avg Customer Health"

### Line Chart: Monthly Revenue
- Position: (0.5", 2.0"), Size: (6", 3")
- X-axis: dim_date[month_name], dim_date[year]
- Y-axis: [Total Volume]
- Title: "Monthly Transaction Volume"
- Data labels: On

### Donut: Transaction Status
- Position: (7.0", 2.0"), Size: (3.5", 3")
- Legend: fact_transactions[status]
- Values: COUNT(transaction_id)
- Colors: successful #02C39A, failed #F96167, refunded #F9E795, disputed #6D2E46

### Bar Chart: Top Merchants
- Position: (0.5", 5.5"), Size: (6", 2.5")
- Y-axis: dim_customer[business_name]
- X-axis: [Total Volume]
- Top N filter: 10
- **Add tooltip**: Show dim_customer[segment]

### Table: At-Risk Customers (RFM)
- Position: (7.0", 5.5"), Size: (3.5", 2.5")
- Filter: dim_customer[health_status] IN ("At Risk", "Critical")
- Columns:
  - business_name
  - segment
  - health_score
  - mrr
- Conditional: health_score < 40 → Red background
- Sort: health_score ascending

### Slicers
- Date range: (11", 0.5"), between slicer
- Country: (11", 2.5"), dropdown
- **Segment (RFM)**: (11", 4.5"), dropdown multi-select

---

## PART 4: PAGE 2 - PAYMENT PERFORMANCE (15 minutes)

### KPIs
1. [Card Failure] - Position: (0.5", 0.5")
2. [Bank Failure] - Position: (3.1", 0.5")
3. [Wallet Failure] - Position: (5.7", 0.5")
4. [Avg Transaction] - Position: (8.3", 0.5")

### Column Chart: Failure by Method
- Position: (0.5", 2.0"), Size: (5", 3")
- X-axis: dim_payment_method[payment_method_name]
- Y-axis: [Failure Rate]
- Analytics → Constant line: 0.025 (2.5% benchmark), orange
- Title: "Payment Failure Rate by Method"

### Line Chart: Daily Failures
- Position: (6.0", 2.0"), Size: (5", 3")
- X-axis: dim_date[full_date]
- Y-axis: [Failure Rate]
- Filter: Last 30 days
- Analytics: Average line, Trend line
- Title: "Daily Failure Rate Trend"

### Matrix: Heatmap
- Position: (0.5", 5.5"), Size: (5", 3")
- Rows: dim_customer[country]
- Columns: dim_payment_method[payment_method_name]
- Values: [Failure Rate]
- Conditional: < 0.02 Green, 0.02-0.04 Yellow, > 0.04 Red
- Title: "Failure Rate by Country × Method"

### Table: High-Failure Merchants (WITH RFM)
- Position: (6.0", 5.5"), Size: (5", 3")
- Columns:
  - business_name
  - **segment** (RFM)
  - **health_score**
  - industry
  - COUNT(fact_transactions) → "Total Txns"
  - SUM(is_failed) → "Failed Txns"
  - [Failure Rate]
- Filter: [Failure Rate] > 0.10
- Sort: [Failure Rate] descending
- Conditional: Failure Rate > 0.15 → Red background

---

## PART 5: PAGE 3 - CUSTOMER HEALTH (RFM PAGE) (20 minutes)

**THIS IS THE MAIN RFM PAGE**

### KPIs (All RFM)
1. [Champions Count] - Green card
2. [At Risk Count] - Yellow card
3. [Dormant Count] - Red card
4. [At Risk MRR] - Red card, currency

### Scatter Chart: RFM Visualization (MAIN VISUAL)
- Position: (0.5", 2.0"), Size: (6.5", 4")
- **X-axis**: dim_customer[recency_score]
- **Y-axis**: dim_customer[frequency_score]
- **Size**: dim_customer[avg_monthly_volume]
- **Legend**: dim_customer[segment]
- Colors (CRITICAL - match exactly):
  - Champions: #02C39A
  - Loyal: #00A896
  - Whales: #028090
  - At Risk: #F9E795
  - Dormant: #F96167
  - New/Testing: #97BC62
- X/Y axis range: 0-5
- Title: "RFM Customer Segmentation"
- Tooltip: Add business_name, mrr, health_score

### Donut: Segment Distribution
- Position: (7.5", 2.0"), Size: (3.5", 4")
- Legend: dim_customer[segment]
- Values: COUNT(customer_id)
- Same colors as scatter
- Data labels: Percentage + Count
- Title: "Customer Segments"

### Table: Customer Health Scorecard
- Position: (0.5", 6.5"), Size: (10.5", 3")
- Columns:
  - business_name → "Business"
  - industry
  - plan
  - mrr → "MRR"
  - **segment** → "Segment"
  - **health_score** → "Health"
  - **recency_score** → "R"
  - **frequency_score** → "F"
  - **monetary_score** → "M"
  - payment_failure_rate → "Failure %"
  - recent_support_tickets → "Tickets"
  - days_since_last_txn → "Days Since Last Txn"
- Conditional formatting:
  - health_score: >70 Green, 40-70 Yellow, <40 Red
  - payment_failure_rate: >0.10 Red
  - recent_support_tickets: >5 Red
- Sort: health_score ascending (worst first)
- Title: "Customer Health Dashboard"

**THIS TABLE IS THE ACTIONABLE OUTPUT**

### Slicers
- Segment: (11", 0.5"), multi-select
- Health Status: (11", 3"), dropdown
- Plan: (11", 5"), dropdown

---

## PART 6: PAGE 4 - SUPPORT & OPERATIONS (15 minutes)

### KPIs
1. [Tickets L7D]
2. [Avg Resolution Hours]
3. [Avg Satisfaction]
4. Dispute Rate (create: `DIVIDE(COUNTROWS(disputes), COUNTROWS(fact_transactions))`)

### Bar Chart: Tickets by Category
- Position: (0.5", 2.0"), Size: (5", 3")
- Y-axis: support_tickets[category]
- X-axis: COUNT(ticket_id)
- Sort: Descending
- Title: "Support Tickets by Category"

### Line Chart: Ticket Trend
- Position: (6.0", 2.0"), Size: (5", 3")
- X-axis: support_tickets[created_at] (by week)
- Y-axis: COUNT(ticket_id)
- Analytics: 4-week MA
- Title: "Weekly Ticket Volume"

### Column Chart: Satisfaction
- Position: (0.5", 5.5"), Size: (4", 3")
- X-axis: support_tickets[satisfaction_score]
- Y-axis: COUNT(ticket_id)
- Colors: Gradient red (1) to green (5)
- Title: "Satisfaction Score Distribution"

### Table: Recent High-Priority (WITH RFM)
- Position: (5.0", 5.5"), Size: (6", 3")
- Columns:
  - ticket_id
  - business_name (from dim_customer)
  - **segment** (RFM)
  - **health_score**
  - category
  - priority
  - created_at
  - [Avg Resolution Hours]
  - satisfaction_score
- Filter: priority IN ("urgent", "high") AND created_at >= TODAY()-7
- Sort: created_at descending
- Conditional:
  - priority "urgent" → Red background
  - Resolution >24h → Yellow
  - health_score <40 → Red text

---

## PART 7: FORMATTING & POLISH (10 minutes)

### Apply Theme
View → Themes → Custom:
- Primary: #028090
- Accent: #02C39A
- Text: #2F3C7E
- Background: #F5F5F5

### Add Page Navigation
1. Insert → Buttons → Blank (create 4 buttons)
2. Text: "Overview | Performance | Health | Support"
3. Actions:
   - Button 1 → Page navigation → Page 1
   - Button 2 → Page 2
   - Button 3 → Page 3
   - Button 4 → Page 4
4. Copy buttons to all pages

### Sync Slicers
1. View → Sync slicers
2. Select Date Range slicer
3. Check "Sync" for all pages
4. Repeat for Segment slicer

---

## PART 8: TESTING RFM INTEGRATION (10 minutes)

### Test Cross-Filtering
1. Go to Page 3
2. Click "At Risk" segment in donut chart
3. **Verify**:
   - Page 1: KPIs update to show At Risk metrics only
   - Page 2: Failure rates filtered to At Risk customers
   - Page 3: Scatter plot highlights At Risk segment
   - Page 4: Support tickets filtered to At Risk customers

### Test Health Score
1. Page 3 → Customer Health table
2. Sort by health_score ascending
3. **Verify**: Customers with score <40 show red background
4. Click on a Critical customer
5. **Verify**: All pages filter to show that customer's data

### Test Segment Colors
1. Page 3 → Scatter plot
2. **Verify each segment has correct color**:
   - Champions = Green (#02C39A)
   - At Risk = Yellow (#F9E795)
   - Dormant = Red (#F96167)
3. Donut chart should match scatter plot colors

---

## PART 9: PUBLISH & SHARE (5 minutes)

### Publish to Service
1. File → Save as `PayFlow_Analytics_RFM.pbix`
2. Home → Publish
3. Sign in to Power BI Service
4. Select workspace: "PayFlow Analytics"
5. Click "Select"
6. Wait for upload

### Configure Refresh
1. Go to app.powerbi.com
2. Navigate to workspace → Datasets
3. Find "PayFlow_Analytics_RFM" → Settings
4. Scheduled refresh:
   - Frequency: Daily
   - Time: 6:00 AM
5. Data source credentials: Enter BigQuery credentials
6. Test connection → Apply

### Share Dashboard
1. Create App from workspace
2. Name: "PayFlow Customer Health Dashboard"
3. Include all 4 pages
4. Publish
5. Share link with executives

---

## VERIFICATION CHECKLIST

Before presenting to stakeholders:

### Data Verification
- [ ] All 5 tables loaded (fact + 3 dims + support)
- [ ] Relationships active and correct
- [ ] dim_customer contains RFM fields
- [ ] All measures calculate correctly
- [ ] Date slicer works across all pages

### RFM Integration
- [ ] Scatter plot shows all 6 segments
- [ ] Segment colors consistent across all visuals
- [ ] Health score conditional formatting works
- [ ] Cross-filtering works (click segment → all pages filter)
- [ ] Customer health table sortable by health_score

### Visual Quality
- [ ] All titles clear and descriptive
- [ ] No overlapping text
- [ ] Data labels readable
- [ ] Colors match design spec
- [ ] Mobile layout created (optional)

### Performance
- [ ] All pages load <3 seconds
- [ ] No errors in DAX measures
- [ ] Filters respond quickly
- [ ] Export to PDF works

---

## TROUBLESHOOTING

### Issue: RFM fields not in dim_customer
**Solution**: Your BigQuery star schema wasn't built correctly. Go back to Module 5 and rebuild dim_customer with RFM integration.

### Issue: Scatter plot shows no data
**Solution**: Check filters. Make sure recency_score and frequency_score are not null. Filter dim_customer WHERE recency_score IS NOT NULL.

### Issue: Segment colors don't match
**Solution**: Manually set colors in scatter plot:
- Data colors → Advanced controls → Select each segment → Set hex code

### Issue: Cross-filtering not working
**Solution**: Check relationships. All should be Many-to-One with Single direction except dim_customer which can be Both.

### Issue: Health score shows wrong values
**Solution**: Verify health_score column exists in dim_customer and contains values 0-100. If not, rebuild customer_health table in BigQuery.

---

## FINAL DELIVERABLE

You now have:
- ✅ 4-page interactive dashboard
- ✅ RFM segmentation fully integrated
- ✅ Customer health scoring visible
- ✅ Cross-filtering enabled across pages
- ✅ Actionable customer health table
- ✅ Published to Power BI Service
- ✅ Scheduled daily refresh

**Dashboard is ready for executive presentation.**

---

## NEXT STEPS

1. Train customer success team on health table
2. Set up alerts for health_score <40 customers
3. Weekly review of At Risk segment
4. Monthly segment migration analysis
5. Quarterly RFM threshold adjustment

**The dashboard is now an operational tool, not just a report.**
