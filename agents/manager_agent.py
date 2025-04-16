# manager_agent.py

import json
import re 

from autogen import ConversableAgent 
from util.helpers import Helper 
from agents.coder_agent import CoderAgent 
from agents.test_case_generator_agent import TestcaseGeneratorAgent 
# from agents.executor_agent import ExecutorAgent
from agents.executor_agent_wt import ExecutorAgent


class ManagerAgent: 
    def __init__(self, coder_agent: CoderAgent, testcase_agent: TestcaseGeneratorAgent, executor_agent: ExecutorAgent): 
        # Yardımcı sınıf üzerinden manager konfigürasyonunu alıyoruz. 
        self.helper = Helper() 
        self.name,self.system_message,self.llm_config = self.helper.manager_config() 
        self.coder_agent = coder_agent
        self.testcase_agent = testcase_agent
        self.executor_agent = executor_agent
        
        self.channels = {
            "coder_channel": [],
            "test_channel": [],
            "executor_channel": []  # Executor’dan gelen mesajlar için (merkezi erişim sağlanacak)
        }
        
        self.MAX_ITER = 5
        self.iter_counter = 0
        
        self.manager_agent = ConversableAgent(
            name=self.name,
            system_message=self.system_message,
            llm_config=self.llm_config
        )
        
    def log_message(self,channel:str, message:str):
        """Adds the message to channel"""        
        if channel in self.channels:
            self.channels[channel].append(message)
        else:
            raise ValueError(f"Undefined channel:{channel}")
        
    def get_channel_history(self, channel:str):
        """returns the history of the channel"""
        return self.channels.get(channel,[])
    
    def reset_channels(self):
        for key in self.channels:
            self.channels[key]=[]
  
    def initiate_testcase_generation(self,problem_description):
        tc_prompt = self.helper.build_tc_prompt(problem_description)
        self.log_message("test_channel", f"Manager:\n{tc_prompt}")          
        tc_response = self.testcase_agent.conversable.generate_reply([{"role":"user","content":tc_prompt}])
        self.log_message ("test_channel", f"TestCaseGenerator:\n{tc_response}")
        return tc_response
    
    def initiate_code_generation(self,func_name:str, problem_description:str, validation_inputs:list, validation_outputs:list):
        coder_prompt = self.helper.build_coder_prompt(func_name,problem_description,validation_inputs,validation_outputs)
        self.log_message("coder_channel",f"Manager:\n{coder_prompt}")
        coder_response = self.coder_agent.conversable.generate_reply([{"role":"user","content":coder_prompt}])
        self.log_message("coder_channel", f"Coder:\n{coder_response}")
        return coder_response
        
    def execute_code(self, code:str, func_name:str, test_inputs:list,test_outputs:list):
        
        testcases = [{"input": test_inputs[i], "expected_output": test_outputs[i]} for i in range(len(test_inputs))]

        
        payload = {
            "code": code,
            "function_name":func_name,
            "testcases":testcases
        }
        
        payload_str = json.dumps(payload)
        
        self.log_message("executor_channel", f"Manager:\n{payload_str}")
        # executor_response = self.executor_agent.execute_and_report(code,testcases)
        executor_response = self.executor_agent.create_execution_report(code,testcases)
        self.log_message("executor_channel", f"ExecutorAgent:\n{executor_response}")
        
        return executor_response 

    def analyze_executor_response(self, executor_response: str) -> bool:
        """
        Analyzes the ExecutorAgent's output by extracting the summary section.
        The function searches for lines containing "Passed:" and "Failed:" and then parses the numbers.
        It returns True if the number of failed tests is 0, otherwise False.
        """
        # Öncelikle, output içindeki "Summary" bölümünü ayıklamaya çalışalım.
        summary_match = re.search(r"Summary:(.*)", executor_response, re.IGNORECASE | re.DOTALL)
        if summary_match:
            summary_text = summary_match.group(1)
            # Summary kısmı içerisinde Passed ve Failed satırlarını bulalım.
            # passed_match = re.search(r"Passed\s*:\s*(\d+)", summary_text, re.IGNORECASE)
            failed_match = re.search(r"Failed\s*:\s*(\d+)", summary_text, re.IGNORECASE)
            if failed_match:
                failed_count = int(failed_match.group(1))
                # İsteğe bağlı olarak passed_match'i de kontrol edebiliriz:
                # passed_count = int(passed_match.group(1)) if passed_match else None
                return failed_count == 0  
        raise ValueError("Unexpected error in manager_agent.analyze_executor_response")  

    def provide_feedback(self, executor_response:str):
        """
        provides feedback for coder and testcase generator agents. should be used when expected outputs doesn't match the actuals.
        """
        
        coder_feedback =  f"""
Based on latest execution report: {executor_response}
Could you please review your code? There may be an error in your implementation.
Double-check your code, then please give your revised code or state "I'm sure the implementation is perfect" 

OUTPUT FORMAT: 
If you're sure your implementation is perfect, return only the following sentence: "I'm sure the implementation is perfect"
Else: Give give only the corrected function implementation. 
***Do NOT include any explanations or markdown. Your answer must contain just function implementation without extra characters or explanations OR the sentence 'I'm sure the implementation is perfect'***
"""

        self.log_message("coder_channel", f"Manager:\n{coder_feedback}")
        coder_feedback_response = self.coder_agent.conversable.generate_reply([{"role":"user", "content":coder_feedback}])
        self.log_message("coder_channel", f"Coder:\n{coder_feedback_response}")


        testcase_feedback = f"""
The execution report indicates the following issues: {executor_response}
Could you please examine the test cases you gave? There might be errors in your test design
Double-check them, then correct the problem if the issue is about the testcases. If not, then you may state 'I'm sure the testcases are true'

OUTPUT FORMAT: 
***If you're sure the testcases are true:*** return only the following sentence: "I'm sure the testcases are true"

***Else:*** 

Return the test cases as a valid JSON array of dictionaries, using the following format:

[
    {{
        "input": <JSON-serializable input>,
        "expected_output": <JSON-serializable output>
    }},
    ...
]

***Do NOT include any explanations or markdown. Your answer must contain just raw JSON OR the following sentence "I'm sure the testcases are true".***
"""


        self.log_message("test_channel", f"Manager:\n{testcase_feedback}")
        testcase_feedback_response = self.testcase_agent.conversable.generate_reply([{"role":"user", "content":testcase_feedback}])
        self.log_message("test_channel", f"TestCaseGenerator:\n{testcase_feedback_response}")
        
        return coder_feedback_response, testcase_feedback_response

    def run_workflow(self, problem_description:str, func_name: str , validation_inputs:list, validation_outputs:list):
        
        """
        1. starts coding and testcase generating phases calling coder and testcase generator
        2. sends generated testcases and code to executor 
        3. starts a loop, while executor returns a negative feedback, sends that feedback to coder and testcase generator with the aim of double checking their work.    
        4. max iter is set but could be expandable
        """
        
        self.log_message("executor_channel", "Workflow starts")

        test_testcases = self.initiate_testcase_generation(problem_description)
        test_inputs, test_outputs = self.helper.parse_testcases(test_testcases)        
        coder_response = self.initiate_code_generation(func_name, problem_description, validation_inputs, validation_outputs)
        current_code = self.helper.extract_code(coder_response)
        
        print(current_code)
        
        while self.iter_counter < self.MAX_ITER:
            self.log_message("executor_channel", f"Manager:\nThe iteration {self.iter_counter} starts.")
            executor_response = self.execute_code(current_code, func_name, test_inputs, test_outputs)
            print(f"executor response: {executor_response}")
            self.log_message("executor_channel", f"Executor:\n{executor_response}")

            try: 
                tests_passed = self.analyze_executor_response(executor_response)  
            except Exception as e : 
                self.log_message("executor_channel", f"Manager:\nError analysing: {e}")
            
            if tests_passed: 
                self.log_message("executor_channel", f"All tests passed in iteration {self.iter_counter}")
                return current_code

            self.log_message("executor_channel", f"Manager:\nSome testcases failed. feedback loop starts")
            coder_fb_response, testcase_fb_response = self.provide_feedback(executor_response)
            
            print(f"coder response: {coder_fb_response}")
            print(f"tc response: {testcase_fb_response}")
            
            if "I'm sure the implementation is perfect" not in coder_fb_response:
                current_code = self.helper.extract_code(coder_fb_response)
            if "I'm sure the testcases are true" not in testcase_fb_response:
                test_inputs, test_outputs = self.helper.parse_testcases(testcase_fb_response)

            print(f"current code: {current_code}")
            print(f"test_inputs: {test_inputs}")
            print(f"test_outputs: {test_outputs}")
            
            self.iter_counter +=1 
        
        self.log_message("executor_channel", "MAX_ITER reached without success. Current code will be returned.")
        return current_code
        