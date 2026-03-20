# Dashboard Design Guide

## PAGE STRUCTURE

### Row 1: KPIs (Answer: WHAT is happening?)
- Total Volume USD: $23.1M
- Success Rate: 91.7%
- Avg Health Score: 68
- At Risk MRR: $XXK

**Why this order?** Volume → Performance → Health → Risk (funnel from general to specific)

### Row 2: Trends (Answer: WHY is it happening?)
- LEFT: Line chart - Monthly revenue trend (shows growth pattern)
- RIGHT: Donut chart - Transaction status split (shows where problems are)

**Why side-by-side?** Time trend + current breakdown gives complete picture

### Row 3: Analysis (Answer: WHERE is the problem?)
- LEFT: Column chart - Failure rate by method (identifies card payments as issue)
- RIGHT: Scatter plot - RFM segmentation (identifies at-risk customers)

**Why these two?** One for operations (fix infrastructure), one for CS (save customers)

### Row 4: Action (Answer: WHO needs attention?)
- FULL WIDTH: Table of at-risk customers with health scores

**Why bottom?** After seeing WHAT/WHY/WHERE, this is the action list

## COLOR STRATEGY

- **Green (#02C39A)**: Success, Champions, good performance
- **Red (#F96167)**: Failure, At Risk, problems
- **Teal (#028090)**: Primary brand color, neutral data
- **Yellow (#F9E795)**: Warning, moderate concern

## DESIGN PRINCIPLES

1. **F-pattern reading**: Top-left → top-right → down
2. **Progressive disclosure**: General → specific
3. **Actionable**: Every visual drives a decision
4. **Benchmarked**: 2.5% line shows industry standard
5. **Interactive**: Click segment → everything filters

## ANSWERS TO CEO QUESTIONS

**Q1: Why 5% failure?**
→ Column chart: Card payments at 6.5% (2.6× benchmark)

**Q2: Who will churn?**
→ Scatter plot: Red dots (At Risk)
→ Table: 126 customers with health <40

**Q3: Are segments profitable?**
→ Scatter plot: Champions (green) = 12% customers
→ Can filter to see Champions revenue in line chart

DONE.
