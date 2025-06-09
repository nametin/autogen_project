from agents.manager_agent import ManagerAgent
from agents.coder_agent import CoderAgent
from agents.executor_agent import ExecutorAgent
from agents.test_case_generator_agent import TestcaseGeneratorAgent
from util.helpers import Helper

helper = Helper()

coder = CoderAgent()
testcase = TestcaseGeneratorAgent()
executor = ExecutorAgent()
manager = ManagerAgent(coder, testcase, executor)

func_name = "expand_encoded_string"
desc = """Given an encoded string where patterns like '3[a]' indicate the substring 'a' repeated 3 times,
decode the string and return the expanded result.

The pattern can be nested, e.g., '2[ab3[c]]' should decode to 'abcccabccc'.

Assume the input string is always valid.
"""


sample_inputs = [
    ("3[a]",),
    ("2[ab3[c]]",),
    ("3[a2[c]]",),
    ("2[abc]3[cd]ef",),
    ("10[x]",),
]

expected_outputs = [
    "aaa",  # 'a' repeated 3 times
    "abcccabccc",  # 3[c] = ccc, so abccc repeated 2 times
    "accaccacc",  # a2[c] = acc, repeated 3 times
    "abcabccdcdcdef",  # 2[abc] + 3[cd] + ef
    "xxxxxxxxxx",  # 10 times x
]


final_code = manager.run_workflow(desc, func_name, sample_inputs, expected_outputs)
print(f"Final code: {final_code}")
