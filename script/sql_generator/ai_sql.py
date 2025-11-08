"""
AISQLRunner - Main class for AI-powered SQL query generation and execution.
Handles conversational queries, SQL generation, execution, and result analysis.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import sys
from pathlib import Path
from .query_runner import SQLAnalysisRunner
from .ai_helpers import (
    classify_question_type,
    generate_sql_query,
    validate_sql_results,
    format_results_for_display,
    format_results_for_api,
)

# Import LangSmith configuration to enable tracing
sys.path.insert(0, str(Path(__file__).parent.parent))
from langsmith_config import setup_langsmith

load_dotenv()
setup_langsmith()


class AISQLRunner:
    """
    Main class for AI-powered SQL analysis.
    Handles question classification, SQL generation, execution, and result analysis.
    """

    def __init__(self):
        """Initialize the AI SQL runner."""
        # Check for required environment variables
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your environment or Render dashboard.")
        
        self.sql_runner = SQLAnalysisRunner()
        self.sql_results = None
        # Use LangChain ChatOpenAI for tracing
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                openai_api_key=openai_key
            )
            self.analysis_llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                openai_api_key=openai_key
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {str(e)}. Please check your OPENAI_API_KEY.")
        # Use LangChain messages instead of dict format
        self.chat_history = [
            SystemMessage(
                content="You are an experienced data analyst. Based on the SQL results provided, analyze the data and provide comprehensive findings. Focus on key insights, trends, and business implications."
            ),
        ]

    # ============================================================================
    # Core Methods for graph.py integration
    # ============================================================================

    def classification_prompt(self, prompt: str) -> str:
        """
        Classify question type. Used by graph.py.
        Returns: "sql" or "conversational"
        """
        question_type = classify_question_type(prompt)
        return "sql" if question_type == "SQL" else "conversational"

    def get_conversational_response(self, prompt: str) -> str:
        """
        Get conversational AI response. Used by graph.py.
        """
        self.chat_history.append(HumanMessage(content=prompt))
        response = self.llm.invoke(self.chat_history)
        content = response.content
        self.chat_history.append(AIMessage(content=content))
        return content

    def generate_sql(self, prompt: str) -> str:
        """
        Generate SQL query from natural language. Used by graph.py.
        """
        return generate_sql_query(prompt)

    def judge_sql_result(self, prompt: str, sql_results: list) -> str:
        """
        Judge if SQL results answer the question. Used by graph.py.
        Returns: "yes" or "no"
        """
        if not sql_results:
            return "no"

        results_summary = ""
        for result in sql_results:
            if "data" in result and not result["data"].empty:
                results_summary += (
                    f"{result['description']}: {len(result['data'])} rows\n"
                )
                results_summary += result["data"].head(10).to_string() + "\n\n"

        judge_prompt = f"""
        Evaluate if the SQL query results properly answer the user's question.
        Respond with ONLY "YES" or "NO".
        
        User question: "{prompt}"
        
        SQL Results:
        {results_summary}
        
        Does this data answer the user's question? YES or NO only.
        """

        # Use LangChain for tracing
        response = self.llm.invoke([HumanMessage(content=judge_prompt)])
        return response.content.strip().upper()

    def analyze_sql_results(self, prompt: str, sql_results: list, sql_query: str = None) -> str:
        """
        Analyze SQL results and generate insights. Used by graph.py.
        
        Args:
            prompt: The user's original question
            sql_results: The results from executing the SQL query
            sql_query: The SQL query that was executed (optional but recommended)
        """
        results_str = format_results_for_display(sql_results)
        
        # Build comprehensive context including SQL query
        analysis_prompt = f"""User Question: {prompt}

"""
        if sql_query:
            analysis_prompt += f"""SQL Query Executed:
{sql_query}

"""
        
        analysis_prompt += f"""SQL Query Results:
{results_str}

