# RFM Framework for Fintech - Complete Documentation

## WHAT IS RFM?

RFM is a customer segmentation technique that scores customers based on three behavioral metrics:

- **R**ecency: How recently did the customer interact?
- **F**requency: How often do they interact?
- **M**onetary: How much value do they generate?

Each metric is scored 1-5 (5 = best), creating a composite RFM score.

---

## WHY RFM FOR FINTECH?

**Traditional use**: E-commerce (Amazon, retail)
- Recency: Days since last purchase
- Frequency: Number of orders
- Monetary: Total spend

**PayFlow adaptation**: Payment processing platform
- Recency: Days since last successful transaction
- Frequency: Transactions processed per month
- Monetary: Monthly transaction volume

**Why it matters**: 
- Predicts churn before it happens
- Identifies high-value customers to protect
- Finds dormant accounts to re-engage
- Prioritizes customer success resources

---

## THE RFM METRICS FOR PAYFLOW

### RECENCY SCORE

**What we measure**: Days since last successful transaction

**Why it matters**: 
- Recent activity = engaged customer
- No recent activity = at risk of churn
- Payment processors live or die by transaction volume

**Scoring logic**:
```
Score 5: Last transaction ≤ 7 days ago (highly engaged)
Score 4: Last transaction 8-30 days ago (active)
Score 3: Last transaction 31-60 days ago (moderate)
Score 2: Last transaction 61-90 days ago (declining)
Score 1: Last transaction > 90 days ago OR never (dormant)
```

**SQL Implementation**:
```sql
CASE 
  WHEN days_since_last_txn IS NULL THEN 1  -- Never transacted
  WHEN days_since_last_txn <= 7 THEN 5
  WHEN days_since_last_txn <= 30 THEN 4
  WHEN days_since_last_txn <= 60 THEN 3
  WHEN days_since_last_txn <= 90 THEN 2
  ELSE 1
END as recency_score
```

**Business interpretation**:
- Score 5: "This merchant is using us daily"
- Score 1: "This merchant hasn't processed a payment in 3+ months - churn risk"

---

### FREQUENCY SCORE

**What we measure**: Average transactions processed per month

**Why it matters**:
- High frequency = deep integration into their business
- Low frequency = testing, not committed
- Frequency correlates with stickiness

**Scoring logic**:
```
Score 5: ≥ 100 transactions/month (power user)
Score 4: 50-99 transactions/month (heavy user)
Score 3: 20-49 transactions/month (regular user)
Score 2: 5-19 transactions/month (light user)
Score 1: < 5 transactions/month (barely using)
```

**SQL Implementation**:
```sql
CASE 
  WHEN avg_monthly_txns >= 100 THEN 5
  WHEN avg_monthly_txns >= 50 THEN 4
  WHEN avg_monthly_txns >= 20 THEN 3
  WHEN avg_monthly_txns >= 5 THEN 2
  ELSE 1
END as frequency_score
```

**Business interpretation**:
- Score 5: "This is their primary payment processor"
- Score 1: "They're barely using us - probably have another provider"

---

### MONETARY SCORE

**What we measure**: Average monthly transaction volume processed

**Why it matters**:
- High volume = high revenue customer
- Volume indicates business size and growth
- Larger customers are more valuable but also have more leverage

**Scoring logic**:
```
Score 5: ≥ $10,000/month (enterprise)
Score 4: $5,000-$9,999/month (high value)
Score 3: $2,000-$4,999/month (medium value)
Score 2: $500-$1,999/month (small value)
Score 1: < $500/month (minimal value)
```

**SQL Implementation**:
```sql
CASE 
  WHEN avg_monthly_volume >= 10000 THEN 5
  WHEN avg_monthly_volume >= 5000 THEN 4
  WHEN avg_monthly_volume >= 2000 THEN 3
  WHEN avg_monthly_volume >= 500 THEN 2
  ELSE 1
END as monetary_score
```

**Business interpretation**:
- Score 5: "Losing this customer would hurt our revenue significantly"
- Score 1: "Small fish - but many small fish = big revenue"

---

## CUSTOMER SEGMENTS

### Segment Definitions

**Champions** (R≥4, F≥4, M≥4)
- **Profile**: Active, frequent, high-value
- **% of base**: 15-20%
- **Behavior**: Process payments daily, high volume, rarely have issues
- **Strategy**: Protect at all costs, white-glove service, upsell to enterprise
- **Example**: E-commerce store doing $50K/month, 200 transactions, zero failures

**Loyal** (R≥4, F≥3)
- **Profile**: Consistently active, good frequency
- **% of base**: 15-20%
- **Behavior**: Regular usage, moderate volume
- **Strategy**: Maintain engagement, prevent from sliding to At Risk
- **Example**: SaaS company, 30 transactions/month, $5K volume

