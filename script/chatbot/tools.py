from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal

from rag.embedding import query_policies_docs
from sql_generator.sql_via_python import query_executor

load_dotenv()
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def convert_to_json_serializable(obj):
    """Recursively convert non-JSON serializable objects to serializable types"""
    if obj is None:
        return None

    # Handle datetime/date types - check both isinstance and duck typing
    try:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        # Check for datetime-like objects by method (handles psycopg2 datetime types)
        elif hasattr(obj, "isoformat") and callable(getattr(obj, "isoformat")):
            return obj.isoformat()
        # Fallback for datetime-like objects with strftime
        elif hasattr(obj, "strftime") and callable(getattr(obj, "strftime")):
            return obj.isoformat() if hasattr(obj, "isoformat") else str(obj)
    except (AttributeError, TypeError, ValueError):
        pass

    # Handle Decimal types
    if isinstance(obj, Decimal):
        return float(obj)

    # Handle collections
    if isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_json_serializable(item) for item in obj]

    # Handle other types - check class name for datetime-like types
    obj_type = type(obj).__name__.lower()
    if "datetime" in obj_type or "date" in obj_type or "time" in obj_type:
        try:
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            elif hasattr(obj, "strftime"):
                return obj.strftime("%Y-%m-%dT%H:%M:%S")
        except (AttributeError, TypeError, ValueError):
            return str(obj)

    # Return as-is for basic JSON-serializable types (str, int, float, bool)
    return obj


def faq(question):
    """rag FAQ"""
    # Use path relative to script directory
    kb_path = Path(__file__).parent / "kb.json"
    with open(kb_path, "r") as f:
        return json.load(f)


def get_my_orders(customer_id, limit=10):
    """Get customer's orders"""
    try:
        customer_id = int(customer_id)
        limit = int(limit)
        if limit <= 0:
            limit = 10
        if limit > 50:
            limit = 50
    except (ValueError, TypeError):
        return {"error": "Invalid customer_id or limit parameter", "data": []}

    # Build query with parameterized values (using psycopg2's %s placeholder)
    query = """
    SELECT 
        oh.order_id,
        oh.order_date,
        oh.quantity,
        p.product_name,
        p.product_price,
        p.category,
        COALESCE(pay.amount, 0) as payment_amount,
        s.carrier as shipping_carrier,
        s.shipping_date
    FROM order_header oh
    JOIN product p ON oh.product_id = p.product_id
    LEFT JOIN payment pay ON oh.order_id = pay.order_id
    LEFT JOIN shipping s ON oh.shipping_id = s.shipping_id
    WHERE oh.customer_id = %s
    ORDER BY oh.order_date DESC
    LIMIT %s
    """

    db = None
    try:
        # Create executor with placeholder query, we'll execute manually with parameters
        db = query_executor("")
        if not db.connect_to_db():
            return {"error": "Failed to connect to database", "data": []}

        # Execute with parameterized query (prevents SQL injection)
        db.cur.execute(query, (customer_id, limit))
        results = db.cur.fetchall()

        # Get column names for better data structure
        columns = [desc[0] for desc in db.cur.description] if db.cur.description else []

        # Format results as list of dictionaries, converting non-JSON types
        formatted_results = []
        if results and columns:
            for row in results:
                row_dict = {}
                for col, val in zip(columns, row):
                    # Use helper function to ensure JSON serializability
                    row_dict[col] = convert_to_json_serializable(val)
                formatted_results.append(row_dict)

        # Ensure the return dictionary is also JSON serializable
        result = {"data": formatted_results, "count": len(formatted_results)}
        return convert_to_json_serializable(result)

    except Exception as e:
        print(f"-- Error in get_my_orders: {e} --")
        return {"error": str(e), "data": []}

    finally:
        if db:
            db.close()


def get_product_reviews(product_id, limit=10):
    product_id = int(product_id)

    query = """
    select 
    from product as p
    join customer_review as cr on p.product_id = cr.product_id
    where p.product_id = %s
    order by cr.review_date desc
    limit 10;
    """

    db = None
    try:
        # Create executor with placeholder query, we'll execute manually with parameters
        db = query_executor("")
        if not db.connect_to_db():
            return {"error": "Failed to connect to database", "data": []}

        # Execute with parameterized query (prevents SQL injection)
        db.cur.execute(query, (product_id, limit))
        results = db.cur.fetchall()

        # Get column names for better data structure
        columns = [desc[0] for desc in db.cur.description] if db.cur.description else []

        # Format results as list of dictionaries, converting non-JSON types
        formatted_results = []
        if results and columns:
            for row in results:
                row_dict = {}
                for col, val in zip(columns, row):
                    # Use helper function to ensure JSON serializability
                    row_dict[col] = convert_to_json_serializable(val)
                formatted_results.append(row_dict)

        # Ensure the return dictionary is also JSON serializable
        result = {"data": formatted_results, "count": len(formatted_results)}
        return convert_to_json_serializable(result)

    except Exception as e:
        print(f"-- Error in get_my_orders: {e} --")
        return {"error": str(e), "data": []}

    finally:
        if db:
            db.close()


def call_functions(name, args):
    """Execute the appropriate function based on name"""
    if name == "faq":
        return faq(**args)
    elif name == "get_my_orders":
        return get_my_orders(**args)
    elif name == "query_policies_docs":
        result = query_policies_docs(**args)
        # If result is empty, return a helpful message instead
        if not result or (isinstance(result, list) and len(result) == 0):
            return {
                "message": "No policy documents found in the knowledge base. The policy documents may not be initialized yet.",
                "documents": []
            }
        return result
    elif name == "get_product_reviews":
        return get_product_reviews(**args)
    return None
