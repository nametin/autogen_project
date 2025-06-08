#!/usr/bin/env python3
import sys
import json
import base64
import io
import contextlib
import types


def execute_helper(python_code: str, input_args):
    """
    Execute a single call to the decoded Python code, capturing stdout, return value, and errors.
    """
    exec_globals = {}
    exec_locals = {}
    stdout = io.StringIO()
    returned = None
    error = None

    # Redirect print output
    with contextlib.redirect_stdout(stdout):
        try:
            exec(python_code, exec_globals, exec_locals)
            # Find the function object in locals
            func = next(
                val
                for val in exec_locals.values()
                if isinstance(val, types.FunctionType)
            )
            # Call with dict or list or single arg
            if isinstance(input_args, dict):
                returned = func(**input_args)
            elif isinstance(input_args, list):
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


def main():
    # Expect a single argument: path to JSON payload
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: run_tests.py <payload.json>"}))
        sys.exit(1)

    payload_path = sys.argv[1]
    try:
        with open(payload_path, "r") as f:
            payload = json.load(f)
    except Exception as e:
        print(json.dumps({"error": f"Failed to load payload: {e}"}))
        sys.exit(1)

    # Extract code and testcases
    python_code_b64 = payload.get("python_code_b64")
    testcases = payload.get("testcases", [])

    try:
        python_code = base64.b64decode(python_code_b64).decode("utf-8")
    except Exception as e:
        print(json.dumps({"error": f"Failed to decode code: {e}"}))
        sys.exit(1)

    # Execute each testcase
    results = []
    for case in testcases:
        inp = case.get("input")
        res = execute_helper(python_code, inp)
        # include expected output for reference
        res["expected_output"] = case.get("expected_output")
        results.append(res)

    # Print JSON with all executions
    output = {"executions": results}
    print(json.dumps(output))


if __name__ == "__main__":
    main()
