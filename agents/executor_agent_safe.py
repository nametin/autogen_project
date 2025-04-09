import subprocess
import tempfile
import os
import json
import textwrap

class ExecutorAgent:
    def __init__(self, timeout=5):
        self.timeout = timeout

    def run(self, function_code: str, function_name: str, inputs: list[tuple], expected_outputs: list):

        with tempfile.TemporaryDirectory() as temp_dir:
            func_file = os.path.join(temp_dir, "func.py")
            data_file = os.path.join(temp_dir, "test_data.json")
            runner_file = os.path.join(temp_dir, "run.py")

            with open(func_file, "w") as f:
                f.write(function_code)

            test_data = [
                {"input": inp, "expected": expected_outputs[i]}
                for i, inp in enumerate(inputs)
            ]
            with open(data_file, "w") as f:
                json.dump(test_data, f)

            with open(runner_file, "w") as f:
                
                code = textwrap.dedent(f"""
import json
import traceback
import sys

try:
    from .func import {function_name}
except Exception as e:
    print(json.dumps([{{"error": "ImportError", "details": str(e)}}]))
    sys.exit(1)

with open("{data_file}", "r") as f:
    test_cases = json.load(f)

results = []
for case in test_cases:
    try:
        inp = case["input"]
        expected = case["expected"]
        output = {function_name}(*inp)
        results.append({{
            "input": inp,
            "expected": expected,
            "actual": output,
            "passed": output == expected
        }})
    except Exception as e:
        results.append({{
            "input": inp,
            "expected": expected,
            "actual": str(e),
            "passed": False,
            "error": traceback.format_exc()
        }})

print(json.dumps(results))
""")

                f.write(code)
                
            try:
                process = subprocess.run(
                    ["python3", runner_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=temp_dir
                )

                if process.returncode != 0:
                    print("[!] Execution error:", process.stderr)
                    return []

                output = json.loads(process.stdout)

            except subprocess.TimeoutExpired:
                print("[!] Execution timed out.")
                return []
            except Exception as e:
                print(f"[!] Unexpected error: {e}")
                return []

        passed = sum(1 for r in output if r.get("passed"))
        total = len(output)
        print(f"\nExecutorAgent: {passed}/{total} tests passed ({(passed/total)*100:.2f}%)\n")

        return output
