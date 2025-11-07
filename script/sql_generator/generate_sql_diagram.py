"""
Generate PNG diagram for SQL Generator workflow
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


def generate_sql_diagram():
    """Generate SQL Generator workflow diagram as PNG"""

    # Set up output directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    output_dir = project_root / "result" / "image"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "sql_agent_graph_simplified.png"

    if USE_PYGRAPHVIZ:
        # Create graph using pygraphviz
        G = pgv.AGraph(
            directed=True,
            strict=False,
            rankdir="TB",
            nodesep=0.5,
            ranksep=0.4,
            fontname="Arial",
            fontsize=10,
        )

        # Add nodes
        G.add_node("User", shape="ellipse", style="filled", fillcolor="#e1f5ff", label="User Question")
        G.add_node("Classify", shape="diamond", style="filled", fillcolor="#fce4ec", label="Classify\nQuestion Type")
        G.add_node("Conversational", shape="box", style="filled", fillcolor="#e8f5e9", label="Conversational\nResponse")
        G.add_node("GenerateSQL", shape="box", style="filled", fillcolor="#fff9c4", label="Generate\nSQL Query")
        G.add_node("ExecuteSQL", shape="box", style="filled", fillcolor="#fff9c4", label="Execute\nQuery")
        G.add_node("Judge", shape="diamond", style="filled", fillcolor="#fce4ec", label="Validate\nResults")
        G.add_node("Analyze", shape="box", style="filled", fillcolor="#e8f5e9", label="Analyze\nResults")
        G.add_node("HandleError", shape="box", style="filled", fillcolor="#ffcccb", label="Handle\nError")
        G.add_node("End", shape="ellipse", style="filled", fillcolor="#e1f5ff", label="Final\nResponse")

        # Add edges
        G.add_edge("User", "Classify")
        G.add_edge("Classify", "Conversational")
        G.add_edge("Classify", "GenerateSQL", label="SQL")
        G.add_edge("GenerateSQL", "ExecuteSQL")
        G.add_edge("ExecuteSQL", "HandleError", label="Error")
        G.add_edge("ExecuteSQL", "Judge", label="Success")
        G.add_edge("Judge", "HandleError", label="Invalid")
        G.add_edge("Judge", "Analyze", label="Valid")
        G.add_edge("HandleError", "GenerateSQL", label="Retry")
        G.add_edge("HandleError", "End", label="Max Retries")
        G.add_edge("Conversational", "End")
        G.add_edge("Analyze", "End")

        # Layout and render
        G.layout(prog="dot")
        G.draw(str(output_path))
        print(f"SQL Generator flow diagram PNG written to: {output_path}")

    elif USE_GRAPHVIZ:
        # Use graphviz library
        dot = Digraph(comment="SQL Generator Workflow")
        dot.attr(rankdir="TB", nodesep="0.5", ranksep="0.4")
        dot.attr("node", fontname="Arial", fontsize="10")

        # Add nodes
        dot.node("User", "User Question", shape="ellipse", style="filled", fillcolor="#e1f5ff")
        dot.node(
            "Classify",
            "Classify\nQuestion Type",
            shape="diamond",
            style="filled",
            fillcolor="#fce4ec",
        )
        dot.node(
            "Conversational",
            "Conversational\nResponse",
            shape="box",
            style="filled",
            fillcolor="#e8f5e9",
        )
        dot.node(
            "GenerateSQL",
            "Generate\nSQL Query",
            shape="box",
            style="filled",
            fillcolor="#fff9c4",
        )
        dot.node(
            "ExecuteSQL",
            "Execute\nQuery",
            shape="box",
            style="filled",
            fillcolor="#fff9c4",
        )
        dot.node(
            "Judge",
            "Validate\nResults",
            shape="diamond",
            style="filled",
            fillcolor="#fce4ec",
        )
        dot.node(
            "Analyze",
            "Analyze\nResults",
            shape="box",
            style="filled",
            fillcolor="#e8f5e9",
        )
        dot.node(
            "HandleError",
            "Handle\nError",
            shape="box",
            style="filled",
            fillcolor="#ffcccb",
        )
        dot.node("End", "Final\nResponse", shape="ellipse", style="filled", fillcolor="#e1f5ff")

        # Add edges
        dot.edge("User", "Classify")
        dot.edge("Classify", "Conversational")
        dot.edge("Classify", "GenerateSQL", label="SQL")
        dot.edge("GenerateSQL", "ExecuteSQL")
        dot.edge("ExecuteSQL", "HandleError", label="Error")
        dot.edge("ExecuteSQL", "Judge", label="Success")
        dot.edge("Judge", "HandleError", label="Invalid")
        dot.edge("Judge", "Analyze", label="Valid")
        dot.edge("HandleError", "GenerateSQL", label="Retry")
        dot.edge("HandleError", "End", label="Max Retries")
        dot.edge("Conversational", "End")
        dot.edge("Analyze", "End")

        # Render
        dot.render(str(output_path).replace(".png", ""), format="png", cleanup=True)
        print(f"SQL Generator flow diagram PNG written to: {output_path}")

    else:
        print("Cannot generate diagram - graphviz or pygraphviz not available")
        print("Please install: pip install pygraphviz OR pip install graphviz")
        return False

    return True


if __name__ == "__main__":
    generate_sql_diagram()

