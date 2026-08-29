import json
from typing import Dict, Any, List
from app.agent.sandbox import PythonSandbox
from app.agent.tools import search_schema, inspect_table, sample_column_values, query_sql
from app.plugins.llm import LLMPlugin

AGENT_PROMPT_TEMPLATE = """You are an expert Data Analyst and Python/SQL developer.
You answer user questions by writing Python code that executes inside a sandbox environment.

--- AVAILABLE HELPER FUNCTIONS ---
- search_schema(query: str, top_k: int = 5) -> List[Dict]: Vector search for relevant tables & column descriptions.
- inspect_table(table_name: str) -> Dict: Returns column types and details for a table.
- sample_column_values(table_name: str, column_name: str, limit: int = 5) -> List: Samples distinct column values.
- query_sql(sql: str) -> List[Dict]: Executes a read-only SELECT query against the SQLite database.

--- INITIAL SCHEMA CONTEXT ---
{schema_context}

--- RULES ---
1. Write executable Python code inside a ```python ``` code block.
2. Use query_sql() to fetch rows. Save the final analysis result into a variable named `result`.
3. Keep code clean, safe, and efficient.
4. Do NOT attempt file system or network operations outside provided tools.

User Question: {question}
{previous_feedback}
Python Code:"""

class PythonSandboxAgent:
    """Code-Interpreter Agent operating inside Python Sandbox with tool tracing and self-repair."""

    def __init__(self, llm: LLMPlugin = None):
        self.llm = llm or LLMPlugin()

    def run(self, question: str, max_retries: int = 3) -> Dict[str, Any]:
        # 1. Initial vector schema search
        initial_matches = search_schema(question, top_k=5)
        schema_context = "\n\n".join([m["text"] for m in initial_matches])

        previous_feedback = ""
        trajectory = []

        for attempt in range(1, max_retries + 1):
            tool_calls_logged = []

            # Create tool wrappers that log calls and arguments with exact keyword signatures
            def tracked_search_schema(query: str, top_k: int = 5):
                try:
                    res = search_schema(query, top_k)
                    tool_calls_logged.append({
                        "tool": "search_schema",
                        "args": {"query": query, "top_k": top_k},
                        "output_summary": f"Returned {len(res)} matching table docs",
                        "status": "success"
                    })
                    return res
                except Exception as e:
                    tool_calls_logged.append({
                        "tool": "search_schema",
                        "args": {"query": query, "top_k": top_k},
                        "output_summary": str(e),
                        "status": "error"
                    })
                    raise

            def tracked_inspect_table(table_name: str):
                try:
                    res = inspect_table(table_name)
                    tool_calls_logged.append({
                        "tool": "inspect_table",
                        "args": {"table_name": table_name},
                        "output_summary": f"Schema details retrieved for '{table_name}'",
                        "status": "success"
                    })
                    return res
                except Exception as e:
                    tool_calls_logged.append({
                        "tool": "inspect_table",
                        "args": {"table_name": table_name},
                        "output_summary": str(e),
                        "status": "error"
                    })
                    raise

            def tracked_sample_column(table_name: str, column_name: str, limit: int = 5):
                try:
                    res = sample_column_values(table_name, column_name, limit)
                    tool_calls_logged.append({
                        "tool": "sample_column_values",
                        "args": {"table_name": table_name, "column_name": column_name, "limit": limit},
                        "output_summary": f"Sampled {len(res)} distinct values",
                        "status": "success"
                    })
                    return res
                except Exception as e:
                    tool_calls_logged.append({
                        "tool": "sample_column_values",
                        "args": {"table_name": table_name, "column_name": column_name, "limit": limit},
                        "output_summary": str(e),
                        "status": "error"
                    })
                    raise

            def tracked_query_sql(sql: str):
                try:
                    res = query_sql(sql)
                    tool_calls_logged.append({
                        "tool": "query_sql",
                        "args": {"sql": sql},
                        "output_summary": f"Executed query successfully. Returned {len(res)} row(s).",
                        "status": "success"
                    })
                    return res
                except Exception as e:
                    tool_calls_logged.append({
                        "tool": "query_sql",
                        "args": {"sql": sql},
                        "output_summary": str(e),
                        "status": "error"
                    })
                    raise

            sandbox_globals = {
                "search_schema": tracked_search_schema,
                "inspect_table": tracked_inspect_table,
                "sample_column_values": tracked_sample_column,
                "query_sql": tracked_query_sql,
            }

            prompt = AGENT_PROMPT_TEMPLATE.format(
                schema_context=schema_context,
                question=question,
                previous_feedback=previous_feedback
            )

            try:
                code_response = self.llm.generate(prompt)
            except Exception as e:
                return {
                    "question": question,
                    "initial_retrieval": initial_matches,
                    "status": "error",
                    "error": f"LLM Generation failed: {str(e)}",
                    "trajectory": trajectory
                }

            # Extract python code block if present
            code = code_response
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()

            sandbox = PythonSandbox(globals_dict=sandbox_globals)
            exec_res = sandbox.execute(code)

            trajectory.append({
                "attempt": attempt,
                "code": code,
                "success": exec_res["success"],
                "stdout": exec_res["stdout"],
                "stderr": exec_res["stderr"],
                "error": exec_res["error"],
                "tool_calls": tool_calls_logged
            })

            if exec_res["success"]:
                return {
                    "question": question,
                    "initial_retrieval": initial_matches,
                    "status": "success",
                    "code": code,
                    "result": exec_res["result"],
                    "stdout": exec_res["stdout"],
                    "iterations": attempt,
                    "trajectory": trajectory
                }

            # Feedback loop for self-correction
            error_details = exec_res["error"] or exec_res["stderr"]
            previous_feedback = f"\n\n[ATTEMPT {attempt} FAILED WITH ERROR]:\n{error_details}\nPlease fix the code and try again."

        return {
            "question": question,
            "initial_retrieval": initial_matches,
            "status": "failed",
            "error": "Exceeded maximum self-repair retries.",
            "iterations": max_retries,
            "trajectory": trajectory
        }
