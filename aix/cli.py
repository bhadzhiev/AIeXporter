import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional, List
from pathlib import Path
import os
import subprocess
import tempfile

from .storage import PromptStorage
from .template import PromptTemplate, TemplateSafeEncoder
from .config import Config
from .api_client import get_client, APIResponse
from .api_keys import setup_api_key
from .command_executor import CommandExecutor
from . import commands
from . import __version__
from .completion import (
    complete_prompt_names, complete_providers, complete_models, 
    complete_prompt_variables, complete_config_keys, complete_tags, complete_formats
)

def version_callback(value: bool):
    if value:
        console = Console()
        console.print(f"[bold cyan]aix (AI eXecutor)[/bold cyan] version [bold green]{__version__}[/bold green]")
        raise typer.Exit()

app = typer.Typer(
    name="aix",
    help="A comprehensive prompt management and execution tool",
    rich_markup_mode="rich"
)
console = Console()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-V", 
        callback=version_callback, 
        is_eager=True,
        help="Show version and exit"
    )
):
    """AI eXecutor (aix) - Your AI butler that lives in the terminal."""
    pass

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
def list(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag", autocompletion=complete_tags)
):
    """List all saved prompts."""
    storage = PromptStorage()
    prompts = storage.list_prompts()
    
    # Filter by tag if specified
    if tag:
        prompts = [p for p in prompts if tag in p.tags]
        if not prompts:
            console.print(f"No prompts found with tag '{tag}'", style="yellow")
            return
    
    if not prompts:
        console.print("No prompts found", style="yellow")
        return
    
    if verbose:
        # Verbose mode: show detailed information for each prompt
        for i, prompt in enumerate(prompts):
            if i > 0:
                console.print()  # Add spacing between prompts
            
            panel_content = f"""[bold cyan]Name:[/bold cyan] {prompt.name}
[bold cyan]Description:[/bold cyan] {prompt.description or 'No description'}
[bold cyan]Variables:[/bold cyan] {', '.join(prompt.variables) if prompt.variables else 'None'}
[bold cyan]Tags:[/bold cyan] {', '.join(prompt.tags) if prompt.tags else 'None'}
[bold cyan]Created:[/bold cyan] {prompt.created_at}
[bold cyan]Updated:[/bold cyan] {prompt.updated_at}

[bold cyan]Template:[/bold cyan]
{prompt.template[:200]}{'...' if len(prompt.template) > 200 else ''}"""
            
            console.print(Panel(panel_content, title=f"Prompt {i+1}/{len(prompts)}", expand=False))
    else:
        # Standard table view
        title = "Saved Prompts"
        if tag:
            title += f" (filtered by tag: {tag})"
        
        table = Table(title=title)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Variables", style="magenta")
        table.add_column("Tags", style="green")
        table.add_column("Description", style="dim")
        
        for prompt in prompts:
            variables = ", ".join(prompt.variables) if prompt.variables else "None"
            tags = ", ".join(prompt.tags) if prompt.tags else "None"
            table.add_row(
                prompt.name, 
                variables, 
                tags, 
                prompt.description[:50] + "..." if len(prompt.description) > 50 else prompt.description
            )
        
        console.print(table)
        
        # Show summary
        if tag:
            console.print(f"\n[dim]Found {len(prompts)} prompt(s) with tag '{tag}'[/dim]")
        else:
            console.print(f"\n[dim]Total: {len(prompts)} prompt(s)[/dim]")

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
def edit(
    name: str = typer.Argument(..., help="Name of the prompt to edit", autocompletion=complete_prompt_names)
):
    """Edit a prompt template using your preferred editor."""
    storage = PromptStorage()
    config = Config()
    prompt = storage.get_prompt(name)
    
    if not prompt:
        console.print(f"Prompt '{name}' not found", style="red")
        return
    
    # Get editor from environment or config
    editor = os.environ.get('EDITOR') or config.get('editor', 'nano')
    
    # Create a temporary file with the current prompt content
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as tmp_file:
        # Write current prompt content with metadata as comments
        tmp_file.write(f"# Prompt: {prompt.name}\n")
        tmp_file.write(f"# Description: {prompt.description}\n")
        tmp_file.write(f"# Tags: {', '.join(prompt.tags) if prompt.tags else 'None'}\n")
        tmp_file.write(f"# Variables: {', '.join(prompt.variables) if prompt.variables else 'None'}\n")
        tmp_file.write("# Edit the template below (lines starting with # will be ignored)\n")
        tmp_file.write("#" + "="*60 + "\n\n")
        tmp_file.write(prompt.template)
        tmp_path = tmp_file.name
    
    try:
        # Open editor
        console.print(f"Opening '{name}' in {editor}...", style="cyan")
        result = subprocess.run([editor, tmp_path], check=True)
        
        # Read the edited content
        with open(tmp_path, 'r') as f:
            edited_content = f.read()
        
        # Extract the template content (skip comment lines)
        lines = edited_content.split('\n')
        template_lines = []
        for line in lines:
            if not line.strip().startswith('#'):
                template_lines.append(line)
        
        new_template = '\n'.join(template_lines).strip()
        
        if new_template == prompt.template:
            console.print("No changes made to the prompt", style="yellow")
            return
        
        # Update the prompt with new template
        updated_prompt = PromptTemplate(
            name=prompt.name,
            template=new_template,
            description=prompt.description,
            tags=prompt.tags,
            variables=PromptTemplate.extract_variables(new_template),
            created_at=prompt.created_at
        )
        
        # Determine format from existing file
        format = "yaml"
        for ext in ["yaml", "json"]:
            if storage._get_prompt_path(name, ext).exists():
                format = ext
                break
        
        success = storage.save_prompt(updated_prompt, format)
        if success:
            console.print(f"Prompt '{name}' updated successfully!", style="green")
            
            # Show what changed
            old_vars = set(prompt.variables)
            new_vars = set(updated_prompt.variables)
            if old_vars != new_vars:
                added = new_vars - old_vars
                removed = old_vars - new_vars
                if added:
                    console.print(f"Added variables: {', '.join(added)}", style="green")
                if removed:
                    console.print(f"Removed variables: {', '.join(removed)}", style="yellow")
        else:
            console.print(f"Failed to update prompt '{name}'", style="red")
            
    except subprocess.CalledProcessError:
        console.print(f"Editor '{editor}' exited with error", style="red")
    except FileNotFoundError:
        console.print(f"Editor '{editor}' not found. Set a different editor:", style="red")
        console.print(f"  export EDITOR=nano", style="yellow")
        console.print(f"  aix config editor vim", style="yellow")
    except KeyboardInterrupt:
        console.print("\nEdit cancelled", style="yellow")
    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

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
    enable_commands: bool = typer.Option(False, "--enable-commands", help="Enable command execution in templates"),
    auto_upgrade: bool = typer.Option(False, "--auto-upgrade", help="Auto-upgrade aix before execution")
):
    """Run a prompt with parameter substitution and optional API execution."""
    storage = PromptStorage()
    config = Config()
    prompt = storage.get_prompt(name)
    
    if not prompt:
        console.print(f"Prompt '{name}' not found", style="red")
        return
    
    # Handle auto-upgrade
    config_auto_upgrade = config.get("auto_upgrade", False)
    if auto_upgrade or config_auto_upgrade:
        console.print("Auto-upgrading aix...", style="cyan")
        success = perform_upgrade()
        if not success:
            console.print("Upgrade failed, continuing with current version...", style="yellow")
    
    # Parse parameters
    param_dict = {}
    if params:
        for param in params:
            if "=" not in param:
                console.print(f"Invalid parameter format: {param}. Use key=value", style="red")
                return
            key, value = param.split("=", 1)
            param_dict[key.strip()] = value.strip()
    
    # Check for missing variables and prompt interactively
    missing_vars = set(prompt.variables) - set(param_dict.keys())
    if missing_vars:
        console.print(f"Missing variables: {', '.join(missing_vars)}", style="yellow")
        
        # Interactive prompting for missing variables
        if not dry_run:  # Only prompt in interactive mode, not for dry runs
            console.print("Please provide values for missing variables:", style="cyan")
            for var in sorted(missing_vars):
                try:
                    value = typer.prompt(f"  {var}")
                    param_dict[var] = value
                except typer.Abort:
                    console.print("\nOperation cancelled", style="yellow")
                    return
        else:
            console.print(f"Use --param {list(missing_vars)[0]}=value to provide missing variables", style="red")
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
        console.print(f"💡 Set it up with: aix api-key {selected_provider}", style="yellow")
        
        # Interactive API key setup
        if typer.confirm("Would you like to set it up now?"):
            if setup_api_key(selected_provider):
                # Reload config to get the new API key
                config = Config()
                api_key = config.get_api_key(selected_provider)
                console.print(f"✅ API key for {selected_provider} configured successfully!", style="green")
            else:
                console.print("❌ Failed to set up API key", style="red")
                return
        else:
            console.print("Operation cancelled. You can set up API keys later with:", style="yellow")
            console.print(f"  aix api-key {selected_provider}", style="dim")
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
    list_all: bool = typer.Option(False, "--list", "-l", help="List all configuration"),
    get: Optional[str] = typer.Option(None, "--get", "-g", help="Get configuration value", autocompletion=complete_config_keys),
    set_pair: Optional[str] = typer.Option(None, "--set", help="Set configuration key=value"),
    reset: bool = typer.Option(False, "--reset", help="Reset configuration to defaults")
):
    """Manage configuration settings."""
    config_manager = Config()
    
    # Handle reset option
    if reset:
        if typer.confirm("Are you sure you want to reset all configuration to defaults? This will remove all settings including API keys."):
            success = config_manager.reset()
            if success:
                console.print("Configuration reset to defaults", style="green")
            else:
                console.print("Failed to reset configuration", style="red")
        else:
            console.print("Reset cancelled", style="yellow")
        return
    
    # Handle --get option
    if get:
        val = config_manager.get(get)
        if val is not None:
            # Mask API keys for security
            if "api_key" in get.lower() and isinstance(val, str):
                if len(val) > 8:
                    val = f"{val[:4]}{'*' * (len(val) - 8)}{val[-4:]}"
                else:
                    val = "*" * len(val)
            console.print(f"[cyan]{get}[/cyan]: {val}")
        else:
            console.print(f"Configuration key '{get}' not found", style="red")
        return
    
    # Handle --set option
    if set_pair:
        if "=" not in set_pair:
            console.print("--set requires key=value format. Example: aix config --set editor=vim", style="red")
            return
        set_key, set_value = set_pair.split("=", 1)
        config_manager.set(set_key.strip(), set_value.strip())
        console.print(f"Set [cyan]{set_key.strip()}[/cyan] = [magenta]{set_value.strip()}[/magenta]", style="green")
        return
    
    # Handle list or traditional positional arguments
    if list_all or (not key and not value and not get and not set_pair):
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
    
    # Handle traditional positional arguments (backward compatibility)
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
        console.print(f"Set [cyan]{key}[/cyan] = [magenta]{value}[/magenta]", style="green")
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

