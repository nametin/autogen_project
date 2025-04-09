from agents.manager_agent import ManagerAgent
from dotenv import load_dotenv

load_dotenv()

description = """
Given a string, return a new string with the words in reverse order.
Words are separated by spaces. Preserve only single spaces between words in the output.
Leading and trailing spaces should be removed in the result.
"""

validation_inputs = [
    ("hello world",),
    ("   OpenAI   builds powerful AI tools   ",),
    ("a b c",),
    ("singleword",),
]
validation_outputs = [
    "world hello",
    "tools AI powerful builds OpenAI",
    "c b a",
    "singleword",
]

manager = ManagerAgent(func_name="reverse_words")

final_code = manager.run_sequential_chat(description, (validation_inputs, validation_outputs))

print("\nFinal Code Output:\n")
print(final_code)
