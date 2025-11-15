from dotenv import load_dotenv
import os
import json
import sys
from pathlib import Path
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool

# Import LangSmith configuration to enable tracing
sys.path.insert(0, str(Path(__file__).parent.parent))
from langsmith_config import setup_langsmith

from chatbot.tools import call_functions

load_dotenv()
setup_langsmith()

# Use LangChain ChatOpenAI for tracing
llm = ChatOpenAI(
    model="gpt-4o-mini", temperature=0, openai_api_key=os.environ.get("OPENAI_API_KEY")
)


class OrderResponse(BaseModel):
    answer: str = Field(
        description="The answer to the user's question about their orders or policies."
    )


# Define tool input schemas
class FAQInput(BaseModel):
    question: str = Field(
        description="The question to search for in the FAQ knowledge base"
    )


class GetOrdersInput(BaseModel):
    customer_id: int = Field(description="The customer's ID")
    limit: int = Field(default=10, description="The number of orders to return")


class GetReviewsInput(BaseModel):
    product_id: int = Field(description="The product's ID")
    limit: int = Field(default=10, description="The number of reviews to return")


class QueryPoliciesInput(BaseModel):
    query_text: str = Field(
        description="A question or phrase describing the user's return/shipping policy information request"
    )
    limit: int = Field(
        default=3, description="The number of policy document chunks to return"
    )


# Define tool wrapper functions
def faq_wrapper(question: str) -> str:
    """Get information about FAQ and company policies"""
    result = call_functions("faq", {"question": question})
    return json.dumps(result) if isinstance(result, (dict, list)) else str(result)


def get_my_orders_wrapper(customer_id: int, limit: int = 10) -> str:
    """Get the customer's orders"""
    result = call_functions(
        "get_my_orders", {"customer_id": customer_id, "limit": limit}
    )
    return json.dumps(result) if isinstance(result, (dict, list)) else str(result)


def get_product_reviews_wrapper(product_id: int, limit: int = 10) -> str:
    """Get the product reviews"""
    result = call_functions(
        "get_product_reviews", {"product_id": product_id, "limit": limit}
    )
    return json.dumps(result) if isinstance(result, (dict, list)) else str(result)


def query_policies_docs_wrapper(query_text: str, limit: int = 3) -> str:
    """Retrieve return and shipping policy documents relevant to the user's question"""
    result = call_functions(
        "query_policies_docs", {"query_text": query_text, "limit": limit}
    )
    return json.dumps(result) if isinstance(result, (dict, list)) else str(result)


tools = [
    StructuredTool.from_function(
        func=faq_wrapper,
        name="faq",
        description="Get information about FAQ and company policies",
        args_schema=FAQInput,
    ),
    StructuredTool.from_function(
        func=get_my_orders_wrapper,
        name="get_my_orders",
        description="Get the customer's orders",
        args_schema=GetOrdersInput,
    ),
    StructuredTool.from_function(
        func=get_product_reviews_wrapper,
        name="get_product_reviews",
        description="Get the product reviews",
        args_schema=GetReviewsInput,
    ),
    StructuredTool.from_function(
        func=query_policies_docs_wrapper,
        name="query_policies_docs",
        description="Retrieve return and shipping policy documents relevant to the user's question",
        args_schema=QueryPoliciesInput,
    ),
]

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)


def chatbot(prompt, max_attempts=5, conversation_messages=None):
    """
    Chat with the customer service chatbot using LangChain for tracing.

    Args:
        prompt: User's question/request
        max_attempts: Maximum number of tool-calling iterations
        conversation_messages: Optional list of previous messages for multi-turn conversations.
                              If None, starts a new conversation.

    Returns:
        tuple: (answer, chat_response, response)
    """
    # Initialize messages - start fresh if no conversation history provided
    if conversation_messages is None:
        messages = [
            SystemMessage(content="you are a helpful chatbot for e-commerce"),
        ]
    else:
        messages = conversation_messages.copy()

    # Add user message
    messages.append(HumanMessage(content=prompt))

    iteration = 0
    while iteration < max_attempts:
        # Call LLM with tools (this will be traced by LangSmith)
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        # Check if there are tool calls
        if response.tool_calls:
            print(f"--- Iteration {iteration + 1} ---")

            # Execute all tool calls
            for tool_call in response.tool_calls:
                name = tool_call["name"]
                args = tool_call["args"]
                print(f"Tool Call: {name} with args: {args}")

                # Execute tool
                tool_result = call_functions(name, args)
                print(f"Tool Result: {json.dumps(tool_result, indent=2)[:200]}...")

                # Add tool result to messages
                messages.append(
                    ToolMessage(
                        content=json.dumps(tool_result)
                        if isinstance(tool_result, (dict, list))
                        else str(tool_result),
                        tool_call_id=tool_call["id"],
                    )
                )

            iteration += 1
        else:
            # No more tool calls, we have the final answer
            print("No more tool calls - final answer received")
            answer = response.content if hasattr(response, "content") else str(response)
            return answer, response, response

    # If we hit max attempts, return what we have
    print(f"Max attempts ({max_attempts}) reached")
    answer = response.content if hasattr(response, "content") else str(response)
    return answer, response, response
