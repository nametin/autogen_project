# docker_module.py

import os
import subprocess
import json
import shutil

class DockerSandbox:
    def __init__(
        self,
        image: str= "python:3.9",
        network: str = "none", 
        memory: str = "512m", 
        cpus: str = "0.5"
    ):
        self.image = image
        self.network = network
        self.memory = memory
        self.cpus = cpus

        self.sandbox_name = "sandbox"
        self.container_dir  = "./sandbox"
        # alttakine erisim yok
        self.sandbox_dir  = "/app/sandbox"

        # Host-side directory to be mounted (called container_dir)
        self.container_dir = os.path.abspath(self.container_dir)

        # Name of the cleanup script inside the sandbox container
        self.cleanup_script_name = "cleanup.sh"

        # Compose volume mapping: host container_dir -> sandbox_dir in container
        self.volume_mapping = f"{self.container_dir}:{self.sandbox_dir}:rw"

        # Prepare base Docker run options for sandbox
        self.run_options = [
            "--network", self.network,
            "--memory", self.memory,
            "--cpus", self.cpus,
            "-v", self.volume_mapping,
            "--name", self.sandbox_name,
            "-d"
        ]

    def start(self):
        """
        Starts a detached Docker container named `sandbox` with the configured resources
        and mounts. The container runs `tail -f /dev/null` to stay alive.
        """
        # Ensure the host-side workspace directory exists
        os.makedirs(self.container_dir, exist_ok=True)

        # Build the full docker run command
        cmd = ["docker", "run"] + self.run_options + [self.image, "tail", "-f", "/dev/null"]
        print(cmd)
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to start sandbox container: {e}") from e

    def cleanup(self):
        """
        Removes all files under the sandbox directory inside the running container.
        Equivalent to running `rm -rf /app/sandbox/*` inside the container.
        """
        # Build the docker exec command
        cmd = [
            "docker",
            "exec",
            self.sandbox_name,
            "bash",
            "-c",
            f"rm -rf {self.sandbox_dir}/*",
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().strip().lower()
            if "no such file or directory" in stderr:
                return
            raise RuntimeError(f"Failed to cleanup sandbox workspace: {stderr}") from e

    def exec(self, cmd: list, timeout: int = 5) -> dict:
        full_cmd = ["docker", "exec", self.sandbox_name] + cmd
        try:
            proc = subprocess.run(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {"error": "[timeout]"}

        out, err = proc.stdout.decode().strip(), proc.stderr.decode().strip()
        print(err)
        if proc.returncode != 0:
            try:
                return json.loads(out)
            except json.JSONDecodeError:
                return {"error": err or out}
        try:
            return json.loads(out)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON: {e}\nOutput: {out}")

    def exec_batch(
        self, python_code_b64: str, inputs: list, timeout: int = 5
    ) -> dict:
        """
        Runs each testcase in the sandbox using run_test.py and returns all results.
        """

        py_path = os.path.join(self.container_dir, "run_test.py")
        self.copy_file("./util/run_test.py",py_path)

        payload = {"python_code_b64": python_code_b64, "inputs": inputs}
        payload_path = os.path.join(self.container_dir, "payload.json")

        with open(payload_path, "w") as f:
            json.dump(payload, f)

        py_sandbox_path = f"{self.sandbox_dir}/run_test.py"
        payload_sandbox_path = f"{self.sandbox_dir}/payload.json"
        executions = []
        for idx in range(len(inputs)):
            cmd = [
                "python",
                py_sandbox_path,
                payload_sandbox_path,
                str(idx),
            ]

            res = self.exec(cmd, timeout=timeout)
            executions.append(res)

        return {"executions": executions}

    def stop(self):
        """
        Stops and removes the sandbox container named `sandbox`.
        If the container is not found or already stopped, it ignores that error.
        """
        
        self.cleanup()
        
        cmd = ["docker", "rm", "-f", self.sandbox_name]
        try:
            # -f: stop running container if needed and then remove
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().lower()
            if "no such container" in stderr:
                return
            raise RuntimeError(f"Failed to stop sandbox container: {stderr.strip()}") from e

    def copy_file(self,src_path: str, dest_path: str) -> None: 
        if not os.path.isfile(src_path):
            raise FileNotFoundError(f"Host file not found: {src_path}")
        # Ensure destination directory exists
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        try:
            shutil.copy2(src_path, dest_path)
        except Exception as e:
            raise RuntimeError(f"Failed to copy file into sandbox: {e}") from e

    def copy_file_to_docker(self, src_path: str, dest_path: str) -> None:
        # Ensure the source file exists
        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Host file not found: {src_path}")

        # Build and run the docker cp command
        cmd = ["docker", "cp", src_path, f"{self.sandbox_name}:{dest_path}"]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(  "done")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode().strip()
            print(stderr)
            raise RuntimeError(f"Failed to copy '{src_path}' into sandbox: {stderr}") from e