def perform_upgrade():
    """Perform the upgrade process programmatically.
    
    Returns:
        bool: True if upgrade succeeded, False otherwise
    """
    console = Console()
    
    try:
        import subprocess
        import shutil
        
        # Find system uv binary
        uv_path = shutil.which("uv")
        if not uv_path:
            console.print("uv not found in PATH. Please install uv first.", style="red")
            console.print("Install uv: curl -Ls https://astral.sh/uv/install.sh | sh", style="yellow")
            return False
        
        console.print("Upgrading aix via uv tool...", style="cyan")
        result = subprocess.run([
            uv_path, "tool", "install", "aix", 
            "--from", "git+https://github.com/bhadzhiev/prompt.git", "--force"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            from . import __version__
            console.print(f"Successfully upgraded aix to version {__version__}", style="green")
            return True
        else:
            console.print("Upgrade failed", style="red")
            console.print("Error:", result.stderr, style="red")
            return False
            
    except Exception as e:
        console.print(f"Upgrade failed: {e}", style="red")
        return False

@app.command()
def upgrade():
    """Upgrade aix to the latest version from GitHub."""
    success = perform_upgrade()
    if success:
        from . import __version__
        console.print(f"Now running aix version {__version__}", style="blue")

if __name__ == "__main__":
    app()