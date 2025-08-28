Mate-Incoder is a multi-agent, Docker-sandboxed pipeline for safe, self-correcting code generation.

QUICK START: 
-Install dependencies
pip install -r requirements.txt

-Place your API keys in .env

-Run Docker Desktop on your machine. Or, at least make sure Docker Container is available to built and start.

-Replace your description and sample runs\outputs in main.py, then start the main
python main.py --init

-View the workflow outputs, and eventually the final code.

CONFIGURATION
-Changing models or timeouts
All Docker and LLM settings live in util/helpers.py. Tweak model names, memory/CPU limits, or iteration caps there.

BENCHMARK DATASET
All data is under eval folder. mbpp.jsonl file is the dataset consisting of 974 sample.

FOLDERS INFORMATION
-agents folder consists of the python files of the agents used in this program. All the workflow is coded under manager_agent.py run_workflow method.
-eval folder has the dataset and used in evaluation of this work.
-sandbox folder: Nothing to do with it. It's just needed for Docker bidding. The util/run_test.py and a payload.json is copied in it in the runtime for 
Executor agent and docker module to reach and run testcases in docker container. After the program execution, its context is cleaned. 
-util folder has the docker_module, helpers and run_test python files. run_test file is the file that is called in docker container by executor agent. 
This is why it's copied under sandbox folder in runtime. 
