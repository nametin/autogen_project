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

# func_name ="sample_func"
# desc = """
# Given a string, return a new string with the words in reverse order.
# Words are separated by spaces. Preserve only single spaces between words in the output.
# Leading and trailing spaces should be removed in the result.
# """

# sample_inputs = [
#     ("hello world",),
#     ("   OpenAI   builds powerful AI tools   ",),
#     ("a b c",),
#     ("singleword",),
# ]

# expected_outputs = [
#     "world hello",
#     "tools AI powerful builds OpenAI",
#     "c b a",
#     "singleword",
# ]

"""
def reverse_in_parentheses(s: str) -> str:

 while '(' in s:
 # Find the innermost pair of parentheses
 start = s.rfind('(')
 end = s.find(')', start)
 
 # Reverse the substring within the innermost parentheses
 s = s[:start] + s[start +1:end][::-1] + s[end +1:]
 
 return s


"""




func_name = "reverse_in_parentheses"
desc = """
Given a string containing lowercase letters and parentheses, 
reverse the characters enclosed within each pair of parentheses, starting from the innermost one.
Return the resulting string with all parentheses removed.

Nested parentheses must be processed correctly. 
Assume the input string is always valid and properly nested.
"""



sample_inputs = [
    ("a(bc)de",),
    ("a(b(cd)e)f",),
    ("(u(love)i)",),
    ("(ed(et(oc))el)",),
    ("abc",),
]

expected_outputs = [
    "acbde",             # bc -> cb
    "aecdcbf",           # cd -> dc, then bdc -> cdb -> ecdcb
    "iloveu",            # love -> evol, then u(evoli) -> iloveu
    "leetcode",          # oc -> co, etco -> octe, edocte -> etcode, eletcode -> leetcode
    "abc",               # No parentheses, so no change
]


final_code = manager.run_workflow(desc, func_name, sample_inputs, expected_outputs)
print(f"Final code: {final_code}")
