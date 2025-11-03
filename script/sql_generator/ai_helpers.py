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
    openai_api_key=os.environ.get("OPENAI_API_KEY")
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
    You are a SQL expert. Generate a PostgreSQL query based on the user's question.
    
    Database Schema:
    {schema_info}
    
    User Question: "{prompt}"
    
    Instructions:
    - Generate only valid PostgreSQL SQL
    - Do not include comments or explanations
    - Use proper JOINs and WHERE clauses
    - Return only the SQL query, nothing else
    - Use parameterized queries style with %s if needed, but for this output use direct values
    - Ensure proper table and column names from the schema
    
    SQL Query:
    """

    try:
        # Use LangChain for tracing (lower temperature for SQL generation)
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
        if not result["data"].empty:
            formatted += f"\n{result['description']}:\n"
            formatted += result["data"].to_string()
            formatted += "\n" + "=" * 50 + "\n"

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
        formatted_data.append(
            {
                "description": result["description"],
                "data": result["data"].to_dict("records")
                if not result["data"].empty
                else [],
            }
        )
    return formatted_data
