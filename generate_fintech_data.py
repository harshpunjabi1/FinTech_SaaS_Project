import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

print("="*70)
print("GENERATING FINTECH DATASET - PAYFLOW ANALYTICS")
print("="*70)

CURRENT_DATE = datetime.now()
START_DATE = CURRENT_DATE - timedelta(days=365)

# ===== 1. CUSTOMERS =====
print("\n1. Generating customers table...")

industries = ['E-commerce', 'SaaS', 'Marketplace', 'Retail', 'Services', 'Non-profit', 'Education', 'Healthcare']
countries = ['USA', 'Canada', 'UK', 'India', 'Brazil', 'Germany', 'Australia', 'Singapore']
plans = ['Starter', 'Growth', 'Pro']
plan_mrr = {'Starter': 29, 'Growth': 99, 'Pro': 299}

num_customers = 5000
customers_data = []

for i in range(1, num_customers + 1):
    # Signup date distributed over past year
    days_ago = int(np.random.exponential(120))  # Most recent signups, some old
    signup_date = CURRENT_DATE - timedelta(days=min(days_ago, 365))
    
    # Industry distribution
    industry = random.choices(
        industries,
        weights=[30, 25, 15, 12, 10, 3, 3, 2]
    )[0]
    
    # Plan based on industry (SaaS tends to go Pro, Non-profit tends Starter)
    if industry in ['SaaS', 'Marketplace']:
        plan = random.choices(plans, weights=[20, 40, 40])[0]
    elif industry in ['Non-profit', 'Education']:
        plan = random.choices(plans, weights=[60, 30, 10])[0]
    else:
        plan = random.choices(plans, weights=[40, 40, 20])[0]
    
    # Employee size correlates with plan
    if plan == 'Starter':
        employee_size = random.choices(['1-10', '11-50', '51-200'], weights=[70, 25, 5])[0]
    elif plan == 'Growth':
        employee_size = random.choices(['1-10', '11-50', '51-200'], weights=[30, 50, 20])[0]
    else:  # Pro
        employee_size = random.choices(['1-10', '11-50', '51-200', '201-1000'], weights=[10, 30, 40, 20])[0]
    
    country = random.choices(countries, weights=[40, 15, 12, 10, 8, 7, 5, 3])[0]
    
    customers_data.append({
        'customer_id': f'cust_{i:05d}',
        'business_name': f'Business_{i}',
        'industry': industry,
        'signup_date': signup_date.strftime('%Y-%m-%d'),
        'plan': plan,
        'mrr': plan_mrr[plan],
        'country': country,
        'employee_size': employee_size
    })

customers_df = pd.DataFrame(customers_data)

# ===== 2. TRANSACTIONS =====
print("2. Generating transactions table (500K transactions)...")

payment_methods = ['card', 'bank_transfer', 'wallet']
currencies = {'USA': 'USD', 'Canada': 'CAD', 'UK': 'GBP', 'India': 'INR', 'Brazil': 'BRL', 
              'Germany': 'EUR', 'Australia': 'AUD', 'Singapore': 'SGD'}

transactions_data = []
transaction_id = 1
target_transactions = 500000

# Calculate transactions per customer based on their profile
customer_transaction_profile = {}
for _, customer in customers_df.iterrows():
    # Active customers have more transactions
    days_since_signup = (CURRENT_DATE - pd.to_datetime(customer['signup_date'])).days
    
    # Transaction frequency based on plan and industry
    if customer['plan'] == 'Pro':
        monthly_txns = random.randint(150, 400)
    elif customer['plan'] == 'Growth':
        monthly_txns = random.randint(40, 150)
    else:  # Starter
        monthly_txns = random.randint(5, 40)
    
    # E-commerce and Marketplace have higher volume
    if customer['industry'] in ['E-commerce', 'Marketplace']:
        monthly_txns = int(monthly_txns * 1.5)
    
    # Total transactions based on how long they've been customer
    months_active = min(days_since_signup / 30, 12)
    total_txns = int(monthly_txns * months_active)
    
    customer_transaction_profile[customer['customer_id']] = {
        'total_txns': total_txns,
        'monthly_txns': monthly_txns,
        'currency': currencies[customer['country']],
        'country': customer['country']
    }

# Generate transactions
customers_sampled = customers_df.sample(n=min(3000, len(customers_df)))  # Not all customers transact

