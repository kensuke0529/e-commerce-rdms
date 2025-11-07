# SQL Generator (Internal Use)

An AI-powered SQL query generation system for internal analytics use. Converts natural language business questions into optimized SQL queries with automatic error handling, validation, and result analysis.

> **Note**: This is an internal tool for data analysts and business users. For customer-facing SQL capabilities, see the [Customer Chatbot](../chatbot/README.md).

## Overview

The SQL Generator enables business users and analysts to query data using natural language, eliminating the need for SQL expertise. It automatically converts questions into database queries, executes them, validates results, and provides AI-powered insights.

![SQL Agent Graph](../../result/image/sql_agent_graph_simplified.png)

## Business Value

### Democratized Data Access

- **No SQL Knowledge Required**: Business users can ask questions in plain English
- **Faster Insights**: Get answers in seconds instead of waiting for data team

### Operational Efficiency

- **Reduced Query Time**: Instant SQL generation vs. manual query writing
- **Error Reduction**: Automatic validation prevents incorrect results
- **Intelligent Retry**: System automatically corrects and retries failed queries
- **Resource Optimization**: Frees data analysts for complex analytical work

### Enhanced Decision Making

- **AI-Powered Insights**: Automatic analysis of query results with business context
- **Actionable Recommendations**: Suggests next steps based on findings
- **Comprehensive Analysis**: Combines data retrieval with interpretation

## Core Capabilities

### 1. Natural Language to SQL Conversion

**Business Function**: Converts business questions into database queries automatically

**Value**:

- Enables non-technical users to access data independently
- Reduces time from question to answer
- Ensures queries follow best practices and business logic

**Supported Question Types**:

- Revenue and sales analytics
- Customer behavior analysis
- Product performance metrics
- Order and purchase history
- Statistical calculations and aggregations

### 2. Intelligent Question Classification

**Business Function**: Automatically determines if a question requires database access or is conversational

**Value**:

- Routes questions appropriately without user intervention
- Handles both data queries and general questions
- Provides conversational responses when SQL isn't needed

**Question Categories**:

- **SQL Questions**: Require database queries (e.g., "What is total revenue?")
- **Conversational Questions**: General inquiries (e.g., "How does this system work?")

### 3. Result Validation

**Business Function**: Ensures query results actually answer the user's question

**Value**:

- Prevents misleading or incomplete answers
- Validates data quality before presenting results
- Automatically retries with corrected queries when validation fails
- Ensures business questions are fully answered

### 4. AI-Powered Result Analysis

**Business Function**: Generates insights and recommendations from query results

**Value**:

- Transforms raw data into actionable insights
- Identifies trends and patterns automatically
- Explains business implications of findings
- Suggests next steps based on results

**Analysis Components**:

- Key findings and important data points
- Trend identification
- Business implications
- Actionable recommendations

## How It Works

### Question Processing Workflow

1. **Question Classification**: System determines if question needs database access
2. **SQL Generation**: Converts natural language to optimized SQL query
3. **Query Execution**: Runs query against database
4. **Result Validation**: Verifies results answer the question correctly
5. **Error Handling**: Automatically corrects and retries if needed
6. **Analysis Generation**: Creates insights and recommendations from results
7. **Response Delivery**: Provides comprehensive answer with data and analysis

### Automatic Error Recovery

When queries fail or produce invalid results:

- System identifies the type of error
- Automatically corrects the query based on error type
- Retries with corrected query (up to configured limit)
- Provides clear explanation if all retries fail

### Multi-Step Processing

The system processes questions through multiple stages:

- Classification to route appropriately
- SQL generation with schema awareness
- Execution with error handling
- Validation to ensure correctness
- Analysis to provide insights
- Response formatting for clarity

## Key Features

### Schema Awareness

- Understands complete database structure
- Knows table relationships and constraints
- Applies business logic automatically
- Generates queries that respect data integrity

### Intelligent Retry Logic

- Automatically corrects syntax errors
- Fixes logic errors based on validation feedback
- Handles empty results gracefully
- Provides user-friendly error messages

### Result Analysis

- Highlights key findings automatically
- Identifies trends and patterns
- Explains business implications
- Suggests actionable next steps


## Additional Resources

- [Main Project README](../../README.md)
- [Customer Chatbot Documentation](../chatbot/README.md)
- [Data Engineering Documentation](../../sql/README.md)

---
