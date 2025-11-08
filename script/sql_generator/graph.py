import os
from typing import TypedDict, Optional, Literal, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from .ai_sql import AISQLRunner


class GraphState(TypedDict, total=False):
    """State that flows through the graph"""

    user_question: str
    question_type: Optional[Literal["sql", "conversational"]]
    sql_query: Optional[str]
    sql_results: Optional[List[Dict[str, Any]]]
    error_type: Optional[str]  # NEW: tracks what went wrong
    error_message: Optional[str]
    judge_result: Optional[Literal["yes", "no"]]
    final_response: str
    retry_count: int
    max_retries: int


def classify_node(state: GraphState, config: RunnableConfig) -> dict:
    """Classify if question needs SQL or is conversational"""
    print("\n[NODE: CLASSIFY]")
    ai_runner = config["configurable"]["ai_runner"]

    question_type = ai_runner.classification_prompt(state["user_question"])
    print(f"Classification: {question_type}")

    return {
        "question_type": question_type.lower(),
        "retry_count": 0,
        "max_retries": config["configurable"].get("max_retries", 2),
    }


def conversational_node(state: GraphState, config: RunnableConfig) -> dict:
    """Handle conversational questions"""
    print("\n[NODE: CONVERSATIONAL]")
    ai_runner = config["configurable"]["ai_runner"]

    response = ai_runner.get_conversational_response(state["user_question"])

    return {"final_response": response}


def generate_sql_node(state: GraphState, config: RunnableConfig) -> dict:
    """Generate SQL query"""
    print(f"\n[NODE: GENERATE_SQL] (Attempt {state.get('retry_count', 0) + 1})")
    ai_runner = config["configurable"]["ai_runner"]

    sql_query = ai_runner.generate_sql(state["user_question"])

    return {"sql_query": sql_query}


def execute_sql_node(state: GraphState, config: RunnableConfig) -> dict:
    """Execute the SQL query"""
    print("\n[NODE: EXECUTE_SQL]")
    ai_runner = config["configurable"]["ai_runner"]

    try:
        results = ai_runner.sql_runner.run_single_query(
            state["sql_query"], state["user_question"]
        )
        print("Execution successful")

        if not results or len(results) == 0:
            return {
                "sql_results": results,
                "error_type": "no_data",
                "error_message": "Query executed but returned no results",
            }
        
        # Check if results contain error messages (string data indicates error)
        has_error = False
        error_messages = []
        for result in results:
            if isinstance(result.get("data"), str) and ("error" in result.get("data", "").lower() or "failed" in result.get("data", "").lower()):
                has_error = True
                error_messages.append(result.get("data", "Unknown error"))
        
        if has_error:
            error_msg = "; ".join(error_messages)
            print(f"  Execution returned errors: {error_msg}")
            return {
                "sql_results": results,
                "error_type": "execution_error",
                "error_message": error_msg,
            }

        return {"sql_results": results, "error_type": None, "error_message": None}

    except ConnectionError as e:
        error_msg = f"Database connection failed: {str(e)}"
        print(f"  {error_msg}")
        return {
            "sql_results": None,
            "error_type": "execution_error",
            "error_message": error_msg,
        }
    except Exception as e:
        error_msg = f"SQL execution failed: {str(e)}"
        print(f"  {error_msg}")
        return {
            "sql_results": None,
            "error_type": "execution_error",
            "error_message": error_msg,
        }


def judge_results_node(state: GraphState, config: RunnableConfig) -> dict:
    """Judge if results answer the question"""
    print("\n[NODE: JUDGE_RESULTS]")
    ai_runner = config["configurable"]["ai_runner"]

    judge_result = ai_runner.judge_sql_result(
        state["user_question"], state["sql_results"]
    )
    print(f"  Judge says: {judge_result}")

    # If judge says NO, mark it as an error type
    if judge_result.lower() == "no":
        return {
            "judge_result": "no",
            "error_type": "invalid_results",
            "error_message": "Results don't answer the question",
        }

    return {"judge_result": judge_result.lower(), "error_type": None}


def analyze_data_node(state: GraphState, config: RunnableConfig) -> dict:
    """Generate analysis from SQL results"""
    print("\n[NODE: ANALYZE_DATA]")
    ai_runner = config["configurable"]["ai_runner"]

    analysis = ai_runner.analyze_sql_results(
        state["user_question"], state["sql_results"]
    )

    return {"final_response": analysis}


