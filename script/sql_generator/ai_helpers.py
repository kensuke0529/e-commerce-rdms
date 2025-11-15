"""
Helper utilities for AI SQL operations.
Contains shared functions for classification, SQL formatting, and result validation.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import pandas as pd
import sys
from pathlib import Path

# Import LangSmith configuration to enable tracing
sys.path.insert(0, str(Path(__file__).parent.parent))
from langsmith_config import setup_langsmith

load_dotenv()
setup_langsmith()

# Use LangChain ChatOpenAI for tracing
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    openai_api_key=os.environ.get("OPENAI_API_KEY"),
)


# ============================================================================
# CLASSIFICATION
# ============================================================================


def classify_question_type(prompt: str) -> str:
    """
    Classify if a question requires SQL or is conversational.

    Returns:
        "SQL" or "CONVERSATIONAL"
    """
    classification_prompt = f"""
    Analyze this question and determine if it requires SQL database querying or is a conversational question.
    
    Question: "{prompt}"
    
    If the question asks for ANY of the following, respond with "SQL":
    - Sales data, revenue, quantities sold
    - Product performance, top products, best items
    - Customer data, demographics, behavior
    - Order data, purchase history
    - Any specific business metrics or data analysis
    - Questions about "what", "which", "how many", "top", "best", "worst" when referring to data
    
    If the question asks for opinions, suggestions, or general advice, respond with "CONVERSATIONAL".
    
    Respond with ONLY one word: SQL or CONVERSATIONAL
    """

    try:
        # Use LangChain for tracing
        response = llm.invoke([HumanMessage(content=classification_prompt)])
        result = response.content.strip().upper()
        return "SQL" if "SQL" in result else "CONVERSATIONAL"
    except Exception as e:
        print(f"Classification error: {e}")
        return "SQL"  # Default to SQL for safety


# ============================================================================
# SQL GENERATION
# ============================================================================


def generate_sql_query(prompt: str) -> str:
    """
    Generate SQL query from natural language prompt.

    Returns:
        SQL query string
    """
    # Read schema information
    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "..", "sql", "0.tables.sql"
    )
    schema_info = ""
    if os.path.exists(schema_path):
        with open(schema_path, "r") as f:
            schema_info = f.read()

    sql_generation_prompt = f"""
You are a PostgreSQL query optimization expert. Generate a correct, efficient SQL query.

DATABASE SCHEMA:
{schema_info}

USER QUESTION: "{prompt}"

CORE PRINCIPLES:

1. TABLE RELATIONSHIPS & DATA FLOW
   - Understand the business domain: orders flow through payment, products belong to sellers
   - Follow foreign key relationships in the schema
   - Use the correct "source of truth" table for each metric:
     * For actual money received → payment table
     * For order details → order_header table
     * For product info → product table
   - Don't calculate derived values when actual values exist in tables

2. DATE & TIME OPERATIONS
   - Use standard SQL functions that work consistently:
     * EXTRACT(YEAR/MONTH/DAY FROM date_column) for date parts
     * AGE(date1, date2) for intervals between dates
     * CURRENT_DATE or NOW() for current timestamps
   - When calculating time periods, consider what the interval represents
   - For date grouping, extract components explicitly rather than truncating

3. WINDOW FUNCTIONS FOR COMPARISONS
   - Use LAG/LEAD for comparing rows to previous/next periods
   - Use RANK/ROW_NUMBER for ordering and ranking
   - Properly define PARTITION BY and ORDER BY clauses
   - Window functions operate on result sets, not during aggregation

4. AGGREGATION & GROUPING
   - Ensure all aggregations match the grouping level requested
   - Use CTEs to break complex aggregations into logical steps
   - When filtering aggregated data, use HAVING not WHERE
   - Consider NULL handling in aggregates (COUNT vs COUNT(*))

5. MULTI-STEP CALCULATIONS
   - Break complex logic into CTEs with descriptive names
   - Each CTE should represent one logical operation
   - Build from simple to complex: base data → calculations → comparisons
   - Avoid nested subqueries when CTEs are clearer

6. JOIN STRATEGY
   - Use explicit JOIN syntax (INNER/LEFT/RIGHT/FULL)
   - Understand when LEFT JOIN is needed (optional relationships)
   - Join on proper keys (check foreign key constraints in schema)
   - Consider join order for performance

7. HANDLING MISSING DATA
   - Use COALESCE for default values
   - Use IS NULL / IS NOT NULL for existence checks
   - LEFT JOIN when you want to include records without matches
   - Consider CASE WHEN for conditional logic