**Whales** (M≥4, F≤2)
- **Profile**: High value but infrequent (large transaction sizes)
- **% of base**: 5-8%
- **Behavior**: Occasional large payments (B2B, invoicing)
- **Strategy**: Don't lose them, understand their payment cycle
- **Example**: Consulting firm, 5 transactions/month but each is $10K+

**At Risk** (R≤2, F≥3)
- **Profile**: Used to be active, now declining
- **% of base**: 10-15%
- **Behavior**: Historically good customer going quiet
- **Strategy**: Immediate intervention, customer success outreach, find out why
- **Example**: Marketplace that processed 50 txns/month, now 0 for 60 days

**Dormant** (R=1)
- **Profile**: No recent activity, essentially churned
- **% of base**: 30-35%
- **Behavior**: Signed up but never engaged, or fully churned
- **Strategy**: Win-back campaigns, reactivation offers, or write off
- **Example**: Retail store that tried PayFlow, processed 3 transactions, never came back

**New/Testing** (R≥3, F≤2, M≤2)
- **Profile**: Recently signed up, low usage
- **% of base**: 15-20%
- **Behavior**: Evaluating the platform, not fully committed
- **Strategy**: Onboarding campaigns, integration support, prove value quickly
- **Example**: Startup testing payment processing, 8 transactions in first month

**Needs Attention** (Everything else)
- **Profile**: Mixed signals, doesn't fit clear pattern
- **% of base**: 5-10%
- **Behavior**: Irregular usage patterns
- **Strategy**: Investigate individually, understand their use case
- **Example**: Seasonal business with sporadic high-volume periods

---

## HEALTH SCORING SYSTEM

### Base Health Score (0-100)

**Formula**:
```
Health Score = (Recency × 20) + (Frequency × 20) + (Monetary × 20) + Penalties
```

**Maximum score**: 100 (if R=5, F=5, M=5, no penalties)
**Minimum score**: -30 (if R=1, F=1, M=1, all penalties)

### Penalties (Negative Adjustments)

**High Payment Failure Rate** (-20 points)
- Trigger: Failure rate > 10% in last 90 days
- Why: Technical issues or fraud, high churn predictor

**Excessive Support Tickets** (-15 points)
- Trigger: > 5 tickets in last 90 days
- Why: Customer experiencing problems, dissatisfaction

**Multiple Disputes** (-15 points)
- Trigger: > 2 disputes total
- Why: Fraud risk or product quality issues

### Health Status Categories

```
Healthy:  70-100 points (Green)
At Risk:  40-69 points  (Yellow)
Critical: 0-39 points   (Red)
```

**Healthy**: No immediate action needed, maintain relationship
**At Risk**: Proactive outreach, identify issues before they churn
**Critical**: Immediate intervention required, executive-level outreach

---

## EXAMPLE CALCULATIONS

### Example 1: Champion Customer

**Merchant**: "TechStore" (E-commerce)
- Last transaction: 2 days ago → R = 5
- Avg transactions/month: 150 → F = 5
- Avg monthly volume: $25,000 → M = 5
- Failure rate: 2% → No penalty
- Support tickets: 1 → No penalty
- Disputes: 0 → No penalty

**Health Score**: (5×20) + (5×20) + (5×20) = **100**
**Segment**: Champions
**Status**: Healthy
**Action**: White-glove service, explore upsell opportunities

---

### Example 2: At-Risk Customer

**Merchant**: "BoutiqueShop" (Retail)
- Last transaction: 65 days ago → R = 2
- Avg transactions/month: 40 (historically) → F = 4
- Avg monthly volume: $8,000 → M = 4
- Failure rate: 15% (before they stopped) → -20
- Support tickets: 6 → -15
- Disputes: 0 → 0

**Health Score**: (2×20) + (4×20) + (4×20) - 20 - 15 = **165 - 35 = 65**
**Segment**: At Risk
**Status**: At Risk
**Action**: Immediate customer success call - they had payment failures, opened tickets, then went quiet. Classic churn pattern.

---

### Example 3: Dormant Customer

**Merchant**: "StartupXYZ" (SaaS)
- Last transaction: Never / 200+ days ago → R = 1
- Avg transactions/month: 2 → F = 1
- Avg monthly volume: $300 → M = 1
- Failure rate: 0% → 0
- Support tickets: 0 → 0
- Disputes: 0 → 0

**Health Score**: (1×20) + (1×20) + (1×20) = **60**
**Segment**: Dormant
**Status**: At Risk (borderline Critical)
**Action**: Automated win-back email campaign, reactivation offer

---

## WHY THIS FRAMEWORK WORKS

### 1. Predictive Power
- Identifies churn 30-60 days before it happens
- R=1 or R=2 with high F/M = customer going quiet = churn warning
- Declining recency score over time = leading indicator

