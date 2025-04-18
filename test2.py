from agents.executor_agent import ExecutorAgent

executor = ExecutorAgent()

testcases = [
    {"input": {"x": 2}, "expected_output": 4},
    {"input": {"x": 0}, "expected_output": 0},
    {"input": {"x": -3}, "expected_output": -9}
]

code = """
def square(x):
    print(f"Calculating square of {x}")
    return x * x
"""

# result = executor.execute_and_report(code, testcases)


result = executor.create_execution_report(code,testcases)
print(result)
