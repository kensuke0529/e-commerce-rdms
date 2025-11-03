"""
Generate PNG diagram for chatbot tool-call flow
"""

import os
from pathlib import Path

USE_PYGRAPHVIZ = False
USE_GRAPHVIZ = False

try:
    import pygraphviz as pgv
    USE_PYGRAPHVIZ = True
except ImportError:
    print("pygraphviz not available, trying alternative method...")
    try:
        from graphviz import Digraph
        USE_GRAPHVIZ = True
    except ImportError:
        print("graphviz not available. Please install pygraphviz or graphviz.")


def generate_chatbot_diagram():
    """Generate chatbot tool-call flow diagram as PNG"""
    
    # Set up output directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    output_dir = project_root / "result" / "image"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "chatbot_tool_call_flow.png"
    
    if USE_PYGRAPHVIZ:
        # Create graph using pygraphviz
        G = pgv.AGraph(
            directed=True,
            strict=False,
            rankdir="TB",
            nodesep=0.5,
            ranksep=0.8,
            fontname="Arial",
            fontsize=10,
        )
        
        # Add nodes
        G.add_node("User", shape="ellipse", style="filled", fillcolor="#e1f5ff")
        G.add_node("Chatbot Entry", shape="box", style="filled", fillcolor="#fff4e1")
        G.add_node("LLM", shape="box", style="filled", fillcolor="#e8f5e9")
        G.add_node("Decision", shape="diamond", style="filled", fillcolor="#fce4ec")
        G.add_node("Final Answer", shape="box", style="filled", fillcolor="#e1f5ff")
        G.add_node("Execute Tools", shape="box", style="filled", fillcolor="#fff9c4")
        
        # Tool nodes
        G.add_node("FAQ Tool", shape="box", style="filled", fillcolor="#f3e5f5")
        G.add_node("Orders Tool", shape="box", style="filled", fillcolor="#f3e5f5")
        G.add_node("Reviews Tool", shape="box", style="filled", fillcolor="#f3e5f5")
        G.add_node("Policies Tool", shape="box", style="filled", fillcolor="#f3e5f5")
        
        # RAG process
        G.add_node("ChromaDB Search", shape="box", style="filled", fillcolor="#e3f2fd")
        
        # Results
        G.add_node("Tool Results", shape="box", style="filled", fillcolor="#fff9c4")
        G.add_node("Append Message", shape="box", style="filled", fillcolor="#e8f5e9")
        
        # Add edges
        G.add_edge("User", "Chatbot Entry")
        G.add_edge("Chatbot Entry", "LLM")
        G.add_edge("LLM", "Decision")
        G.add_edge("Decision", "Final Answer", label="No tool calls")
        G.add_edge("Decision", "Execute Tools", label="Has tool calls")
        G.add_edge("Execute Tools", "FAQ Tool")
        G.add_edge("Execute Tools", "Orders Tool")
        G.add_edge("Execute Tools", "Reviews Tool")
        G.add_edge("Execute Tools", "Policies Tool")
        G.add_edge("Policies Tool", "ChromaDB Search")
        G.add_edge("FAQ Tool", "Tool Results")
        G.add_edge("Orders Tool", "Tool Results")
        G.add_edge("Reviews Tool", "Tool Results")
        G.add_edge("ChromaDB Search", "Tool Results")
        G.add_edge("Tool Results", "Append Message")
        G.add_edge("Append Message", "LLM", label="Iterate (max_attempts)")
        
        # Layout and render
        G.layout(prog="dot")
        G.draw(str(output_path))
        print(f"Chatbot flow diagram PNG written to: {output_path}")
        
    elif USE_GRAPHVIZ:
        # Use graphviz library
        dot = Digraph(comment="Chatbot Tool-Call Flow")
        dot.attr(rankdir="TB", nodesep="0.5", ranksep="0.8")
        dot.attr("node", fontname="Arial", fontsize="10")
        
        # Add nodes
        dot.node("User", "User", shape="ellipse", style="filled", fillcolor="#e1f5ff")
        dot.node("Chatbot Entry", "Chatbot Entry", shape="box", style="filled", fillcolor="#fff4e1")
        dot.node("LLM", "LLM with Tools\n(LangChain)", shape="box", style="filled", fillcolor="#e8f5e9")
        dot.node("Decision", "Any tool\ncalls?", shape="diamond", style="filled", fillcolor="#fce4ec")
        dot.node("Final Answer", "Return final\nanswer", shape="box", style="filled", fillcolor="#e1f5ff")
        dot.node("Execute Tools", "Execute tool\ncall(s)", shape="box", style="filled", fillcolor="#fff9c4")
        
        # Tool nodes
        dot.node("FAQ Tool", "faq →\ncall_functions(\"faq\")", shape="box", style="filled", fillcolor="#f3e5f5")
        dot.node("Orders Tool", "get_my_orders →\ncall_functions(\"get_my_orders\")", shape="box", style="filled", fillcolor="#f3e5f5")
        dot.node("Reviews Tool", "get_product_reviews →\ncall_functions(\"get_product_reviews\")", shape="box", style="filled", fillcolor="#f3e5f5")
        dot.node("Policies Tool", "query_policies_docs →\ncall_functions(\"query_policies_docs\")", shape="box", style="filled", fillcolor="#f3e5f5")
        
        # RAG process
        dot.node("ChromaDB Search", "Embeddings +\nChromaDB search", shape="box", style="filled", fillcolor="#e3f2fd")
        
        # Results
        dot.node("Tool Results", "Tool Results", shape="box", style="filled", fillcolor="#fff9c4")
        dot.node("Append Message", "Append ToolMessage\nto messages", shape="box", style="filled", fillcolor="#e8f5e9")
        
        # Add edges
        dot.edge("User", "Chatbot Entry")
        dot.edge("Chatbot Entry", "LLM")
        dot.edge("LLM", "Decision")
        dot.edge("Decision", "Final Answer", label="No")
        dot.edge("Decision", "Execute Tools", label="Yes")
        dot.edge("Execute Tools", "FAQ Tool")
        dot.edge("Execute Tools", "Orders Tool")
        dot.edge("Execute Tools", "Reviews Tool")
        dot.edge("Execute Tools", "Policies Tool")
        dot.edge("Policies Tool", "ChromaDB Search")
        dot.edge("FAQ Tool", "Tool Results")
        dot.edge("Orders Tool", "Tool Results")
        dot.edge("Reviews Tool", "Tool Results")
        dot.edge("ChromaDB Search", "Tool Results")
        dot.edge("Tool Results", "Append Message")
        dot.edge("Append Message", "LLM", label="Iterate (max_attempts)")
        
        # Render
        dot.render(str(output_path).replace(".png", ""), format="png", cleanup=True)
        print(f"Chatbot flow diagram PNG written to: {output_path}")
        
    else:
        print("Cannot generate diagram - graphviz or pygraphviz not available")
        print("Please install: pip install pygraphviz OR pip install graphviz")
        return False
    
    return True


if __name__ == "__main__":
    generate_chatbot_diagram()

