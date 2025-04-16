# coder_agent.py

from autogen import ConversableAgent
from util.helpers import Helper

class CoderAgent:
    def __init__(self):
        self.helper = Helper()
        
        name, system_message, llm_config = self.helper.coder_config()
        
        self._conversable = ConversableAgent(
            name=name,
            system_message=system_message,
            llm_config=llm_config 
        )
        
    @property
    def conversable(self):
        return self._conversable
    
    # for debug
    def generate_code(self, func_name, description, sample_inputs=None, expected_outputs=None):
            
        prompt = self.helper.build_coder_prompt(func_name,description,sample_inputs,expected_outputs)
        
        response = self.agent.generate_reply(messages=[{"role": "user", "content": prompt}])
        
        code = self.helper.extract_code(response)
        
        return code
