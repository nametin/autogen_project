# Mate-Incoder

A multi-agent, Docker-sandboxed pipeline for safe, self-correcting code generation.

## Features

- **Multi-Agent Architecture**: Coordinated agents for code generation, testing, and validation
- **Docker Sandboxing**: Safe execution environment for generated code
- **Self-Correcting**: Iterative improvement through automated feedback loops
- **Benchmark Evaluation**: Built-in support for MBPP dataset evaluation

## Quick Start

### Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys**
   Create a `.env` file on root folder and and add your API keys

3. **Start Docker**
   Ensure Docker Desktop is running or Docker containers are available

4. **Run the pipeline**
   ```bash
   python main.py --init
   ```

5. **View results**
   Monitor workflow outputs and review the generated code

## Configuration

### Model and Timeout Settings

All Docker and LLM configurations are located in `util/helpers.py`. You can modify:
- Model names
- Memory/CPU limits
- Iteration timeouts
- Other pipeline parameters

## Project Structure

```
autogen_project/
├── agents/                     # Agent implementations
│   ├── coder_agent.py         # Code generation agent
│   ├── executor_agent.py      # Code execution agent
│   ├── manager_agent.py       # Workflow orchestration
│   └── test_case_generator_agent.py  # Test case generation
├── eval/                      # Evaluation datasets
│   ├── mbpp.jsonl            # MBPP dataset (974 samples)
│   ├── sample.json           # Sample data
│   └── sanitized-mbpp.json   # Processed MBPP data
├── util/                     # Utility modules
│   ├── docker_module.py      # Docker container management
│   ├── helpers.py            # Configuration and utilities
│   └── run_test.py           # Test execution in containers
├── main.py                   # Entry point
└── requirements.txt          # Python dependencies
```

### Key Components

- **`agents/`**: Contains all agent implementations. The main workflow is orchestrated in `manager_agent.py`'s `run_workflow` method
- **`eval/`**: Houses the benchmark datasets used for evaluation
- **`sandbox/`**: Runtime directory (auto-generated) for Docker operations. Contains copied utilities for secure execution
- **`util/`**: Core utilities for Docker management, configuration, and test execution

## Benchmark Dataset

The project includes the MBPP (Mostly Basic Python Problems) dataset with 974 programming problems for evaluation and benchmarking.

## How It Works

1. **Code Generation**: Agents generate code based on problem descriptions
2. **Test Execution**: Code is executed in isolated Docker containers
3. **Validation**: Results are validated against test cases
4. **Iteration**: Self-correction loop improves code quality
5. **Evaluation**: Performance is measured against benchmark datasets