8. PERFORMANCE CONSIDERATIONS
   - Filter early (WHERE before JOIN when possible)
   - Use indexes implied by primary/foreign keys
   - Avoid SELECT * in subqueries
   - Use EXISTS instead of IN for large subsets

9. QUERY STRUCTURE
   - Start with the main table that contains the primary entity
   - Join related tables as needed
   - Apply filters (WHERE)
   - Group if aggregating (GROUP BY)
   - Filter aggregates (HAVING)
   - Order results (ORDER BY)
   - Limit if needed (LIMIT)

10. ANALYTICAL PATTERNS
    - Growth rates: current vs previous using LAG
    - Cumulative totals: SUM() OVER (ORDER BY ...)
    - Rankings: RANK/DENSE_RANK/ROW_NUMBER
    - Moving averages: AVG() OVER (ROWS BETWEEN ...)
    - Cohort analysis: First event + subsequent events over time periods

OUTPUT REQUIREMENTS:
- Return ONLY the SQL query
- No explanations, comments, or markdown formatting
- Use meaningful aliases for calculated columns
- Format numbers appropriately (ROUND for currency)
- Ensure column names in SELECT match what users expect
- Order results logically (usually by primary grouping columns)

VERIFICATION CHECKLIST (think through before generating):
□ Are all table names spelled correctly per schema?
□ Do all columns exist in their referenced tables?
□ Are JOINs connecting on correct foreign key relationships?
□ Are aggregations at the right level (matching GROUP BY)?
□ Are window functions using correct PARTITION/ORDER BY?
□ Does date arithmetic use proper PostgreSQL functions?
□ Are NULLs handled appropriately?
□ Does the query answer the actual question asked?

Generate the PostgreSQL query now:
"""

    try:
        sql_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            openai_api_key=os.environ.get("OPENAI_API_KEY")
        )
        response = sql_llm.invoke([HumanMessage(content=sql_generation_prompt)])
        sql_query = response.content.strip()

        # Clean up the query - remove markdown code blocks if present
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]

        return sql_query.strip()
    except Exception as e:
        print(f"SQL generation error: {e}")
        raise


# ============================================================================
# VALIDATION
# ============================================================================


def validate_sql_results(sql_results: list) -> tuple[bool, bool, str]:
    """
    Validate SQL query results.

    Args:
        sql_results: List of result dictionaries with 'description' and 'data' keys

    Returns:
        Tuple of (is_valid: bool, has_data: bool, error_msg: str)
    """
    if not sql_results:
        return False, False, "No results returned from query"

    if not isinstance(sql_results, list):
        return False, False, "Results must be a list"

    has_data = False
    for result in sql_results:
        if not isinstance(result, dict):
            return False, False, "Each result must be a dictionary"

        if "data" not in result:
            return False, False, "Result missing 'data' key"

        if not isinstance(result["data"], pd.DataFrame):
            return False, False, "Result data must be a pandas DataFrame"

        if not result["data"].empty:
            has_data = True

    if not has_data:
        return True, False, "Query executed successfully but returned no rows"

    return True, True, ""


# ============================================================================
# FORMATTING
# ============================================================================


def format_results_for_display(sql_results) -> str:
    """
    Format SQL results for console/display output.

    Args:
        sql_results: List of result dictionaries

    Returns:
        Formatted string
    """
    if not sql_results:
        return "No results available"

    formatted = ""
    for result in sql_results:
        # Check if data is a DataFrame before calling .empty
        if isinstance(result["data"], pd.DataFrame) and not result["data"].empty:
            formatted += f"\n{result['description']}:\n"
            formatted += result["data"].to_string()
            formatted += "\n" + "=" * 50 + "\n"
        elif isinstance(result["data"], str):
            # Handle error messages
            formatted += f"\n{result['description']}: {result['data']}\n"
            formatted += "=" * 50 + "\n"

    return formatted


def format_results_for_api(sql_results) -> list[dict]:
    """
    Format SQL results for JSON API response.

    Args:
        sql_results: List of result dictionaries with 'description' and 'data' keys

    Returns:
        List of dictionaries with 'description' and 'data' keys (data as list of dicts)
    """
    formatted_data = []
    for result in sql_results:
        # Check if data is a DataFrame before calling .empty
        if isinstance(result["data"], pd.DataFrame):
            formatted_data.append(
                {
                    "description": result["description"],
                    "data": result["data"].to_dict("records")
                    if not result["data"].empty
                    else [],
                }
            )
        else:
            # Handle error messages (strings) or other types
            formatted_data.append(
                {
                    "description": result["description"],
                    "data": result["data"] if isinstance(result["data"], str) else [],
                }
            )
    return formatted_data
