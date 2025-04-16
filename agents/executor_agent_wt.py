import io
import contextlib
import types
import json
from util.helpers import Helper

from autogen import ConversableAgent, register_function
from typing import Annotated

# TOOL FUNCTION 
def execute_code (python_code: Annotated[str, "Python function definition as string"],
                    inputs: Annotated[dict, "Dictionary of function inputs"]) -> dict:
    returned = None
    
    inputs = inputs or {}
    exec_globals = {}
    exec_locals = {}
        
    stdout = io.StringIO()
        
    with contextlib.redirect_stdout(stdout):
        try: 
            exec(python_code, exec_globals, exec_locals)
            func = next(val for val in exec_locals.values() if isinstance(val, types.FunctionType))
            
            returned = func(**inputs)

        except Exception as e:
            return {
                "printed": stdout.getvalue(),
                "error": str(e)
            }
            
    return {
        "printed": stdout.getvalue(),
        "returned": returned
    }

def execute_helper (python_code: str, input_args: dict):
    
    exec_globals = {}
    exec_locals = {}
    stdout = io.StringIO()
    returned = None
    error = None
    
    with contextlib.redirect_stdout(stdout):
        try:
            exec(python_code, exec_globals, exec_locals)
            func = next(val for val in exec_locals.values() if isinstance(val, types.FunctionType))
            if isinstance(input_args, dict):
                returned = func(**input_args)
            elif isinstance(input_args, list):
                returned = func(*input_args)
            else: 
                returned = func(input_args)

        except Exception as e:
            error = str(e)

    return {
        "input": input_args,
        "printed": stdout.getvalue(),
        "returned": returned,
        "error": error
    }    
    
# TOOL FUNCTION 
def execute_code_batch (python_code: Annotated[str, "Python function definition as string"],
                        inputs: Annotated[list, "List of input dictionaries to call the function with"]
)-> dict :
    executions = [execute_helper(python_code, input_args) for input_args in inputs]
    return {"executions": executions}

class ExecutorAgent: 
    def __init__ (self):
        self.helper = Helper()
        # name, system_message, llm_config = self.helper.executor_assistant_config()
        
        name, system_message, llm_config = self.helper.executor_config()

        self.assistant= ConversableAgent(
            name=name,
            system_message=system_message,
            llm_config=llm_config    
        )

        self.user_proxy = ConversableAgent(
            name = "user",
            llm_config=False,
            is_termination_msg=lambda msg: msg.get("content") and "quit chat" in msg["content"],
            human_input_mode="NEVER"
        )   
        
        self.register_tool()

    def register_tool (self):
        register_function(
            execute_code,
            caller=self.assistant,
            executor=self.user_proxy,
            name="execute_code",
            description="Executes Python function code and returns both printed and returned values."
        )
        
        register_function(
            execute_code_batch,
            caller=self.assistant,
            executor=self.user_proxy,
            name="execute_code_batch",
            description="Executes a Python function with multiple input sets and returns results for all test cases."
        )
        
    def run_task(self,message:str):
        
        chat_result = self.user_proxy.initiate_chat(self.assistant,message=message)
        for msg in reversed(chat_result.chat_history):
            if msg.get("role") == "user" and msg.get("name") == "Executor":
                content = msg.get("content")
                return content.replace("quit chat", "").strip()

        return None
        
    def execute_and_report(self, python_code: str, testcases: list):

        prompt = """
You are an AI code evaluator. Right now you're in a chat with an assistant agent that can run python methods and return their outputs.
You will receive: 
- Python function code (as string)
- A list of test cases, where each test contains:
    - input: a list of arguments
    - expected_output: the expected result

You should: 
- Dynamically execute the function for every testcase. To execute the function, use the chat that you're in. Note that the other agent in the chat can run python methods and return their outputs.
- Run all testcases sending them one by one to the chat. While sending message to chat, follow the 'MESSAGE FORMAT' given below.
- Report which testcases pass or fail. (if actual output matches the expected output, then testcase passes, fails otherwise.) You'll return a summary at the end of all testcase executions. 

Run the testcases ***ONE BY ONE*** don't send all testcases to the other agent in only one message.
If you ended running the testcases (using the chat), it means your chat should be terminated. When you want to terminate the chat session, send a message to chat following the 'OUTPUT FORMAT' given below. 
Note that if your chat message includes 'quit chat', then chat will be terminated. Please don't add 'quit chat' to your chat message unless you want to terminate the session. 

MESSAGE FORMAT: 
code: 
<python code>
input: 
<input>  

OUTPUT FORMAT: 
quit chat

Summary: 
    Passed: <num1>
    Failed: <num2> 
Mismatches: 
    Testcase <tc1> -> input: <input1> ; expected output: <expected_output1> ; program output: <actual_output1>
    Testcase <tc2> -> input: <input2> ; expected output: <expected_output2> ; program output: <actual_output2>
    ...
    
***NOTE THAT YOUR MESSAGE SHOULD PERFECTLY MATCH EITHER THE GIVEN MESSAGE FORMAT OR GIVEN OUTPUT FORMAT. DO NOT ANY OTHER CHARACTER OR EXPLANATION JUST GIVE WHAT IS EXPECTED***
"""
        
        payload = {
            "code": python_code,
            "testcases": testcases
        }
        full_message = prompt + "\n" + json.dumps(payload)
        
        return self.run_task(full_message)
    
    def create_execution_report(self,python_code: str, testcases: list):
        
        prompt = """
You are an AI test evaluator. A tool (execute_code_batch) is available to you that can run a Python function across multiple testcases in batch.
Each testcase includes:
- input: a dictionary of arguments to pass to the function
- expected_output: the expected result

Your task:
- Call the tool with the given function and testcases (all at once).
- Then compare each execution result:
    - If the returned value matches expected_output, mark as PASSED.
    - Otherwise, mark as FAILED.

After evaluating all test cases, generate a final summary using the following **strict format**:

OUTPUT FORMAT:
quit chat

Summary: 
    Passed: <number_of_passed_cases>
    Failed: <number_of_failed_cases>
Mismatches: 
    Testcase <i> -> input: <input> ; expected output: <expected_output> ; program output: <actual> ; error: <error_text>
    ...
    
IMPORTANT RULES:

- DO NOT modify the function code under any circumstances.
- DO NOT modify the content of test cases (neither `input` nor `expected_output`).
- If a tool call fails due to a type error or formatting issue, you are allowed to retry the tool call — but only by formatting the input correctly.
    - You may NOT change input values or expected values.
    - If errors occur because of formatting, you're only allowed to retry by formatting the input **correctly**, not by changing its values.
- If the function code itself is invalid (e.g., syntax error, undefined variables), include the error message in the summary report.
- Again, carefully note that, YOU ARE NOT ALLOWED TO CHANGE THE GIVEN FUNCTION OR INPUT VALUES IN ANY CASE.
- If your message includes the phrase "quit chat", the chat session will be terminated — only include it in the final summary message.

***DO NOT add any other explanation or comments. Only give the OUTPUT FORMAT stated above at the end. ***
"""

        inputs = [tc["input"] for tc in testcases]

        payload = {
            "code": python_code,
            "inputs": inputs,
            "testcases": testcases  
        }

        full_message = prompt + "\n" + json.dumps(payload)
        return self.run_task(full_message)