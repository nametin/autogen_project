#!/usr/bin/env python3
import sys
import json
import base64
import io
import contextlib
import types

def execute_helper(python_code: str, input_args):
    """
    Execute a single test case: capture stdout, return value, and error.
    """
    exec_globals = {}
    exec_locals = {}
    stdout = io.StringIO()
    returned = None
    error = None

    with contextlib.redirect_stdout(stdout):
        try:
            exec(python_code, exec_globals, exec_locals)
            func = next(
                val
                for val in exec_locals.values()
                if isinstance(val, types.FunctionType)
            )
            if isinstance(input_args, dict):
                returned = func(**input_args)
            elif isinstance(input_args, (list, tuple)):
                returned = func(*input_args)
            else:
                returned = func(input_args)
        except Exception as e:
            error = str(e)

    return {
        "input": input_args,
        "printed": stdout.getvalue(),
        "returned": returned,
        "error": error,
    }

# Expect payload path and test index
if len(sys.argv) != 3:
    print(json.dumps({"error": "Usage: run_test.py <payload.json> <test_index>"}))
    sys.exit(1)

payload_path = sys.argv[1]
try:
    with open(payload_path, "r") as f:
        payload = json.load(f)
except Exception as e:
    print(json.dumps({"error": f"Failed to load payload: {e}"}))
    sys.exit(1)

try:
    python_code_b64 = payload["python_code_b64"]
    python_code = base64.b64decode(python_code_b64).decode("utf-8")
except Exception as e:
    print(json.dumps({"error": f"Failed to decode code: {e}"}))
    sys.exit(1)

try:
    idx = int(sys.argv[2])
except ValueError:
    print(json.dumps({"error": "Test index must be an integer"}))
    sys.exit(1)

inputs_list = payload.get("inputs")
if not isinstance(inputs_list, list):
    print(json.dumps({"error": "Invalid payload format; 'inputs' must be a list"}))
    sys.exit(1)

if idx < 0 or idx >= len(inputs_list):
    print(json.dumps({"error": f"Test index out of range: {idx}"}))
    sys.exit(1)

input_args = inputs_list[idx]

result = execute_helper(python_code, input_args)
print(json.dumps(result))
