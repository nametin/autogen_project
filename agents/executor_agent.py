# executor_agent.py

import io
import contextlib
import types
import json
import base64
import io
import os
import subprocess

from util.helpers import Helper
from util.docker_module import DockerSandbox
sandbox = DockerSandbox()

from autogen import ConversableAgent, register_function
from typing import Annotated

def execute_helper_old(python_code: str, input_args: dict):

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

inputs_default = []

# TOOL FUNCTION
def execute_code_batch(
    python_code_b64: Annotated[
        str, "Base64-encoded Python function definition as a UTF-8 string"
    ],
    inputs: Annotated[
        list,
        "This must be the exact list of test inputs from your JSON payload’s 'inputs' key. Each element will be passed unchanged to the function."  
    ],
) -> dict:
    x = sandbox.exec_batch(python_code_b64, inputs, timeout=5)
    return x


class ExecutorAgent: 
    def __init__ (self):
        self.helper = Helper()
        
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
    
    def create_execution_report(self,python_code_b64: str, testcases: list):
        
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
Mismatches: (Failed Testcases)
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
            "python_code_b64": python_code_b64,
            "inputs": inputs,
            "testcases": testcases  
        }
        self.inputs_default=inputs
        full_message = prompt + "\n" + json.dumps(payload)
        return self.run_task(full_message)
