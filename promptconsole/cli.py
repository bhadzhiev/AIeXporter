import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional, List
from pathlib import Path

from .storage import PromptStorage
from .template import PromptTemplate, TemplateSafeEncoder
from .config import Config
from .api_client import get_client, APIResponse
from .api_keys import setup_api_key
from .command_executor import CommandExecutor
from . import commands
from .completion import (
    complete_prompt_names, complete_providers, complete_models, 
    complete_prompt_variables, complete_config_keys, complete_tags, complete_formats
)

app = typer.Typer(
    name="promptconsole",
    help="A comprehensive prompt management and execution tool",
    rich_markup_mode="rich"
)
console = Console()

@app.command()
def create(
    name: str = typer.Argument(..., help="Name of the prompt template"),
    template: str = typer.Argument(..., help="Template content with {variable} syntax"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Description of the prompt"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags for organization", autocompletion=complete_tags),
    format: str = typer.Option("yaml", "--format", "-f", help="Storage format (yaml/json)", autocompletion=complete_formats)
):
    """Create a new prompt template."""
    storage = PromptStorage()
    
    # Automatically unescape template if it contains escaped characters
    encoder = TemplateSafeEncoder()
    unescaped_template = encoder.unescape_template(template)
    
    prompt = PromptTemplate(
        name=name,
        template=unescaped_template,
        description=description or "",
        tags=tags or [],
        variables=PromptTemplate.extract_variables(unescaped_template)
    )
    
    success = storage.save_prompt(prompt, format)
    if success:
        console.print(f"Prompt '{name}' created successfully!", style="green")
    else:
        console.print(f"Failed to create prompt '{name}'", style="red")

@app.command()
def list():
    """List all saved prompts."""
    storage = PromptStorage()
    prompts = storage.list_prompts()
    
    if not prompts:
        console.print("No prompts found", style="yellow")
        return
    
    table = Table(title="Saved Prompts")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Variables", style="magenta")
    table.add_column("Tags", style="green")
    table.add_column("Description", style="dim")
    
    for prompt in prompts:
        variables = ", ".join(prompt.variables) if prompt.variables else "None"
        tags = ", ".join(prompt.tags) if prompt.tags else "None"
        table.add_row(prompt.name, variables, tags, prompt.description[:50] + "..." if len(prompt.description) > 50 else prompt.description)
    
    console.print(table)

@app.command()
def show(
    name: str = typer.Argument(..., help="Name of the prompt to show", autocompletion=complete_prompt_names)
):
    """Show detailed information about a prompt."""
    storage = PromptStorage()
    prompt = storage.get_prompt(name)
    
    if not prompt:
        console.print(f"Prompt '{name}' not found", style="red")
        return
    
    panel_content = f"""[bold cyan]Name:[/bold cyan] {prompt.name}
[bold cyan]Description:[/bold cyan] {prompt.description}
[bold cyan]Variables:[/bold cyan] {', '.join(prompt.variables) if prompt.variables else 'None'}
[bold cyan]Tags:[/bold cyan] {', '.join(prompt.tags) if prompt.tags else 'None'}

[bold cyan]Template:[/bold cyan]
{prompt.template}"""
    
    console.print(Panel(panel_content, title="Prompt Details", expand=False))

