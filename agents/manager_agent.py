import json
from util.helpers import Helper
from agents.coder_agent import CoderAgent
from agents.test_case_generator_agent import TestcaseGeneratorAgent
from agents.executor_agent import ExecutorAgent

class ManagerAgent:
    def __init__(self, func_name="my_function"):
        self.helper = Helper()
        self.max_iterations = 10
        self.func_name = func_name
        
        self.coder_agent = CoderAgent()
        self.testcase_agent = TestcaseGeneratorAgent()
        self.executor_agent = ExecutorAgent()

    def run_sequential_chat(self, description, validation_testcases):
        iteration = 0
        generated_code = None
        
        while iteration < self.max_iterations:
            print(f"Iteration {iteration+1} started.")
            
            # Adım 1: Testcase Generator'dan ek test caseleri üretme (yalnızca description ile)
            tc_prompt = self.helper.build_tc_prompt(description)
            tc_response = self.testcase_agent.conversable.generate_reply(messages=[{"role": "user", "content": tc_prompt}])
            
            try:
                test_set = json.loads(tc_response)
            except Exception as e:
                print("Error parsing test cases:", e)
                return None
            
            print(test_set)
            
            # Adım 2: Coder Agent'ten kod üretimi (yalnızca validation test caseleri ve description ile)
            # validation_testcases: tuple (list_of_inputs, list_of_expected_outputs)
            sample_inputs, expected_outputs = validation_testcases
            coder_prompt = self.helper.build_coder_prompt(self.func_name, description, sample_inputs, expected_outputs)
            coder_response = self.coder_agent.conversable.generate_reply(messages=[{"role": "user", "content": coder_prompt}])
            generated_code = self.helper.extract_code(coder_response)
            print("\n\n")
            print(generated_code)
            
            # Adım 3: Executor Agent'e kodu, test setini gönderip testleri çalıştırma
            execution_payload = {
                "code": generated_code,
                "function_name": self.func_name,
                "testcases": test_set
            }
            exec_msg = json.dumps(execution_payload)
            exec_response = self.executor_agent.conversable.generate_reply(messages=[{"role": "user", "content": exec_msg}])
            print("\nExecutor response:\n", exec_response)
            
            # Adım 4: Test sonuçlarını değerlendirme
            if self._all_tests_passed(exec_response):
                print("All tests passed. Final code generated.")
                return generated_code
            else:
                # Hata içeren testleri özetle
                feedback = self._extract_feedback(exec_response)
                print("Feedback for revision:\n", feedback)
                # Geri bildirimi Coder Agent'e ekleyip kodu revize ettiriyoruz
                coder_prompt += "\nFEEDBACK:\n" + feedback
                coder_response = self.coder_agent.conversable.generate_reply(messages=[{"role": "user", "content": coder_prompt}])
                generated_code = self.helper.extract_code(coder_response)
                iteration += 1
        
        return "Maximum iterations reached without all tests passing."

    def _all_tests_passed(self, report):
        """
        Basit bir kontrol: Rapor içerisinde başarısız test işareti (örneğin "❌") varsa testler geçmemiş demektir.
        Bu kontrolü geliştirmek gerekebilir.
        """
        return "❌" not in report

    def _extract_feedback(self, report):
        """
        Executor raporundan hata içeren satırları çıkartarak basit bir geri bildirim metni oluşturur.
        """
        feedback_lines = []
        for line in report.splitlines():
            if "❌" in line:
                feedback_lines.append(line)
        return "\n".join(feedback_lines) if feedback_lines else "No specific feedback extracted."

