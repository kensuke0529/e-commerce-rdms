import sys
from pathlib import Path
import json

from numpy import result_type

project_root = (
    Path().resolve().parent.parent.parent
)  # Adjust based on notebook location
sys.path.insert(0, str(project_root / "script"))

from sql_generator.ai_helpers import generate_sql_query
from sql_generator.query_runner import SQLAnalysisRunner


json_path = (
    project_root / "script" / "sql_generator" / "eval" / "sql_generator_sample.json"
)
with open(json_path) as f:
    data = json.load(f)

results = []
for row in data:
    prompt = row["prompt"]

    sql_query = generate_sql_query(prompt)
    ai_runner = SQLAnalysisRunner()

    sql_data = ai_runner.run_single_query(sql_query)
    
    print("================")
    print(f"query: {prompt}")
    print(f"generated query: {sql_query}")
    print(f"sql result: \n {sql_data}")
    print("================")

    results.append(
        {
            "prompt": prompt,
            "generated query": sql_query,
            "sql result": sql_data,
        }
    )