@app.command()
def delete(
    name: str = typer.Argument(..., help="Name of the prompt to delete", autocompletion=complete_prompt_names),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete a prompt."""
    storage = PromptStorage()
    
    if not storage.get_prompt(name):
        console.print(f"Prompt '{name}' not found", style="red")
        return
    
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete prompt '{name}'?")
        if not confirm:
            console.print("Operation cancelled", style="yellow")
            return
    
    success = storage.delete_prompt(name)
    if success:
        console.print(f"Prompt '{name}' deleted successfully!", style="green")
    else:
        console.print(f"Failed to delete prompt '{name}'", style="red")

@app.command()
def run(
    name: str = typer.Argument(..., help="Name of the prompt to run", autocompletion=complete_prompt_names),
    params: Optional[List[str]] = typer.Option(None, "--param", "-p", help="Parameters in key=value format", autocompletion=complete_prompt_variables),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Preview the generated prompt without executing"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Save output to file"),
    provider: Optional[str] = typer.Option(None, "--provider", help="API provider (openrouter, openai, anthropic)", autocompletion=complete_providers),
    model: Optional[str] = typer.Option(None, "--model", help="Model to use", autocompletion=complete_models),
    stream: bool = typer.Option(False, "--stream", help="Stream the response"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens", help="Maximum tokens to generate"),
    temperature: Optional[float] = typer.Option(None, "--temperature", help="Temperature for generation"),
    execute: bool = typer.Option(False, "--execute", "-e", help="Execute the prompt via API"),
    enable_commands: bool = typer.Option(False, "--enable-commands", help="Enable command execution in templates")
):
    """Run a prompt with parameter substitution and optional API execution."""
    storage = PromptStorage()
    config = Config()
    prompt = storage.get_prompt(name)
    
    if not prompt:
        console.print(f"Prompt '{name}' not found", style="red")
        return
    
    # Parse parameters
    param_dict = {}
    if params:
        for param in params:
            if "=" not in param:
                console.print(f"Invalid parameter format: {param}. Use key=value", style="red")
                return
            key, value = param.split("=", 1)
            param_dict[key.strip()] = value.strip()
    
    # Check for missing variables
    missing_vars = set(prompt.variables) - set(param_dict.keys())
    if missing_vars:
        console.print(f"Missing required variables: {', '.join(missing_vars)}", style="red")
        return
    
    # Generate the final prompt
    if enable_commands:
        # Execute commands in the template
        executor = CommandExecutor()
        generated_prompt, command_outputs = prompt.render(param_dict, execute_commands=True, command_executor=executor)
        
        if command_outputs:
            console.print("Executed commands:", style="blue")
            for cmd_placeholder, output in command_outputs.items():
                console.print(f"  {cmd_placeholder} → {output[:100]}{'...' if len(output) > 100 else ''}", style="dim")
    else:
        generated_prompt = prompt.render_simple(param_dict)
    
    if dry_run:
        console.print(Panel(generated_prompt, title="Dry Run - Generated Prompt", expand=False))
        return
    
    # If not executing via API, just show/save the generated prompt
    if not execute:
        if output:
            if isinstance(output, str):
                output = Path(output)
            output.write_text(generated_prompt)
            console.print(f"Generated prompt saved to {output}", style="green")
        else:
            console.print(Panel(generated_prompt, title="Generated Prompt", expand=False))
        return
    
    # Execute via API
    selected_provider = provider or config.get_default_provider()
    api_key = config.get_api_key(selected_provider)
    
    if not api_key:
        console.print(f"No API key found for provider '{selected_provider}'", style="red")
        console.print(f"💡 Set it up with: python main.py api-key {selected_provider}", style="yellow")
        if typer.confirm("Would you like to set it up now?"):
            if setup_api_key(selected_provider):
                api_key = config.get_api_key(selected_provider)
            else:
                return
        else:
            return
    
    try:
        client = get_client(selected_provider, api_key)
        selected_model = model or config.get_default_model(selected_provider)
        
        # Prepare API parameters
        api_params = {}
        if max_tokens:
            api_params["max_tokens"] = max_tokens
        elif selected_provider == "anthropic":
            api_params["max_tokens"] = config.get("max_tokens", 1024)
        
        if temperature is not None:
            api_params["temperature"] = temperature
        else:
            api_params["temperature"] = config.get("temperature", 0.7)
        
        console.print(f"Executing via {selected_provider} using {selected_model}...", style="blue")
        
        if stream:
            console.print("Streaming response:", style="cyan")
            response_text = ""
            for chunk in client.stream_generate(generated_prompt, selected_model, **api_params):
                console.print(chunk, end="")
                response_text += chunk
            console.print()  # New line after streaming
        else:
            with console.status("🔄 Generating response..."):
                response = client.generate(generated_prompt, selected_model, **api_params)
            response_text = response.content
            
            # Show usage info if available
            if response.usage:
                usage = response.usage
                console.print(f"\nUsage: {usage.get('prompt_tokens', 0)} prompt + {usage.get('completion_tokens', 0)} completion = {usage.get('total_tokens', 0)} total tokens", style="dim")
        
        # Output result
        if output:
            if isinstance(output, str):
                output = Path(output)
            output.write_text(response_text)
            console.print(f"\nResponse saved to {output}", style="green")
        else:
            console.print(Panel(response_text, title="API Response", expand=False))
        
        client.close()
        
    except Exception as e:
        console.print(f"API Error: {str(e)}", style="red")

@app.command()
def config(
    key: Optional[str] = typer.Argument(None, help="Configuration key to get/set", autocompletion=complete_config_keys),
    value: Optional[str] = typer.Argument(None, help="Value to set"),
    list_all: bool = typer.Option(False, "--list", "-l", help="List all configuration")
):
    """Manage configuration settings."""
    config_manager = Config()
    
    if list_all or (not key and not value):
        settings = config_manager.get_all()
        if not settings:
            console.print("📝 No configuration found", style="yellow")
            return
        
        table = Table(title="⚙️  Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="magenta")
        
        for k, v in settings.items():
            # Mask API keys for security
            if k == "api_keys" and isinstance(v, dict):
                masked_keys = {}
                for provider, api_key in v.items():
                    if isinstance(api_key, str) and len(api_key) > 8:
                        masked_keys[provider] = f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"
                    else:
                        masked_keys[provider] = "*" * len(str(api_key))
                table.add_row(k, str(masked_keys))
            else:
                table.add_row(k, str(v))
        
        console.print(table)
        return
    
    if key and not value:
        # Get value
        val = config_manager.get(key)
        if val is not None:
            # Mask API keys for security
            if "api_key" in key.lower() and isinstance(val, str):
                if len(val) > 8:
                    val = f"{val[:4]}{'*' * (len(val) - 8)}{val[-4:]}"
                else:
                    val = "*" * len(val)
            console.print(f"[cyan]{key}[/cyan]: {val}")
        else:
            console.print(f"Configuration key '{key}' not found", style="red")
    elif key and value:
        # Set value
        config_manager.set(key, value)
        console.print(f"Set {key} = {value}", style="green")
    else:
        console.print("Please provide a key or use --list", style="red")

@app.command("api-key")
def api_key_command(
    provider: str = typer.Argument(..., help="Provider (openrouter, openai, anthropic)", autocompletion=complete_providers),
    action: str = typer.Option("set", "--action", "-a", help="Action: set, get, delete")
):
    """Manage API keys for different providers."""
    config_manager = Config()
    
    if action == "set":
        setup_api_key(provider)
    elif action == "get":
        key = config_manager.get_api_key(provider)
        if key:
            # Show only first and last 4 characters for security
            masked_key = f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}" if len(key) > 8 else "*" * len(key)
            console.print(f"🔑 {provider}: {masked_key}")
        else:
            console.print(f"No API key found for {provider}", style="red")
    elif action == "delete":
        if config_manager.get_api_key(provider):
            if typer.confirm(f"Delete API key for {provider}?"):
                api_keys = config_manager.get("api_keys", {})
                if provider in api_keys:
                    del api_keys[provider]
                    config_manager.set("api_keys", api_keys)
                    console.print(f"API key for {provider} deleted", style="green")
        else:
            console.print(f"No API key found for {provider}", style="red")
    else:
        console.print(f"Invalid action: {action}. Use: set, get, delete", style="red")

@app.command()
def safe_template(template: str = typer.Argument(..., help="Template content to encode safely")):
    """Encode a template string for safe CLI usage."""
    encoder = TemplateSafeEncoder()
    
    # Show the escaped version
    escaped = encoder.escape_template(template)
    console.print(f"Escaped template:", style="cyan")
    console.print(escaped)
    
    # Show the safely quoted version for CLI
    quoted = encoder.format_for_cli(template)
    console.print(f"\nSafe CLI format:", style="green")
    console.print(quoted)
    
    # Show example usage
    console.print(f"\nExample usage:", style="yellow")
    console.print(f"python main.py create \"my-prompt\" {quoted}")
    
    # Test round-trip
    unescaped = encoder.unescape_template(escaped)
    if unescaped == template:
        console.print("\nRound-trip test passed", style="green")
    else:
        console.print("\nRound-trip test failed", style="red")

# Add command testing subcommands
cmd_app = typer.Typer(name="cmd", help="Command execution utilities")
cmd_app.command("test")(commands.test_cmd)
cmd_app.command("list")(commands.show_commands)
cmd_app.command("template-test")(commands.template_test)
app.add_typer(cmd_app, name="cmd")

@app.command()
def upgrade():
    """Upgrade aix to the latest version from GitHub."""
    console = Console()
    
    console.print("Upgrading aix to latest version...", style="cyan")
    
    try:
        import subprocess
        import sys
        
        # Skip uv tool upgrade as it doesn't work for git installs
        result = subprocess.run([
            sys.executable, "-m", "uv", "tool", "install", "aix", 
            "--from", "git+https://github.com/bhadzhiev/prompt.git", "--force"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            console.print("Successfully upgraded via uv tool", style="green")
            console.print("Run: aix --help to verify the upgrade", style="green")
        else:
            console.print("Upgrade failed", style="red")
            console.print("Error:", result.stderr, style="red")
            console.print("Please run: uv tool install aix --from git+https://github.com/bhadzhiev/prompt.git --force", style="yellow")
            
    except Exception as e:
        console.print(f"Upgrade failed: {e}", style="red")
        console.print("Please run: uv tool install aix --from git+https://github.com/bhadzhiev/prompt.git", style="yellow")

if __name__ == "__main__":
    app()