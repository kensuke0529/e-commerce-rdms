#!/usr/bin/env python3
"""
Script to create an Excel evaluation file from the SQL report.
Extracts user questions, expected SQL queries, and expected results.
"""

import re
import pandas as pd
from pathlib import Path

def parse_report_md(file_path):
    """Parse the report.md file to extract queries and results."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    queries = []
    
    # Split by query sections (### Query)
    sections = re.split(r'### Query \d+:', content)
    
    for section in sections[1:]:  # Skip first empty section
        # Extract query title/description
        title_match = re.search(r'^([^\n]+)', section.strip())
        title = title_match.group(1).strip() if title_match else ""
        
        # Extract SQL query
        sql_match = re.search(r'```sql\n(.*?)```', section, re.DOTALL)
        sql_query = sql_match.group(1).strip() if sql_match else ""
        
        # Extract results table
        results_match = re.search(r'\*\*Results:\*\*\s*\n\n(.*?)(?=\n\n\*\*Analysis:|\Z)', section, re.DOTALL)
        results_text = results_match.group(1).strip() if results_match else ""
        
        # Check for execution errors
        if "*Execution error*" in results_text or "Execution error" in section:
            results_text = "EXECUTION ERROR"
        
        if sql_query:
            queries.append({
                'title': title,
                'sql': sql_query,
                'results': results_text
            })
    
    return queries

def get_user_questions():
    """Map query titles to user questions."""
    question_map = {
        "Total Revenue": "What is the total revenue generated from all completed orders?",
        "Monthly revenue trend": "Calculate monthly revenue trends. Show month, total revenue, order count, and average order value.",
        "month-over-month revenue growth %": "Calculate month-over-month revenue growth percentage with running totals.",
        "category revenue": "Which product categories generate the most revenue? Include percentage of total revenue and cumulative percentage for Pareto analysis.",
        "Calculate revenue per seller with 10% platform fee deduction. Rank sellers by net revenue and identify top 20% performers.": "Calculate revenue per seller with 10% platform fee deduction. Rank sellers by net revenue and identify top 20% performers.",
        "How many customers have made at least one purchase?": "How many customers have made at least one purchase?",
        "Calculate customer lifetime value (CLV). Show top 10 customers by total spend.": "Calculate customer lifetime value (CLV). Show top 10 customers by total spend.",
        "Perform RFM analysis (Recency, Frequency, Monetary). Segment customers into: Champions, Loyal, At-Risk, Lost.": "Perform RFM analysis (Recency, Frequency, Monetary). Segment customers into: Champions, Loyal, At-Risk, Lost.",
        "2. how many orders": "How many orders has each customer made?",
        "3. total_spending": "What is the total spending for each customer?",
        "Combined": "Show combined RFM analysis with recency, frequency, monetary values and spending groups for all customers.",
        "calculate customer retention rate by cohort (group by first purchase month, track repeat purchases)": "Calculate customer retention rate by cohort (group by first purchase month, track repeat purchases).",
        "Find customers who bid but never purchased. Calculate their total bid activity and potential lost revenue.": "Find customers who bid but never purchased. Calculate their total bid activity and potential lost revenue.",
        "1. List top 10 best-selling products by quantity sold.": "List top 10 best-selling products by quantity sold.",
        "2. Which products have the highest average customer rating? (minimum 3 reviews)": "Which products have the highest average customer rating? (minimum 3 reviews)",
        "3. Product performance dashboard - units sold, revenue, average rating, review count, bid activity (total bids, unique bidders).": "Product performance dashboard - units sold, revenue, average rating, review count, bid activity (total bids, unique bidders).",
        "4. Identify slow-moving inventory (products with less than 2 units sold).": "Identify slow-moving inventory (products with less than 2 units sold).",
        "Average shipping time (days) by carrier.": "What is the average shipping time (days) by carrier?",
        "Customer service metrics dashboard: total tickets, average resolution time, tickets by customer segment (CLV tier).": "Customer service metrics dashboard: total tickets, average resolution time, tickets by customer segment (CLV tier).",
        "Staff performance ranking: tickets handled, hours logged, avg time per ticket, customer/seller split.": "Staff performance ranking: tickets handled, hours logged, avg time per ticket, customer/seller split.",
        "1. Find data quality issues - orders without payment, products without seller, missing emails.": "Find data quality issues - orders without payment, products without seller, missing emails.",
        "product wo seller": "How many products are missing seller information?",
        "missing email": "How many users are missing email addresses?",
        "Duplicate emails": "Are there any duplicate email addresses in the system?",
        "payment has to be more than quantity * product_price": "Verify that payment amounts match quantity * product_price for all orders.",
    }
    return question_map

def should_exclude_query(title, results):
    """Determine if a query should be excluded from evaluation."""
    # Exclude queries with execution errors
    if "EXECUTION ERROR" in results or "*Execution error*" in results:
        return True
    
    # Exclude incomplete/sub-queries
    exclude_titles = [
        "Perform RFM analysis (Recency, Frequency, Monetary). Segment customers into: Champions, Loyal, At-Risk, Lost.",  # Incomplete - only shows recency
        "2. how many orders",  # Sub-query of RFM
        "3. total_spending",  # Sub-query of RFM
        "Customer service metrics dashboard: total tickets, average resolution time, tickets by customer segment (CLV tier).",  # Execution error
        "product wo seller",  # Sub-query of data quality check
        "missing email",  # Sub-query of data quality check
        "Duplicate emails",  # Sub-query of data quality check
    ]
    
    return title in exclude_titles

def create_eval_dataframe(queries, question_map):
    """Create a DataFrame with evaluation columns."""
    rows = []
    
    for query_data in queries:
        title = query_data['title']
        results = query_data['results']
        
        # Skip excluded queries
        if should_exclude_query(title, results):
            print(f"  Excluding: {title}")
            continue
        
        user_question = question_map.get(title, title)  # Use title as fallback
        
        # Clean SQL query - remove comments if needed, but keep them for reference
        sql_query = query_data['sql']
        
        # Format results - truncate if too long
        if len(results) > 1000:
            results = results[:1000] + "... (truncated)"
        
        rows.append({
            'User Question': user_question,
            'Expected SQL Query': sql_query,
            'Expected Result': results,
            'AI Generated Query': '',  # Empty for evaluation - to be filled by AI model
            'Result': ''  # Empty for evaluation - to be filled after running AI query
        })
    
    return pd.DataFrame(rows)

def main():
    report_path = Path('result/report.md')
    output_path = Path('result/sql_generator_eval.xlsx')
    
    print("Parsing report.md...")
    queries = parse_report_md(report_path)
    print(f"Found {len(queries)} queries")
    
    print("Mapping questions...")
    question_map = get_user_questions()
    
    print("Creating DataFrame (filtering useless queries)...")
    df = create_eval_dataframe(queries, question_map)
    
    print(f"Creating Excel file: {output_path}")
    # Replace NaN with empty strings for better Excel display
    df = df.fillna('')
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='SQL Evaluation', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['SQL Evaluation']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            )
            # Set reasonable max width (SQL queries can be long)
            if col == 'Expected SQL Query' or col == 'AI Generated Query':
                max_length = min(max_length, 150)
            else:
                max_length = min(max_length, 100)
            worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
    
    print(f"✅ Excel file created successfully: {output_path}")
    print(f"Total rows: {len(df)}")

if __name__ == '__main__':
    main()

