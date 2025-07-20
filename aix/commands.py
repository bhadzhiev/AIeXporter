import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Optional
from .command_executor import CommandExecutor

console = Console()


def test_cmd(
    command: str = typer.Argument(..., help="Command to test"),
    timeout: int = typer.Option(
        30, "--timeout", "-t", help="Command timeout in seconds"
    ),
):
    """Test a command to see if it's allowed and get its output."""
    from .config import Config
    config = Config()
    
    disabled_commands = config.get_disabled_commands()
    executor = CommandExecutor(disabled_commands=disabled_commands or None)

    # Check if command is allowed
    if not executor.is_command_allowed(command):
        console.print(f"Command disabled for security: {command}", style="red")
        console.print("Disabled command patterns:", style="yellow")
        for cmd in executor.disabled_commands:
            console.print(f"  - {cmd}", style="dim")
        return

    console.print(f"Testing command: [cyan]{command}[/cyan]")

    # Execute the command
    success, stdout, stderr = executor.execute_command(command, timeout)

    if success:
        console.print("Command executed successfully", style="green")
        if stdout:
            console.print(Panel(stdout, title="Output", expand=False))
    else:
        console.print("Command failed", style="red")
        if stderr:
            console.print(
                Panel(stderr, title="Error", expand=False, border_style="red")
            )


def show_commands():
    """Show command execution status and disabled commands."""
    from .config import Config
    config = Config()
    
    disabled_commands = config.get_disabled_commands()
    executor = CommandExecutor(disabled_commands=disabled_commands or None)
    commands_enabled = config.get_commands_enabled()

    console.print("Command Execution Status", style="bold cyan")
    console.print(f"Commands enabled globally: {commands_enabled}", style="green" if commands_enabled else "red")
    
    if disabled_commands:
        console.print("\nDisabled Commands:", style="bold red")
        table = Table()
        table.add_column("Disabled Pattern", style="red")
        table.add_column("Reason", style="dim")

        for cmd in disabled_commands:
            table.add_row(cmd, "Security restriction")
        
        console.print(table)
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
    from .config import Config
    config = Config()
    
    disabled_commands = config.get_disabled_commands()
    executor = CommandExecutor(disabled_commands=disabled_commands or None)

    # Parse variables
    variables = {}
    if var:
        for v in var if isinstance(var, list) else [var]:
            if "=" in v:
                key, value = v.split("=", 1)
                variables[key.strip()] = value.strip()

    console.print("Testing template:", style="bold")
    console.print(Panel(template, title="Template", expand=False))

    # Extract commands first
    commands = executor.extract_commands(template)
    if commands:
        console.print("Found commands:", style="yellow")
        for placeholder, command in commands:
            console.print(f"  {placeholder} → {command}")

    # Process template
    try:
        result, command_outputs = executor.process_template(template, variables)

        if command_outputs:
            console.print("\nCommand outputs:", style="blue")
            for placeholder, output in command_outputs.items():
                console.print(f"  {placeholder}")
                console.print(Panel(output, border_style="blue", expand=False))

        console.print("\nFinal result:", style="green")
        console.print(Panel(result, title="Processed Template", expand=False))

    except Exception as e:
        console.print(f"Error processing template: {e}", style="red")
