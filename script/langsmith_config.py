"""
LangSmith Configuration and Setup
Enables tracing and monitoring for LangChain components.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def setup_langsmith():
    """
    Configure LangSmith tracing environment variables.
    Set these in your .env file:
    - LANGCHAIN_TRACING_V2=true
    - LANGCHAIN_API_KEY=your_langsmith_api_key
    - LANGCHAIN_PROJECT=rdms (optional, defaults to 'rdms')
    """
    # Enable LangSmith tracing
    if os.environ.get("LANGCHAIN_TRACING_V2") != "true":
        os.environ["LANGCHAIN_TRACING_V2"] = "true"

    # Set project name if not already set
    if not os.environ.get("LANGCHAIN_PROJECT"):
        os.environ["LANGCHAIN_PROJECT"] = os.environ.get("LANGCHAIN_PROJECT", "rdms")

    # Check if API key is set
    api_key = os.environ.get("LANGCHAIN_API_KEY")
    if not api_key:
        print(
            "Warning: LANGCHAIN_API_KEY not found in environment variables. "
            "LangSmith tracing will not work without an API key. "
            "Get your API key from https://smith.langchain.com/"
        )
        return False

    print(
        f"LangSmith tracing enabled for project: {os.environ.get('LANGCHAIN_PROJECT')}"
    )
    return True


# Auto-setup when module is imported
if __name__ != "__main__":
    setup_langsmith()
