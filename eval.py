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
func_name = "sample_method"
desc = "Write a function to find the number of ways to fill it with 2 x 1 dominoes for the given 3 x n board."


sample_inputs = [
    ("2",),
    ("8",),
    ("12",),
]

expected_outputs = [
    "3",
    "153",
    "2131",
]


final_code = manager.run_workflow(desc, func_name, sample_inputs, expected_outputs)
print(f"Final code: {final_code}")
