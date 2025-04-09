import json
import re
import os

class Helper:
    
    def __init__(self):
        self.key = os.getenv("GROQ_API_KEY")
    
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
            
REQUIREMENTS: 
- Provide a Python implementation.
- Import necessary libraries.
- In your answer, give only the function implementation, without extra characters or explanations. Don't add any character other than the function in your answer.
"""

        return prompt

    def build_tc_prompt(self, description):
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
- If the input consists of multiple values, use a list.
- Use lowercase booleans (true/false) in JSON.
- Do NOT include any explanations or markdown. Just raw JSON.
""".strip()
        return prompt
    
    def coder_config(self):
        name = "Coder"        
        system_message="You are an AI code generator that creates Python functions based on descriptions and test cases."

        llm_config={
            "config_list": [
                {
                    "model":"qwen-2.5-coder-32b",
                    "base_url": "https://api.groq.com/openai/v1", 
                    "api_key": self.key       
                }
            ],
            "temperature": 0.7
        }     
        
        llm_config_local={
            "config_list": [
                {
                    "model":"gemma3:4b",
                    "base_url": "http://localhost:11434/v1", 
                    "api_key": "sk-no-key-required"       
                }
            ],
            "temperature": 0.7
        }  
        
        
        return name,system_message, llm_config

    def testcase_generator_config(self):
        name = "TestcaseGenerator"
        
        system_message="""
        You are an AI test designer that generates Python test cases without seeing the implementation. 
        Your job is to create diverse, valid, and well-structured test cases based only on the task description.
        You should include basic, edge, and large-scale test scenarios.
        For each test, provide an input and its expected output. Ensure outputs are logically consistent with the task.
        Do not include Python code, only structured test descriptions.
        """       
        
        llm_config={
            "config_list": [
                {
                    "model":"qwen-2.5-32b",
                    "base_url": "https://api.groq.com/openai/v1", 
                    "api_key": self.key       
                }
            ],
            "temperature": 0.7
        }  
        
        llm_config_local= {
            "config_list": [
                {
                    "model": "gemma3:1b",
                    "base_url": "http://localhost:11434/v1", 
                    "api_key": "sk-no-key-required"
                }
            ],
            "temperature": 0.4
        }          
        
        return name, system_message, llm_config
    
    def executor_config(self):
        name = "Executor"
        
        system_message="""
You are an AI code evaluator. 
Your job is to test Python functions against given test cases and report results clearly.

You will receive:
- Python function code (as string)
- The function name (as string)
- A list of test cases, where each test contains:
    - input: a list of arguments
    - expected_output: the expected result

You should:
- Dynamically execute the function
- Run all test cases
- Report which ones pass or fail
- Provide a summary with counts and mismatches
        """       
        
        llm_config={
            "config_list": [
                {
                    "model":"llama-3.3-70b-versatile",
                    "base_url": "https://api.groq.com/openai/v1", 
                    "api_key": self.key       
                }
            ],
            "temperature": 0.9
        }  
                
        return name, system_message, llm_config
        
    def manager_config(self):
        
        llm_config={
            "config_list": [
                {
                    "model": "llama-3.3-70b-specdec",
                    "base_url": "https://api.groq.com/openai/v1",
                    "api_key":  self.key 
                }
            ],
            "temperature": 0.7
        }
        
        return llm_config
    
    