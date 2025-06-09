# test_case_generator_agent.py

from autogen import ConversableAgent
from util.helpers import Helper

class TestcaseGeneratorAgent:
    def __init__(self):
        self.helper = Helper()
        name, system_message, llm_config = self.helper.testcase_generator_config()
        
        self.agent = ConversableAgent(
            name=name,
            system_message=system_message,
            llm_config=llm_config    
        )
        
    @property
    def conversable(self):
        return self.agent
    