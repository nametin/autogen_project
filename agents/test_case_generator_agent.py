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
    
    
    # for debug 
    def generate_testcases(self, description):
        prompt = f"""
        TASK DESCRIPTION:
        {description}
        
        Add at least one:
        - Basic functionality test 
        - Edge case 
        - Large-scale test 
        
        OUTPUT FORMAT:
        Return the test cases as a valid JSON array of dictionaries, using the following format:

        [
        {{
            "input": <JSON-serializable input>,
            "expected_output": <JSON-serializable output>
        }},
        ...
        ]

        Rules:
        - "input" can be any JSON-valid type: number, string, list, object, tuple-as-list, etc.
        - If the input consists of multiple values, use a list or array.
        - Use lowercase booleans (true/false), no Python syntax.
        - Do NOT include any explanations or markdown. Just raw JSON.
        """
        prompt 
        response = self.agent.generate_reply(messages=[{"role": "user", "content": prompt}])
        
        runs,outputs = Helper.parse_testcases(response)
    
        return runs,outputs