for _, customer in customers_sampled.iterrows():
    if transaction_id > target_transactions:
        break
    
    customer_id = customer['customer_id']
    profile = customer_transaction_profile[customer_id]
    signup_date = pd.to_datetime(customer['signup_date'])
    
    num_txns = min(profile['total_txns'], 200)  # Cap per customer
    
    for _ in range(num_txns):
        if transaction_id > target_transactions:
            break
        
        # Transaction date between signup and now
        days_range = (CURRENT_DATE - signup_date).days
        if days_range > 0:
            txn_date = signup_date + timedelta(days=random.randint(0, days_range))
        else:
            txn_date = signup_date
        
        # Transaction amount (realistic distribution)
        if customer['industry'] in ['E-commerce', 'Marketplace']:
            amount = round(np.random.lognormal(3.5, 1.2), 2)  # Mean ~$50, tail to $500+
        elif customer['industry'] == 'SaaS':
            amount = round(np.random.lognormal(4.0, 0.8), 2)  # Mean ~$80, less variance
        else:
            amount = round(np.random.lognormal(3.0, 1.0), 2)  # Mean ~$30
        
        amount = max(1.0, min(amount, 9999.99))  # Cap between $1 and $10K
        
        # Payment method preference by country
        if profile['country'] in ['India', 'Brazil']:
            payment_method = random.choices(payment_methods, weights=[40, 20, 40])[0]
        elif profile['country'] in ['Germany', 'UK']:
            payment_method = random.choices(payment_methods, weights=[50, 40, 10])[0]
        else:
            payment_method = random.choices(payment_methods, weights=[70, 20, 10])[0]
        
        # Transaction status (realistic failure patterns)
        # Card has higher failure rate
        if payment_method == 'card':
            status = random.choices(
                ['successful', 'failed', 'refunded', 'disputed'],
                weights=[90, 6, 3, 1]
            )[0]
        elif payment_method == 'bank_transfer':
            status = random.choices(
                ['successful', 'failed', 'refunded', 'disputed'],
                weights=[94, 4, 1.5, 0.5]
            )[0]
        else:  # wallet
            status = random.choices(
                ['successful', 'failed', 'refunded', 'disputed'],
                weights=[95, 3, 1.8, 0.2]
            )[0]
        
        # Stripe fee structure: 2.9% + $0.30
        if status == 'successful':
            fee = round(amount * 0.029 + 0.30, 2)
        else:
            fee = 0
        
        transactions_data.append({
            'transaction_id': f'txn_{transaction_id:08d}',
            'customer_id': customer_id,
            'transaction_date': txn_date.strftime('%Y-%m-%d %H:%M:%S'),
            'amount': amount,
            'currency': profile['currency'],
            'status': status,
            'payment_method': payment_method,
            'fee': fee
        })
        transaction_id += 1

transactions_df = pd.DataFrame(transactions_data)

# ===== 3. SUPPORT TICKETS =====
print("3. Generating support_tickets table...")

categories = ['payment_failure', 'refund_request', 'integration_help', 'billing_question', 
              'fraud_alert', 'account_setup', 'payout_delay', 'api_error']
priorities = ['low', 'medium', 'high', 'urgent']

tickets_data = []
ticket_id = 1

# Customers with payment failures are more likely to create tickets
failed_txns = transactions_df[transactions_df['status'] == 'failed'].groupby('customer_id').size()

for customer_id in customers_df['customer_id']:
    # Probability of creating ticket
    has_failures = customer_id in failed_txns.index
    
    if has_failures:
        num_tickets = random.choices([0, 1, 2, 3, 4, 5, 6], weights=[20, 25, 20, 15, 10, 7, 3])[0]
    else:
        num_tickets = random.choices([0, 1, 2, 3], weights=[60, 25, 12, 3])[0]
    
    customer_signup = pd.to_datetime(customers_df[customers_df['customer_id'] == customer_id]['signup_date'].values[0])
    
    for _ in range(num_tickets):
        days_since_signup = (CURRENT_DATE - customer_signup).days
        if days_since_signup > 0:
            created = customer_signup + timedelta(days=random.randint(1, days_since_signup))
        else:
            created = customer_signup
        
        # Resolution time based on priority
        if has_failures:
            category = random.choices(
                categories,
                weights=[40, 20, 15, 10, 5, 5, 3, 2]
            )[0]
            priority = random.choices(priorities, weights=[20, 30, 35, 15])[0]
        else:
            category = random.choices(
                categories,
                weights=[10, 15, 25, 20, 5, 15, 5, 5]
            )[0]
            priority = random.choices(priorities, weights=[40, 40, 15, 5])[0]
        
        # Resolution time
        if priority == 'urgent':
            resolution_hours = random.randint(1, 8)
        elif priority == 'high':
            resolution_hours = random.randint(4, 24)
        elif priority == 'medium':
            resolution_hours = random.randint(8, 72)
        else:
            resolution_hours = random.randint(24, 168)
        
        resolved = created + timedelta(hours=resolution_hours)
        
        # Satisfaction score (lower for urgent/high priority)
        if priority in ['urgent', 'high']:
            satisfaction = random.choices([1, 2, 3, 4, 5], weights=[15, 20, 30, 25, 10])[0]
        else:
            satisfaction = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 35, 30])[0]
        
        tickets_data.append({
            'ticket_id': f'tkt_{ticket_id:06d}',
            'customer_id': customer_id,
            'created_at': created.strftime('%Y-%m-%d %H:%M:%S'),
            'resolved_at': resolved.strftime('%Y-%m-%d %H:%M:%S'),
            'category': category,
            'priority': priority,
            'satisfaction_score': satisfaction
        })
        ticket_id += 1

