from agents.coder_agent import CoderAgent
from agents.test_case_generator_agent import TestcaseGeneratorAgent
from agents.executor_agent import ExecutorAgent
from autogen import GroupChat, GroupChatManager, UserProxyAgent
from util.helpers import Helper

helper = Helper()
coder = CoderAgent()
test_case_generator = TestcaseGeneratorAgent()
executor = ExecutorAgent()

name= "method"
description ="Write a Python function that returns True if any two numbers in a list are closer to each other than a given threshold."

sample_inputs = [
    "([1.0, 2.0, 3.0, 4.0], 0.5)",
    "([1.0, 2.0, 3.0, 4.0], 1.5)",
    "([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], 0.4)"
]

expected_outputs = [
    "False",
    "True",
    "False"
]    

user = UserProxyAgent(name="User", human_input_mode="NEVER")

prompt = Helper.build_coder_prompt(name,description, sample_inputs, expected_outputs)


# groupchat = GroupChat(
#     agents=[user, coder.conversable],
#     messages=[
#         {
#             "role": "user",
#             "content": prompt
#         }
#     ],
#     max_round=30
# )

# llm_config = helper.manager_config()

# manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)
# manager.run()