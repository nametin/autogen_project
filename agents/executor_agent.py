import json
import traceback
from util.helpers import Helper
from autogen import ConversableAgent

class ExecutorAgent:
    def __init__(self):
        self.helper = Helper()
        name, system_message, llm_config = self.helper.executor_config()
        
        self.agent= ConversableAgent(
            name=name,
            system_message=system_message,
            llm_config=llm_config    
        )
        
        self.agent.register_for_execution(self._execute)

    @property
    def conversable(self):
        return self.agent


    def _execute(self, messages, sender, config):
        try:
            content = messages[-1]["content"]
            data = json.loads(content)

            code = data["code"]
            function_name = data["function_name"]
            testcases = data["testcases"]

            local_env = {}
            exec(code, {}, local_env)

            func = local_env.get(function_name)
            if not callable(func):
                return f"[Executor ❌] Function '{function_name}' not found."

            results = []
            for i, case in enumerate(testcases):
                try:
                    result = func(*case["input"])
                    passed = result == case["expected_output"]
                    results.append({
                        "input": case["input"],
                        "expected": case["expected_output"],
                        "actual": result,
                        "passed": passed
                    })
                except Exception as e:
                    results.append({
                        "input": case["input"],
                        "expected": case["expected_output"],
                        "actual": str(e),
                        "passed": False,
                        "error": traceback.format_exc()
                    })

            # Özetleme
            passed_count = sum(1 for r in results if r["passed"])
            total = len(results)

            summary = f"🧪 Executor Report: {passed_count}/{total} tests passed.\n\n"
            for r in results:
                status = "✅" if r["passed"] else "❌"
                summary += f"{status} Input: {r['input']} → Expected: {r['expected']}, Got: {r['actual']}\n"

            return summary

        except Exception as e:
            return f"[Executor 💥] Internal error: {str(e)}"


    # for debug
    def run(self, code: str, function_name: str):
        local_env = {}
        try:
            exec(code, {}, local_env)
        except Exception as e:
            print(f"[!] Execution error: {e}")
            return None

        func = local_env.get(function_name)
        if callable(func):
            return func
        else:
            print(f"[!] Function '{function_name}' not found or not callable.")
            return None
