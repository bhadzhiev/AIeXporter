import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Optional
from .command_executor import CommandExecutor

console = Console()

def test_cmd(
    command: str = typer.Argument(..., help="Command to test"),
    timeout: int = typer.Option(30, "--timeout", "-t", help="Command timeout in seconds")
):
    """Test a command to see if it's allowed and get its output."""
    executor = CommandExecutor()
    
    # Check if command is allowed
    if not executor.is_command_allowed(command):
        console.print(f"Command not allowed: {command}", style="red")
        console.print("Allowed command prefixes:", style="yellow")
        for cmd in executor.allowed_commands:
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
            console.print(Panel(stderr, title="Error", expand=False, border_style="red"))

def show_commands():
    """Show allowed commands and their information."""
    executor = CommandExecutor()
    
    console.print("Allowed Commands", style="bold cyan")
    
    table = Table()
    table.add_column("Command", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Version/Info", style="dim")
    
    for cmd in executor.allowed_commands:
        # Try to get command info
        info = executor.get_command_info(cmd)
        
        if "error" in info:
            status = "Not found"
            version = info["error"]
        else:
            status = "Available"
            version = info.get("version", "Unknown")
        
        table.add_row(cmd, status, version)
    
    console.print(table)

def template_test(
    template: str = typer.Argument(..., help="Template string to test"),
    var: Optional[str] = typer.Option(None, "--var", help="Variables in key=value format (can be used multiple times)")
):
    """Test a template with command execution."""
    executor = CommandExecutor()
    
    # Parse variables
    variables = {}
    if var:
        for v in var if isinstance(var, list) else [var]:
            if "=" in v:
                key, value = v.split("=", 1)
                variables[key.strip()] = value.strip()
    
    console.print(f"Testing template:", style="bold")
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