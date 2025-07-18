import subprocess
import shlex
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import os

class CommandExecutor:
    """Execute shell commands safely and capture their output for use in prompts."""
    
    def __init__(self, allowed_commands: Optional[List[str]] = None, working_dir: Optional[Path] = None):
        """
        Initialize command executor with security constraints.
        
        Args:
            allowed_commands: List of allowed command prefixes. If None, all commands are allowed.
            working_dir: Working directory for command execution. Defaults to current directory.
        """
        self.allowed_commands = allowed_commands or [
            "git", "ls", "pwd", "date", "whoami", "hostname", "uname",
            "cat", "head", "tail", "wc", "grep", "find", "which",
            "python", "pip", "npm", "node", "cargo", "go", "java",
            "docker", "kubectl", "terraform", "ansible"
        ]
        self.working_dir = working_dir or Path.cwd()
        
    def is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed to be executed."""
        if not command.strip():
            return False
            
        # Parse the command to get the base command
        try:
            parsed = shlex.split(command)
            if not parsed:
                return False
            base_command = parsed[0]
            
            # Check against allowed commands
            return any(base_command.startswith(allowed) for allowed in self.allowed_commands)
        except ValueError:
            # Invalid shell syntax
            return False
    
    def execute_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Execute a shell command and return success status, stdout, and stderr.
        
        Args:
            command: Shell command to execute
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        if not self.is_command_allowed(command):
            return False, "", f"Command not allowed: {command}"
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_dir
            )
            
            return result.returncode == 0, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", f"Error executing command: {str(e)}"
    
    def extract_commands(self, text: str) -> List[Tuple[str, str]]:
        """
        Extract commands from text using various syntaxes:
        - $(command) - shell-like command substitution
        - {cmd:command} - custom command syntax
        - {exec:command} - alternative command syntax
        
        Returns:
            List of (placeholder, command) tuples
        """
        commands = []
        
        # Pattern for $(command)
        shell_pattern = r'\$\(([^)]+)\)'
        for match in re.finditer(shell_pattern, text):
            placeholder = match.group(0)
            command = match.group(1).strip()
            commands.append((placeholder, command))
        
        # Pattern for {cmd:command} or {exec:command}
        custom_pattern = r'\{(?:cmd|exec):([^}]+)\}'
        for match in re.finditer(custom_pattern, text):
            placeholder = match.group(0)
            command = match.group(1).strip()
            commands.append((placeholder, command))
        
        return commands
    
    def process_template(self, template: str, variables: Dict[str, str] = None) -> Tuple[str, Dict[str, str]]:
        """
        Process a template by executing embedded commands and substituting variables.
        
        Args:
            template: Template string with embedded commands and variables
            variables: Dictionary of variable substitutions
            
        Returns:
            Tuple of (processed_template, command_outputs)
        """
        variables = variables or {}
        command_outputs = {}
        processed = template
        
        # Extract and execute commands
        commands = self.extract_commands(template)
        
        for placeholder, command in commands:
            if placeholder in command_outputs:
                # Already executed this command
                continue
                
            success, stdout, stderr = self.execute_command(command)
            
            if success:
                output = stdout.strip()
                command_outputs[placeholder] = output
                processed = processed.replace(placeholder, output)
            else:
                error_msg = f"[ERROR: {stderr.strip() or 'Command failed'}]"
                command_outputs[placeholder] = error_msg
                processed = processed.replace(placeholder, error_msg)
        
        # Substitute regular variables
        for var, value in variables.items():
            processed = processed.replace(f"{{{var}}}", value)
        
        return processed, command_outputs
    
    def get_command_info(self, command: str) -> Dict[str, str]:
        """Get information about a command (help text, version, etc.)."""
        info = {}
        
        if not self.is_command_allowed(command):
            info["error"] = f"Command not allowed: {command}"
            return info
        
        # Try to get version
        for version_flag in ["--version", "-V", "-v", "version"]:
            success, stdout, stderr = self.execute_command(f"{command} {version_flag}")
            if success and stdout.strip():
                info["version"] = stdout.strip().split('\n')[0]
                break
        
        # Try to get help
        for help_flag in ["--help", "-h", "help"]:
            success, stdout, stderr = self.execute_command(f"{command} {help_flag}")
            if success and stdout.strip():
                info["help"] = stdout.strip()
                break
        
        return info