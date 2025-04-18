from agents.manager_agent import ManagerAgent
from agents.coder_agent import CoderAgent
from agents.executor_agent import ExecutorAgent
from agents.test_case_generator_agent import TestcaseGeneratorAgent
from util.helpers import Helper

helper = Helper()

coder = CoderAgent()
testcase = TestcaseGeneratorAgent()
executor = ExecutorAgent()
manager = ManagerAgent(coder,testcase,executor)

func_name ="sample_func"
desc = """
Given a string, return a new string with the words in reverse order.
Words are separated by spaces. Preserve only single spaces between words in the output.
Leading and trailing spaces should be removed in the result.
"""

sample_inputs = [
    ("hello world",),
    ("   OpenAI   builds powerful AI tools   ",),
    ("a b c",),
    ("singleword",),
]

expected_outputs = [
    "world hello",
    "tools AI powerful builds OpenAI",
    "c b a",
    "singleword",
]

final_code = manager.run_workflow(desc, func_name, sample_inputs, expected_outputs)
print(f"Final code: {final_code}")
