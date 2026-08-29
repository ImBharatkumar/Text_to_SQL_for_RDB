import sys
import io
import traceback
from typing import Dict, Any

class PythonSandbox:
    """Isolated Python code execution environment with stdout/stderr capture."""

    def __init__(self, globals_dict: Dict[str, Any] = None):
        self.globals_dict = globals_dict or {}

    def execute(self, code_str: str) -> Dict[str, Any]:
        """
        Executes code_str safely in the sandbox.
        Returns:
            {
                "success": bool,
                "stdout": str,
                "stderr": str,
                "result": Any,
                "error": str
            }
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Local execution namespace
        local_scope = {}
        global_scope = {"__builtins__": __builtins__}
        global_scope.update(self.globals_dict)

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture

            exec(code_str, global_scope, local_scope)

            # Look for a result variable or return from local_scope
            result = local_scope.get("result", local_scope.get("output", None))

            return {
                "success": True,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "result": result,
                "error": None
            }
        except Exception as e:
            err_msg = traceback.format_exc()
            return {
                "success": False,
                "stdout": stdout_capture.getvalue(),
                "stderr": stderr_capture.getvalue(),
                "result": None,
                "error": str(e),
                "traceback": err_msg
            }
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