Please analyze these results and provide comprehensive insights, trends, and business implications based on the data. Reference specific numbers and patterns from the results."""
        
        self.chat_history.append(HumanMessage(content=analysis_prompt))
        
        # Use LangChain for tracing
        response = self.analysis_llm.invoke(self.chat_history)
        content = response.content
        self.chat_history.append(AIMessage(content=content))
        return content

    def generate_error_suggestion(
        self, prompt: str, sql_query: str, error_msg: str
    ) -> str:
        """
        Generate error suggestions. Used by graph.py.
        """
        error_prompt = f"""
        The SQL query failed with an error.
        
        User question: {prompt}
        SQL query: {sql_query}
        Error: {error_msg}
        
        Please suggest a corrected SQL query or explain what went wrong.
        """
        self.chat_history.append(HumanMessage(content=error_prompt))
        # Use LangChain for tracing
        response = self.llm.invoke(self.chat_history)
        content = response.content
        self.chat_history.append(AIMessage(content=content))
        return content

    # ============================================================================
    # Public API Methods
    # ============================================================================

    def ask_ai(self, prompt: str) -> str:
        """
        Main interactive method for CLI usage.
        Classifies question, executes SQL if needed, and returns response.
        """
        print("\n" + "=" * 80)
        print(f"AI ANALYST: {prompt}")
        print("=" * 80)

        question_type = classify_question_type(prompt)
        print(f"\nCLASSIFICATION RESULT: '{question_type}'")

        if question_type == "CONVERSATIONAL":
            return self._handle_conversational(prompt, verbose=True)
        else:
            return self._handle_sql_query(prompt, verbose=True)

    def ask_ai_api(self, prompt: str) -> dict:
        """
        API-friendly non-streaming version.
        Returns structured JSON response.
        """
        try:
            question_type = classify_question_type(prompt)

            if question_type == "CONVERSATIONAL":
                response = self._handle_conversational(prompt, verbose=False)
                return {
                    "status": "success",
                    "question_type": "conversational",
                    "prompt": prompt,
                    "response": response,
                    "sql_query": None,
                    "data": None,
                }
            else:
                return self._handle_sql_query_api(prompt)

        except Exception as e:
            return {
                "status": "error",
                "prompt": prompt,
                "error": str(e),
                "message": "An error occurred while processing your request",
            }

    def ask_ai_api_streaming(self, prompt: str):
        """
        API-friendly streaming version.
        Returns generator that yields streaming chunks.
        """
        try:
            question_type = classify_question_type(prompt)

            if question_type == "CONVERSATIONAL":
                return self._handle_conversational_streaming(prompt)
            else:
                return self._handle_sql_query_streaming(prompt)

        except Exception as e:

            def generate_error_stream():
                yield {
                    "type": "error",
                    "error": str(e),
                    "message": "An error occurred while processing your request",
                    "prompt": prompt,
                }

            return generate_error_stream()

    # ============================================================================
    # Private Helper Methods
    # ============================================================================

    def _handle_conversational(self, prompt: str, verbose: bool = False) -> str:
        """Handle conversational questions."""
        if verbose:
            print(f"\nCONVERSATIONAL RESPONSE:")
            print("=" * 60)

        response = self.get_conversational_response(prompt)

        if verbose:
            print(response)
            print("=" * 60)
            print("\n")

        return response

    def _handle_sql_query(self, prompt: str, verbose: bool = False) -> str:
        """Handle SQL-based questions with verbose output."""
        query = self.generate_sql(prompt)

        if verbose:
            print(f"\nGenerated SQL Query:")
            print("-" * 50)
            print(query)
            print("-" * 50)

        # Execute SQL
        try:
            self.sql_results = self.sql_runner.run_single_query(query, prompt)
        except Exception as e:
            if verbose:
                print(f"\nSQL EXECUTION ERROR:")
                print("=" * 60)
                print(f"Error: {str(e)}")
                print("=" * 60)
            return self.generate_error_suggestion(prompt, query, str(e))

        # Validate results
        is_valid, has_data, error_msg = validate_sql_results(self.sql_results)

        if not is_valid:
            if verbose:
                print(f"\nSQL QUERY FAILED:")
                print("=" * 60)
                print(f"Error: {error_msg}")
                print("=" * 60)
            return self.generate_error_suggestion(prompt, query, error_msg)

        if not has_data:
            if verbose:
                print(f"\nNO DATA RETURNED:")
                print("=" * 60)
                print("Query executed successfully but returned no rows")
                print("=" * 60)

            empty_prompt = f"""
            The SQL query executed but returned no data.
            
            User question: {prompt}
            SQL query: {query}
            
            Please either:
            1. Suggest why no data was returned and what the user might try instead
            2. Provide a modified query that might return results
            3. Explain if the data simply doesn't exist in the database
            """
            return self.get_conversational_response(empty_prompt)

        # Judge if results answer the question
        judge_result = self.judge_sql_result(prompt, self.sql_results)

        if verbose:
            print(f"\nJUDGE RESULT: {judge_result}")
            print(f"\nQUERY RESULTS:")
            print("=" * 60)
            for result in self.sql_results:
                print(f"\n{result['description']}:")
                print("-" * 40)
                print(result["data"])
                print("-" * 40)

        if judge_result == "YES":
            # Pass SQL query so AI can see what was executed
            analysis = self.analyze_sql_results(prompt, self.sql_results, sql_query=query)
            if verbose:
                print(f"\nAI ANALYSIS:")
                print("=" * 60)
                print(analysis)
                print("=" * 60)
                print("\n")
            return analysis
        else:
            # Results don't answer question
            if verbose:
                print(f"\nQUERY RESULTS (May not fully answer question):")
                print("=" * 60)

            results_summary = format_results_for_display(self.sql_results)
            retry_prompt = f"""
            The SQL query returned data but doesn't properly answer the user's question.
            
            Original question: {prompt}
            Generated SQL: {query}
            SQL Results: {results_summary}
            
            Please either:
            1. Suggest a better SQL query that would properly answer the question
            2. Explain what information is missing and why the current query doesn't work
            3. Provide insights from the available data if it's partially relevant
            """
            response = self.get_conversational_response(retry_prompt)

            if verbose:
                print(f"\nAI FEEDBACK:")
                print("=" * 60)
                print(response)
                print("=" * 60)
                print("\n")

            return response

    def _handle_sql_query_api(self, prompt: str) -> dict:
        """Handle SQL query for API (non-streaming)."""
        query = self.generate_sql(prompt)

        try:
            self.sql_results = self.sql_runner.run_single_query(query, prompt)
        except Exception as e:
            return {
                "status": "error",
                "question_type": "sql",
                "prompt": prompt,
                "error": str(e),
                "message": f"SQL execution failed: {str(e)}",
                "sql_query": query,
            }

        is_valid, has_data, error_msg = validate_sql_results(self.sql_results)

        if not is_valid or not has_data:
            return {
                "status": "error",
                "question_type": "sql",
                "prompt": prompt,
                "error": error_msg,
                "message": error_msg,
                "sql_query": query,
                "has_data": has_data,
            }

        formatted_data = format_results_for_api(self.sql_results)
        
        # Use analyze_sql_results which includes SQL query in context
        analysis = self.analyze_sql_results(prompt, self.sql_results, sql_query=query)

        return {
            "status": "success",
            "question_type": "sql",
            "prompt": prompt,
            "sql_query": query,
            "data": formatted_data,
            "analysis": analysis,
            "total_results": len(formatted_data),
        }

    def _handle_conversational_streaming(self, prompt: str):
        """Handle conversational questions with streaming."""

        self.chat_history.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.chat_history,
            stream=True,
            stream_options={"include_usage": True},
            temperature=0.7,
        )

        def generate_stream():
            full_content = ""
            usage_info = None

            try:
                for chunk in response:
                    if (
                        chunk.choices
                        and len(chunk.choices) > 0
                        and chunk.choices[0].delta.content is not None
                    ):
                        content = chunk.choices[0].delta.content
                        full_content += content
                        yield {
                            "type": "content",
                            "content": content,
                            "full_content": full_content,
                            "question_type": "conversational",
                            "prompt": prompt,
                        }

                    if hasattr(chunk, "usage") and chunk.usage:
                        usage_info = chunk.usage

                self.chat_history.append({"role": "assistant", "content": full_content})
                yield {
                    "type": "complete",
                    "full_content": full_content,
                    "usage": usage_info,
                    "question_type": "conversational",
                    "prompt": prompt,
                    "sql_query": None,
                    "data": None,
                }
            except Exception as e:
                yield {
                    "type": "error",
                    "error": str(e),
                    "message": "Error during streaming response",
                }

        return generate_stream()

    def _handle_sql_query_streaming(self, prompt: str):
        """Handle SQL query with streaming."""
        query = self.generate_sql(prompt)

        try:
            self.sql_results = self.sql_runner.run_single_query(query, prompt)
        except Exception as e:

            def generate_error_stream():
                yield {
                    "type": "error",
                    "error": str(e),
                    "message": f"SQL execution failed: {str(e)}",
                    "sql_query": query,
                }

            return generate_error_stream()

        is_valid, has_data, error_msg = validate_sql_results(self.sql_results)

        if not is_valid or not has_data:

            def generate_error_stream():
                yield {
                    "type": "error",
                    "error": error_msg,
                    "message": error_msg,
                    "sql_query": query,
                    "has_data": has_data,
                }

            return generate_error_stream()

        formatted_data = format_results_for_api(self.sql_results)
        results_str = format_results_for_display(self.sql_results)

        self.chat_history.append(
            {
                "role": "user",
                "content": f"Here are the SQL query results:\n{results_str}\nUser question: {prompt}",
            }
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.chat_history,
            stream=True,
            stream_options={"include_usage": True},
        )

        def generate_stream():
            full_content = ""
            usage_info = None

            try:
                for chunk in response:
                    if (
                        chunk.choices
                        and len(chunk.choices) > 0
                        and chunk.choices[0].delta.content is not None
                    ):
                        content = chunk.choices[0].delta.content
                        full_content += content
                        yield {
                            "type": "analysis",
                            "content": content,
                            "full_content": full_content,
                            "sql_query": query,
                            "data": formatted_data,
                            "question_type": "sql",
                            "prompt": prompt,
                        }

                    if hasattr(chunk, "usage") and chunk.usage:
                        usage_info = chunk.usage

                self.chat_history.append({"role": "assistant", "content": full_content})
                yield {
                    "type": "complete",
                    "full_content": full_content,
                    "sql_query": query,
                    "data": formatted_data,
                    "usage": usage_info,
                    "question_type": "sql",
                    "prompt": prompt,
                    "total_results": len(formatted_data),
                }
            except Exception as e:
                yield {
                    "type": "error",
                    "error": str(e),
                    "message": "Error during streaming analysis",
                }

        return generate_stream()


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    ai = AISQLRunner()

    while True:
        print(
            "ask me questions about e-commerce dataset! Type 'exit' or 'end' to exit!"
        )
        user_input = input("You: ")

        if user_input.lower() in ["exit", "end"]:
            print("goodbye!")
            break

        ai.ask_ai(prompt=user_input)