support_tickets_df = pd.DataFrame(tickets_data)

# ===== 4. DISPUTES =====
print("4. Generating disputes table...")

dispute_reasons = ['fraudulent', 'product_not_received', 'duplicate', 'not_as_described', 'unauthorized']
dispute_statuses = ['won', 'lost', 'pending']

disputes_data = []
dispute_id = 1

# Only disputed transactions create disputes
disputed_txns = transactions_df[transactions_df['status'] == 'disputed']

for _, txn in disputed_txns.iterrows():
    created_date = pd.to_datetime(txn['transaction_date']) + timedelta(days=random.randint(1, 30))
    
    reason = random.choices(
        dispute_reasons,
        weights=[40, 25, 15, 15, 5]
    )[0]
    
    # Dispute outcome
    if reason == 'fraudulent':
        status = random.choices(dispute_statuses, weights=[20, 70, 10])[0]  # Usually lost
    elif reason == 'duplicate':
        status = random.choices(dispute_statuses, weights=[60, 30, 10])[0]  # Usually won
    else:
        status = random.choices(dispute_statuses, weights=[40, 40, 20])[0]
    
    disputes_data.append({
        'dispute_id': f'dsp_{dispute_id:06d}',
        'transaction_id': txn['transaction_id'],
        'customer_id': txn['customer_id'],
        'created_date': created_date.strftime('%Y-%m-%d'),
        'reason': reason,
        'status': status,
        'amount': txn['amount']
    })
    dispute_id += 1

disputes_df = pd.DataFrame(disputes_data)

# ===== SAVE ALL FILES =====
print("\n5. Saving CSV files...")

customers_df.to_csv('/mnt/user-data/outputs/customers.csv', index=False)
transactions_df.to_csv('/mnt/user-data/outputs/transactions.csv', index=False)
support_tickets_df.to_csv('/mnt/user-data/outputs/support_tickets.csv', index=False)
disputes_df.to_csv('/mnt/user-data/outputs/disputes.csv', index=False)

# ===== VALIDATION =====
import os

print("\n" + "="*70)
print("DATASET GENERATION COMPLETE")
print("="*70)

for filename in ['customers', 'transactions', 'support_tickets', 'disputes']:
    filepath = f'/mnt/user-data/outputs/{filename}.csv'
    size_mb = os.path.getsize(filepath) / 1024 / 1024
    df = pd.read_csv(filepath)
    print(f"{filename}.csv: {len(df):,} rows ({size_mb:.1f} MB)")

print("\n" + "="*70)
print("DATA QUALITY CHECKS")
print("="*70)

# Transaction status distribution
status_dist = transactions_df['status'].value_counts(normalize=True) * 100
print("\nTransaction Status Distribution:")
for status, pct in status_dist.items():
    print(f"  {status}: {pct:.1f}%")

# Payment method distribution
method_dist = transactions_df['payment_method'].value_counts(normalize=True) * 100
print("\nPayment Method Distribution:")
for method, pct in method_dist.items():
    print(f"  {method}: {pct:.1f}%")

# Support ticket categories
cat_dist = support_tickets_df['category'].value_counts().head(5)
print("\nTop Support Ticket Categories:")
for cat, count in cat_dist.items():
    print(f"  {cat}: {count}")

# Total revenue and fees
total_revenue = transactions_df[transactions_df['status'] == 'successful']['amount'].sum()
total_fees = transactions_df[transactions_df['status'] == 'successful']['fee'].sum()
print(f"\nTotal Successful Transaction Volume: ${total_revenue:,.2f}")
print(f"Total Fees Earned: ${total_fees:,.2f}")
print(f"Effective Fee Rate: {(total_fees/total_revenue*100):.2f}%")

# Dispute rate
dispute_rate = (len(disputes_df) / len(transactions_df)) * 100
print(f"\nDispute Rate: {dispute_rate:.2f}%")

print("\n" + "="*70)
print("FILES READY FOR BIGQUERY UPLOAD")
print("="*70)
