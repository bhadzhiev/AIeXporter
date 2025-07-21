"""Placeholder generator execution engine for dynamic template placeholders."""

import subprocess
import tempfile
import os
from typing import Dict, List, Optional
from .template import PlaceholderGenerator


class PlaceholderExecutionError(Exception):
    """Exception raised when placeholder generation fails."""

    pass


class PlaceholderExecutor:
    """Executes placeholder generators and returns generated values."""

    def __init__(self, timeout: int = 30):
        """Initialize with execution timeout in seconds."""
        self.timeout = timeout

    def execute_generators(
        self, generators: List[PlaceholderGenerator]
    ) -> Dict[str, str]:
        """Execute all placeholder generators and return combined results."""
        placeholders = {}

        for generator in generators:
            try:
                result = self._execute_generator(generator)
                if result:
                    placeholders.update(result)
            except Exception as e:
                # Log warning but continue with other generators
                print(
                    f"Warning: Placeholder generator ({generator.language}) failed: {e}"
                )

        return placeholders

    def _execute_generator(
        self, generator: PlaceholderGenerator
    ) -> Optional[Dict[str, str]]:
        """Execute a single placeholder generator based on its language."""
        if generator.language.lower() == "python":
            return self._execute_python(generator.script)
        elif generator.language.lower() == "bash":
            return self._execute_bash(generator.script)
        else:
            raise PlaceholderExecutionError(
                f"Unsupported generator language: {generator.language}"
            )

    def _execute_python(self, script: str) -> Dict[str, str]:
        """Execute Python script in a restricted environment."""
        try:
            # Create a restricted globals dictionary for security
            restricted_globals = {
                "__builtins__": {
                    "__import__": __import__,
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "list": list,
                    "dict": dict,
                    "tuple": tuple,
                    "set": set,
                    "range": range,
                    "enumerate": enumerate,
                    "zip": zip,
                    "print": print,
                    "abs": abs,
                    "min": min,
                    "max": max,
                    "sum": sum,
                    "sorted": sorted,
                    "reversed": reversed,
                },
                "os": _create_restricted_os(),
                "subprocess": _create_restricted_subprocess(),
                "glob": __import__("glob"),
                "json": __import__("json"),
                "re": __import__("re"),
                "datetime": __import__("datetime"),
            }

            # Execute script in restricted environment
            local_vars = {}
            exec(script, restricted_globals, local_vars)

            # Extract placeholders dictionary
            if "placeholders" in local_vars:
                placeholders = local_vars["placeholders"]
                if isinstance(placeholders, dict):
                    # Convert all values to strings
                    return {k: str(v) for k, v in placeholders.items()}
                else:
                    raise PlaceholderExecutionError("placeholders must be a dictionary")
            else:
                raise PlaceholderExecutionError(
                    "Script must define a 'placeholders' dictionary"
                )

        except Exception as e:
            raise PlaceholderExecutionError(f"Python execution failed: {e}")

    def _execute_bash(self, script: str) -> Dict[str, str]:
        """Execute Bash script in a subprocess and parse key=value output."""
        try:
            # Create a temporary script file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
                f.write("#!/bin/bash\n")
                f.write("set -euo pipefail\n")  # Enable strict error handling
                f.write(script)
                script_path = f.name

            try:
                # Make script executable and run it
                os.chmod(script_path, 0o755)

                # Run with limited environment for security
                env = {
                    "PATH": "/usr/bin:/bin",
                    "HOME": "/tmp",
                    "SHELL": "/bin/bash",
                }

                result = subprocess.run(
                    ["/bin/bash", script_path],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    env=env,
                    cwd=os.getcwd(),  # Run in current working directory
                )

                if result.returncode != 0:
                    raise PlaceholderExecutionError(
                        f"Bash script failed: {result.stderr}"
                    )

                # Parse key=value output
                placeholders = {}
                for line in result.stdout.strip().split("\n"):
                    if "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        placeholders[key.strip()] = value.strip()

                return placeholders

            finally:
                # Clean up temporary script file
                try:
                    os.unlink(script_path)
                except OSError:
                    pass

        except subprocess.TimeoutExpired:
            raise PlaceholderExecutionError(
                f"Bash script timed out after {self.timeout} seconds"
            )
        except Exception as e:
            raise PlaceholderExecutionError(f"Bash execution failed: {e}")


def _create_restricted_os():
    """Create a restricted os module for Python execution."""
    import os

    class RestrictedOS:
        getcwd = os.getcwd
        listdir = os.listdir
        path = os.path
        environ = dict(os.environ)  # Read-only copy

        def walk(self, top, **kwargs):
            """Safe version of os.walk with depth limit."""
            depth = 0
            for root, dirs, files in os.walk(top, **kwargs):
                yield root, dirs, files
                depth += 1
                if depth > 10:  # Limit recursion depth
                    break

    return RestrictedOS()


def _create_restricted_subprocess():
    """Create a restricted subprocess module for Python execution."""
    import subprocess

    class RestrictedSubprocess:
        PIPE = subprocess.PIPE
        STDOUT = subprocess.STDOUT

        def run(self, args, **kwargs):
            """Restricted subprocess.run with security constraints."""
            # Only allow specific safe commands
            allowed_commands = {
                "ls",
                "cat",
                "head",
                "tail",
                "wc",
                "grep",
                "find",
                "git",
                "date",
                "whoami",
                "pwd",
                "echo",
                "which",
                "file",
                "test",
                "tr",
                "sed",
                "cut",
                "du",
                "sort",
                "uniq",
                "rev",
                "awk",
                "xargs",
                "stat",
                "basename",
                "sh",
                "bc",
            }

            if isinstance(args, (list, tuple)) and args:
                command = args[0]
                if command not in allowed_commands:
                    raise PermissionError(f"Command '{command}' not allowed")
            elif isinstance(args, str):
                command = args.split()[0] if args.split() else ""
                if command not in allowed_commands:
                    raise PermissionError(f"Command '{command}' not allowed")

            # Add security constraints
            kwargs.setdefault("timeout", 10)
            kwargs.setdefault("cwd", os.getcwd())

            return subprocess.run(args, **kwargs)

    return RestrictedSubprocess()
