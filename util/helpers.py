# helpers.py

import json
import re
import os
from dotenv import load_dotenv

class Helper:

    def __init__(self):
        load_dotenv()
        self.key = os.getenv("GROQ_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

        # First line is preview model
        # Second line is production model. If preview can't found, then production will be used.

        self.coder_model = "meta-llama/llama-4-maverick-17b-128e-instruct"
        # self.coder_model = "deepseek-r1-distill-llama-70b"
        # self.coder_model= "llama-3.3-70b-versatile"

        # self.tc_model="meta-llama/llama-4-scout-17b-16e-instruct"
        self.tc_model= "meta-llama/llama-4-maverick-17b-128e-instruct"
        # self.tc_model = "deepseek-r1-distill-llama-70b"
        # self.tc_model= "llama3-70b-8192"

        # self.exec_model="meta-llama/llama-4-scout-17b-16e-instruct"
        # self.exec_model= "meta-llama/llama-4-maverick-17b-128e-instruct"
        self.exec_model = "llama-3.1-8b-instant"

        self.manager_model="mistral-saba-24b"
        # self.manager_model="gemma2-9b-it"

        # self.openai_model = "gpt-3.5-turbo-0125"
        self.openai_model = "gpt-4-turbo-2024-04-09"

    def parse_testcases(self,json_response: str):        
        try:
            testcases = json.loads(json_response)
            inputs = []
            outputs = []

            for case in testcases:
                inp = case.get("input")
                out = case.get("expected_output")

                if isinstance(inp, list):
                    # Çoklu input için → tuple
                    inputs.append(tuple(inp))
                else:
                    inputs.append((inp,))

                outputs.append(out)

            return inputs, outputs
        except json.JSONDecodeError as e:
            print(f"[!] JSON decode error: {e}")
            return [], []
        except Exception as e:
            print(f"[!] Unexpected error: {e}")
            return [], []

    def extract_code(self,raw_output: str) -> str:
        if "```" in raw_output:
            code_blocks = re.findall(r"```(?:python)?\n(.*?)```", raw_output, re.DOTALL)
            return code_blocks[0].strip() if code_blocks else raw_output.strip()
        return raw_output.strip()

    def build_coder_prompt(self,func_name, description, sample_inputs=None, expected_outputs=None):

        if sample_inputs is None or expected_outputs is None:
            raise ValueError("Sample inputs and expected outputs must be provided.")

        if len(sample_inputs) != len(expected_outputs):
            raise ValueError("Each sample input should have a corresponding expected output.")

        test_cases = "\n".join([f"- Input: {sample_inputs[i]} → Expected Output: {expected_outputs[i]}" for i in range(len(sample_inputs))])

        prompt=f"""
You are a senior Python developer.

CODING TASK IN PYTHON:
Write an optimized and well-documented Python function based on the following details:
Function name: 
{func_name}
Detailed function description: 
{description}
Ensure that the function satisfies the following test cases:
{test_cases}
            
The function should:
- Follow best coding practices.
- Include proper docstrings and type hints.
- Be efficient and optimized.
- Avoid unnecessary complexity.
- Ensure all given inputs return the expected outputs.
- Be careful about indentation — make sure all blocks are properly indented.
            
REQUIREMENTS: 
- Provide a Python implementation.
- Import necessary libraries.
- In your answer, give only the function implementation, without extra characters or explanations. Don't add any character other than the function in your answer.
"""
        return prompt

    # - Only for your first answer, we expect your code **to be intentionally wrong** for debugging purposes. Please intentionally add some code lines to make the give wrong outputs. To illustrate: raise some unnecessary exceptions or give unexpected outputs.

    def build_tc_prompt(self, description,sample_input,sample_output):
        prompt = f"""
TASK DESCRIPTION:
{description}

THERE is one example input and output for this problem. Don't copy them please, these are just for get sense of: 
Sample input: {sample_input}
Sample output: {sample_output}

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
- If the input consists of multiple values, use a list.
- Use lowercase booleans (true/false) in JSON.
- Do NOT include any explanations or markdown. Just raw JSON.
IMPORTANT RULE: Your entire response **MUST** be exactly one valid JSON array and nothing else. 
- Do NOT include any text before or after the array.
- Do NOT use markdown code fences.
- Do NOT add punctuation, commentary, or stray commas.
""".strip()
        return prompt

    # - Only for your first answer, we expect one of your testcases **to be intentionally wrong** for debugging purposes. Please add one wrong testcase at the end of your answer but don't mark it as "wrong". To illustrate: make input be "h" output be "p".

    def coder_config(self):
        name = "Coder"        
        system_message="You are an AI code generator that creates Python functions based on descriptions and test cases."

        # grok
        llm_config={
            "config_list": [
                {
                    "model":self.coder_model,
                    "base_url": "https://api.groq.com/openai/v1", 
                    "api_key": self.key       
                }
            ],
            "temperature": 0.7
        }     

        # openai
        llm_config_openai = {
            "config_list": [
                {
                    "model": self.openai_model, 
                    "base_url": "https://api.openai.com/v1",   
                    "api_key": self.openai_key
                }
            ],
            "temperature": 0.7
        }     

        # return name, system_message, llm_config
        return name, system_message, llm_config_openai

    def testcase_generator_config(self):
        name = "TestcaseGenerator"

        system_message="""
        You are an AI test designer that generates Python test cases without seeing the implementation. 
        Your job is to create diverse, valid, and well-structured test cases based only on the task description.
        You should include basic, edge, and large-scale test scenarios.
        For each test, provide an input and its expected output. Ensure outputs are logically consistent with the task.
        Do not include Python code, only structured test descriptions.
        """       

        # grok
        llm_config={
            "config_list": [
                {
                    "model":self.tc_model,
                    "base_url": "https://api.groq.com/openai/v1", 
                    "api_key": self.key       
                }
            ],
            "temperature": 0.7
        }  

        # openai
        llm_config_openai = {
            "config_list": [
                {
                    "model": self.openai_model,
                    "base_url": "https://api.openai.com/v1",
                    "api_key": self.openai_key,
                }
            ],
            "temperature": 0.7,
        }

        # return name, system_message, llm_config
        return name, system_message, llm_config_openai

    def executor_config(self):
        name = "Executor"
        system_message="You are an AI code evaluator. You have only one duty. You need to evaluate the given code and prepare a evaluation report. You must not do debugging. You must not try to solve problems."

        llm_config={
            "config_list": [
                {
                    "model":self.exec_model,
                    "base_url": "https://api.groq.com/openai/v1", 
                    "api_key": self.key       
                }
            ],
            "temperature": 0.9
        }  

        # openai
        llm_config_openai = {
            "config_list": [
                {
                    # "model": self.openai_model,
                    "model": "gpt-4-turbo-2024-04-09",
                    "base_url": "https://api.openai.com/v1",
                    "api_key": self.openai_key,
                }
            ],
            "temperature": 0.7,
        }

        # return name, system_message, llm_config
        return name, system_message, llm_config_openai

    def manager_config(self):
        name = "Manager"

        system_message = "You are the Manager Agent coordinating CoderAgent, TestcaseGeneratorAgent, and ExecutorAgent."

        llm_config={
            "config_list": [
                {
                    "model": self.manager_model,
                    "base_url": "https://api.groq.com/openai/v1",
                    "api_key":  self.key 
                }
            ],
            "temperature": 0.7
        }

        return name, system_message, llm_config
