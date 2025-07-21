import typer
from rich.console import Console
from typing import Optional
from .executor import CommandExecutor
from .security import DefaultSecurityValidator

console = Console()


def test_cmd(
    command: str = typer.Argument(..., help="Command to test"),
    timeout: int = typer.Option(
        30, "--timeout", "-t", help="Command timeout in seconds"
    ),
):
    """Test a command to see if it's allowed and get its output."""
    from ..config import Config
    config = Config()
    
    disabled_commands = config.get_disabled_commands()
    security_validator = DefaultSecurityValidator(disabled_commands=disabled_commands or None)
    executor = CommandExecutor(security_validator=security_validator, timeout=timeout)

    # Check if command is allowed
    if not executor.is_command_allowed(command):
        console.print(f"Command disabled for security: {command}", style="red")
        console.print("Disabled command patterns:", style="yellow")
        for cmd in security_validator.disabled_commands:
            console.print(f"  - {cmd}", style="dim")
        return

    console.print(f"Testing command: [cyan]{command}[/cyan]")

    # Execute the command
    success, stdout, stderr = executor.execute(command)

    if success:
        console.print("Command executed successfully", style="green")
        if stdout:
            console.print("Output:")
        console.print(stdout)
    else:
        console.print("Command failed", style="red")
        if stderr:
            console.print("Error:")
            console.print(stderr)


def show_commands():
    """Show command execution status and disabled commands."""
    from ..config import Config
    config = Config()
    
    disabled_commands = config.get_disabled_commands()
    commands_enabled = config.get_commands_enabled()

    console.print("Command Execution Status", style="bold cyan")
    console.print(f"Commands enabled globally: {commands_enabled}", style="green" if commands_enabled else "red")
    
    if disabled_commands:
        console.print("\nDisabled Commands:", style="bold red")
        for cmd in disabled_commands:
            console.print(f"  {cmd}: Security restriction")
    else:
        console.print("\nNo additional disabled commands (using default security list)", style="dim")
        
    console.print("\n[dim]Note: Commands are enabled by default but restricted by security patterns[/dim]")


def template_test(
    template: str = typer.Argument(..., help="Template string to test"),
    var: Optional[str] = typer.Option(
        None, "--var", help="Variables in key=value format (can be used multiple times)"
    ),
):
    """Test a template with command execution."""
    from ..config import Config
    config = Config()
    
    disabled_commands = config.get_disabled_commands()
    security_validator = DefaultSecurityValidator(disabled_commands=disabled_commands or None)
    executor = CommandExecutor(security_validator=security_validator)

    # Parse variables
    variables = {}
    if var:
        for v in var if isinstance(var, list) else [var]:
            if "=" in v:
                key, value = v.split("=", 1)
                variables[key.strip()] = value.strip()

    console.print("Testing template:", style="bold")
    console.print("Template:")
    console.print(template)

    console.print("\n[dim]Note: Template processing functionality has been moved to the template module[/dim]")
    console.print("Current template testing is limited to command validation.")
    
    # For now, just validate any commands in the template
    import re
    commands = re.findall(r'\$\([^)]+\)|\{cmd:[^}]+\}|\{exec:[^}]+\}', template)
    if commands:
        console.print("Found commands:", style="yellow")
        for cmd_placeholder in commands:
            cmd = cmd_placeholder.strip('$(){}').replace('cmd:', '').replace('exec:', '')
            if executor.is_command_allowed(cmd):
                console.print(f"  {cmd_placeholder} → {cmd} [green]✓[/green]")
            else:
                console.print(f"  {cmd_placeholder} → {cmd} [red]✗[/red]")
    
    # Show template with variables substituted (basic)
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{key}}}", value)
    
    console.print("\nTemplate with variables:")
    console.print(result)