### 2. Resource Prioritization
- Customer success teams have limited time
- Focus on: Champions (protect) + At Risk (save)
- Dormant customers get automated campaigns, not human touch

### 3. Revenue Protection
- $2.3M in MRR from At Risk + Critical customers
- Saving 20% of at-risk customers = $460K saved revenue
- 5:1 ROI on customer success investment

### 4. Product Insights
- Dormant customers with high failure rates → fix payment infrastructure
- At Risk customers with support tickets → product/UX issues
- Champions with specific industries → ideal customer profile

---

## OPERATIONAL PLAYBOOK

### Weekly Review
1. Run RFM analysis in BigQuery
2. Export Critical + At Risk customers (health score < 70)
3. Assign to customer success team
4. Track interventions and outcomes

### Monthly Review
1. Segment migration analysis (who moved between segments?)
2. Churn rate by segment
3. Revenue by segment
4. Adjust health score thresholds if needed

### Quarterly Review
1. Validate RFM scoring logic (are predictions accurate?)
2. Adjust segment definitions based on business changes
3. Update penalty weights based on churn correlation analysis

---

## DASHBOARD INTEGRATION

### How RFM Shows Up in Dashboard

**Page 1: Executive Overview**
- KPI: Average Health Score (single number: 68.5)
- Trend: Health score over time (is it improving?)

**Page 2: Payment Performance**
- Filter failures by segment
- Insight: "At Risk segment has 12% failure rate vs 5% overall"

**Page 3: Customer Health** (RFM Deep Dive)
- Scatter plot: R × F sized by M, colored by segment
- Table: All customers with health scores, sortable
- Donut: Customer count by segment
- Bar: MRR by segment

**Page 4: Support & Operations**
- Filter tickets by segment
- Insight: "At Risk customers open 3x more tickets than Champions"

**Cross-filtering**: 
- Click "At Risk" on Page 3 → Pages 1,2,4 filter to show only At Risk data
- This is the power of integrated star schema

---

## ADVANCED: TIME-BASED ANALYSIS

### Segment Migration
Track how customers move between segments month-over-month:

```sql
-- Compare this month vs last month segments
WITH current_month AS (
  SELECT customer_id, segment as current_segment
  FROM customer_health
  WHERE analysis_date = CURRENT_DATE()
),
last_month AS (
  SELECT customer_id, segment as last_segment  
  FROM customer_health_history
  WHERE analysis_date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)
)
SELECT 
  last_segment,
  current_segment,
  COUNT(*) as customer_count
FROM current_month c
JOIN last_month l ON c.customer_id = l.customer_id
GROUP BY last_segment, current_segment;
```

**Insights**:
- "50 customers moved from Loyal → At Risk" (investigate why)
- "15 At Risk → Champions" (what did we do right?)

---

## TECHNICAL NOTES

### Why Scores 1-5?
- Easy to understand (like star ratings)
- Allows for 125 possible RFM combinations (5×5×5)
- Can create 3-digit RFM codes: "555" = Champion, "111" = Dormant

### Why These Thresholds?
- Based on PayFlow's data distribution
- ≥100 txns/month = top 20% of customers
- ≥$10K/month = top 15% by volume
- Adjust for your business

### Alternative Approaches
- **Quintiles**: Divide customers into 5 equal buckets (20% each)
- **K-means clustering**: Let algorithm find segments
- **Supervised learning**: Train model to predict churn directly

RFM is chosen because:
- Interpretable (executives understand it)
- Actionable (clear what to do for each segment)
- Fast to implement (no ML training needed)

---

## SUCCESS METRICS

### How to Measure RFM Effectiveness

**Leading Indicators**:
- % of At Risk customers saved (moved to Healthy)
- Time to intervention (days from "At Risk" to customer success contact)
- Support ticket resolution rate by segment

**Lagging Indicators**:
- Churn rate by segment (At Risk should have lower churn if framework works)
- MRR retention ($ saved by preventing churn)
- Customer lifetime value by segment

**Target**: 
- Reduce At Risk segment from 15% to 10% within 6 months
- Increase Champions from 15% to 20%
- Overall health score improvement: 68 → 75

---

## CONCLUSION

RFM is not just segmentation - it's an **early warning system** for churn.

By scoring customers on recent behavior (Recency), usage intensity (Frequency), and business value (Monetary), you can:

1. **Predict** who will churn before they do
2. **Prioritize** which customers deserve immediate attention  
3. **Personalize** outreach based on segment characteristics
4. **Prove** the ROI of customer success investments

**The goal**: Turn data into action, action into retention, retention into revenue.

---

## APPENDIX: FULL SQL REFERENCE

See `Course_Workflow_Complete.md` Module 4 for complete SQL implementation including:
- RFM metric calculation
- Score assignment logic
- Segment definitions
- Health score formula
- Integration with star schema