def handle_error_node(state: GraphState, config: RunnableConfig) -> dict:
    """Decides whether to retry or give up"""

    print("\n[NODE: HANDLE_ERROR]")
    ai_runner = config["configurable"]["ai_runner"]

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)
    error_type = state.get("error_type", "unknown")
    error_msg = state.get("error_message", "Unknown error")

    print(f"  Error type: {error_type}")
    print(f"  Retry: {retry_count}/{max_retries}")

    # Check if we should retry
    if retry_count < max_retries:
        print("  → Will retry")
        return {
            "retry_count": retry_count + 1,
            "final_response": None,  # Clear any previous response
        }

    # Max retries reached - generate final error response
    print("  → Max retries reached, generating final response")

    # Generate appropriate error message based on error type
    if error_type == "execution_error":
        response = ai_runner.generate_error_suggestion(
            state["user_question"],
            state.get("sql_query", "No query generated"),
            error_msg,
        )
    elif error_type == "no_data":
        prompt = (
            f"The SQL query executed successfully but returned no data for: "
            f"'{state['user_question']}'. Query: {state['sql_query']}. "
            f"Explain why and suggest alternatives."
        )
        response = ai_runner.get_conversational_response(prompt)
    elif error_type == "invalid_results":
        # Check if this is a multi-part question
        question = state['user_question'].lower()
        is_multi_part = any(keyword in question for keyword in ['and', 'also', 'show me', 'what is', 'who is'])
        
        if is_multi_part:
            # Create an enhanced prompt that includes the original question with explicit instructions
            enhanced_prompt = (
                f"{state['user_question']} "
                f"IMPORTANT: This is a multi-part question. Generate a SQL query using CTEs and UNION ALL "
                f"to answer ALL parts. For example, if asking for top state, top customer, and top item, "
                f"create separate CTEs for each (top_state, top_customer, top_item) and combine with UNION ALL."
            )
            # Try to generate a better SQL query
            try:
                better_query = ai_runner.generate_sql(enhanced_prompt)
                # Execute the better query
                try:
                    better_results = ai_runner.sql_runner.run_single_query(
                        better_query, state['user_question']
                    )
                    if better_results and len(better_results) > 0:
                        # Check if better results answer the question
                        better_judge = ai_runner.judge_sql_result(state['user_question'], better_results)
                        if better_judge.upper() == "YES":
                            # Analyze the better results
                            analysis = ai_runner.analyze_sql_results(state['user_question'], better_results)
                            return {
                                "final_response": analysis,
                                "sql_query": better_query,
                                "sql_results": better_results,
                            }
                except Exception as e:
                    print(f"  Better query execution failed: {e}")
            except Exception as e:
                print(f"  Failed to generate better query: {e}")
        
        # Fallback to conversational response
        prompt = (
            f"After {max_retries} attempts, queries returned data but didn't fully answer: "
            f"'{state['user_question']}'. Last query: {state.get('sql_query', 'No query')}. "
            f"Please explain what information is available and what might be missing. "
            f"If this was a multi-part question, suggest how to break it down into separate queries."
        )
        response = ai_runner.get_conversational_response(prompt)
    else:
        response = f"I encountered an error: {error_msg}"

    return {"final_response": response}


# Route
def route_after_classification(state: GraphState) -> str:
    """Route based on question type"""
    if state["question_type"] == "conversational":
        return "conversational"
    return "generate_sql"


def route_after_execution(state: GraphState) -> str:
    """Route based on execution results"""
    if state.get("error_type"):
        return "handle_error"  # Any error goes to unified handler
    return "judge"


def route_after_judge(state: GraphState) -> str:
    """Route based on judge result"""
    if state.get("error_type"):
        return "handle_error"  # Judge said NO
    return "analyze"


def route_after_error(state: GraphState) -> Literal["generate_sql", "end"]:
    """Route after error - retry or end"""
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    if retry_count < max_retries and not state.get("final_response"):
        return "generate_sql"  # Retry
    return "end"


# Graph
def build_sql_agent_graph():
    """Build the SQL agent graph"""

    workflow = StateGraph(GraphState)

    # Add nodes (notice: only ONE error handler!)
    workflow.add_node("classify", classify_node)
    workflow.add_node("conversational", conversational_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("judge", judge_results_node)
    workflow.add_node("analyze", analyze_data_node)
    workflow.add_node("handle_error", handle_error_node)  # ONE handler for all errors!

    # Set entry point
    workflow.set_entry_point("classify")

    workflow.add_conditional_edges(
        "classify",
        route_after_classification,
        {"conversational": "conversational", "generate_sql": "generate_sql"},
    )

    workflow.add_conditional_edges(
        "execute_sql",
        route_after_execution,
        {"handle_error": "handle_error", "judge": "judge"},
    )

    workflow.add_conditional_edges(
        "judge",
        route_after_judge,
        {"handle_error": "handle_error", "analyze": "analyze"},
    )

    # Error handler can retry or end
    workflow.add_conditional_edges(
        "handle_error",
        route_after_error,
        {"generate_sql": "generate_sql", "end": END},
    )

    # Add sequential edges
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_edge("conversational", END)
    workflow.add_edge("analyze", END)

    print("[SIMPLIFIED GRAPH BUILT]")
    return workflow.compile()


# ============================================================================
# Usage Example
# ============================================================================


def run_sql_agent(user_question: str, ai_runner: AISQLRunner, max_retries: int = 2):
    """
    Run the SQL agent with a user question

    Args:
        user_question: The user's natural language question
        ai_runner: Instance of AISQLRunner
        max_retries: Maximum retry attempts (default: 2)

    Returns:
        Final state with response
    """
    app = build_sql_agent_graph()

    initial_state = {
        "user_question": user_question,
        "retry_count": 0,
        "max_retries": max_retries,
    }

    config = {"configurable": {"ai_runner": ai_runner, "max_retries": max_retries}}

    result = app.invoke(initial_state, config)

    return result


if __name__ == "__main__":
    try:
        app = build_sql_agent_graph()
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "result", "image"
        )
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "sql_agent_graph_simplified.png")

        app.get_graph().draw_png(output_path)
        print(f"\nGraph PNG written to: {output_path}")
    except Exception as e:
        print(f"Failed to render graph PNG: {e}")
