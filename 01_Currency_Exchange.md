# Currency Exchange - Time-Anchored Rates

## GOOGLE SHEETS SETUP

### Column A: date_key
A1: `date_key`
A2: `20240101`
A3: `=TEXT(DATE(LEFT(A2,4),MID(A2,5,2),RIGHT(A2,2))+1,"YYYYMMDD")`
Copy A3 down to row 731

### Column B: currency
B1: `currency`
B2-B9: USD, CAD, GBP, EUR, INR, BRL, AUD, SGD
Copy B2:B9, paste down to row 731

### Column C: to_usd_rate
C1: `to_usd_rate`

**C2 (USD):** `1`

**C3 (CAD):**
```
=IFERROR(1/INDEX(GOOGLEFINANCE("CURRENCY:USDCAD","price",DATE(LEFT($A3,4),MID($A3,5,2),RIGHT($A3,2)),DATE(LEFT($A3,4),MID($A3,5,2),RIGHT($A3,2))),2,2),0.74)
```

**C4 (GBP):**
```
=IFERROR(INDEX(GOOGLEFINANCE("CURRENCY:GBPUSD","price",DATE(LEFT($A4,4),MID($A4,5,2),RIGHT($A4,2)),DATE(LEFT($A4,4),MID($A4,5,2),RIGHT($A4,2))),2,2),1.27)
```

**C5 (EUR):**
```
=IFERROR(INDEX(GOOGLEFINANCE("CURRENCY:EURUSD","price",DATE(LEFT($A5,4),MID($A5,5,2),RIGHT($A5,2)),DATE(LEFT($A5,4),MID($A5,5,2),RIGHT($A5,2))),2,2),1.08)
```

**C6 (INR):**
```
=IFERROR(1/INDEX(GOOGLEFINANCE("CURRENCY:USDINR","price",DATE(LEFT($A6,4),MID($A6,5,2),RIGHT($A6,2)),DATE(LEFT($A6,4),MID($A6,5,2),RIGHT($A6,2))),2,2),0.012)
```

**C7 (BRL):**
```
=IFERROR(1/INDEX(GOOGLEFINANCE("CURRENCY:USDBRL","price",DATE(LEFT($A7,4),MID($A7,5,2),RIGHT($A7,2)),DATE(LEFT($A7,4),MID($A7,5,2),RIGHT($A7,2))),2,2),0.20)
```

**C8 (AUD):**
```
=IFERROR(1/INDEX(GOOGLEFINANCE("CURRENCY:USDAUD","price",DATE(LEFT($A8,4),MID($A8,5,2),RIGHT($A8,2)),DATE(LEFT($A8,4),MID($A8,5,2),RIGHT($A8,2))),2,2),0.66)
```

**C9 (SGD):**
```
=IFERROR(1/INDEX(GOOGLEFINANCE("CURRENCY:USDSGD","price",DATE(LEFT($A9,4),MID($A9,5,2),RIGHT($A9,2)),DATE(LEFT($A9,4),MID($A9,5,2),RIGHT($A9,2))),2,2),0.74)
```

Copy C2:C9 down to row 731.

Download as CSV.

## BIGQUERY

```sql
CREATE TABLE payflow_star.dim_exchange_rates (
  date_key STRING,
  currency STRING,
  to_usd_rate FLOAT64
);
```

Upload CSV.

```

DONE.
