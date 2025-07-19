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
from .collection import CollectionManager, Collection
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
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tag", autocompletion=complete_tags),
    all_templates: bool = typer.Option(False, "--all", "-a", help="Show all templates (ignore current collection)")
):
    """List all saved prompts."""
    storage = PromptStorage()
    manager = CollectionManager()
    
    # Check if a collection is loaded and filter templates accordingly
    current_collection = manager.collection_storage.get_current_collection()
    
    if current_collection and not all_templates:
        # Show only templates from the current collection
        prompts = manager.list_current_collection_templates()
        collection_info = f" (from collection: {current_collection})"
    else:
        # Show all templates
        prompts = storage.list_prompts()
        collection_info = ""
    
    # Filter by tag if specified
    if tag:
        prompts = [p for p in prompts if tag in p.tags]
        if not prompts:
            console.print(f"No prompts found with tag '{tag}'{collection_info}", style="yellow")
            return
    
    if not prompts:
        if current_collection and not all_templates:
            console.print(f"No prompts found in collection '{current_collection}'", style="yellow")
            console.print("Use 'aix collection-add <template>' to add templates", style="cyan")
        else:
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
        if current_collection and not all_templates:
            title += f" (Collection: {current_collection})"
        elif all_templates and current_collection:
            title += " (All Templates)"
        
        if tag:
            title += f" - filtered by tag: {tag}"
        
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
        
        # Show summary with collection context
        summary = f"[dim]Total: {len(prompts)} prompt(s)"
        if current_collection and not all_templates:
            summary += f" in collection '{current_collection}'"
        elif tag:
            summary += f" with tag '{tag}'"
        summary += "[/dim]"
        
        console.print(f"\n{summary}")
        
        # Show collection status hint
        if current_collection:
            if not all_templates:
                console.print(f"[dim]Tip: Use --all to see all templates or 'aix collection-unload' to work with all templates[/dim]")
            else:
                console.print(f"[dim]Current collection: '{current_collection}' is loaded[/dim]")

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
    manager = CollectionManager()
    
    # Check if a collection is loaded and if the prompt is in it
    current_collection = manager.collection_storage.get_current_collection()
    
    prompt = storage.get_prompt(name)
    
    if not prompt:
        console.print(f"Prompt '{name}' not found", style="red")
        if current_collection:
            console.print(f"Tip: Currently in collection '{current_collection}'. Use 'aix list --all' to see all templates", style="cyan")
        return
    
    # If a collection is loaded, check if the prompt is in it
    if current_collection:
        collection = manager.collection_storage.get_collection(current_collection)
        if collection and not collection.has_template(name):
            console.print(f"Warning: Prompt '{name}' is not in the current collection '{current_collection}'", style="yellow")
            console.print(f"Tip: Add it with: aix collection-add {name}", style="cyan")
            console.print(f"Tip: Or unload collection with: aix collection-unload", style="cyan")
            # Still allow execution, just warn the user
    
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
            if missing_vars:
                first_var = next(iter(missing_vars))
                console.print(f"Use --param {first_var}=value to provide missing variables", style="red")
            return
    
    # Generate the final prompt
    if enable_commands:
        # Execute commands in the template
        executor = CommandExecutor()
        generated_prompt, command_outputs = prompt.render(param_dict, execute_commands=True, command_executor=executor)
        
        if command_outputs:
            console.print("Executed commands:", style="blue")
            for cmd_placeholder, cmd_output in command_outputs.items():
                console.print(f"  {cmd_placeholder} → {cmd_output[:100]}{'...' if len(cmd_output) > 100 else ''}", style="dim")
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
    
    # Always show the generated prompt before execution
    console.print(Panel(generated_prompt, title="Generated Prompt (before API execution)", expand=False))
    
    if not api_key:
        console.print(f"No API key found for provider '{selected_provider}'", style="red")
        console.print(f"Tip: Set it up with: aix api-key {selected_provider}", style="yellow")
        
        # Interactive API key setup
        if typer.confirm("Would you like to set it up now?"):
            if setup_api_key(selected_provider):
                # Reload config to get the new API key
                config = Config()
                api_key = config.get_api_key(selected_provider)
                console.print(f"API key for {selected_provider} configured successfully!", style="green")
            else:
                console.print("Failed to set up API key", style="red")
                return
        else:
            console.print("Operation cancelled. You can set up API keys later with:", style="yellow")
            console.print(f"  aix api-key {selected_provider}", style="dim")
            return
    
    try:
        # Handle custom providers
        custom_config = None
        if selected_provider.startswith("custom:"):
            provider_name = selected_provider[7:]  # Remove "custom:" prefix
            custom_config = config.get_custom_provider(provider_name)
            if not custom_config:
                console.print(f"Custom provider '{provider_name}' not found", style="red")
                console.print("Available custom providers:", style="yellow")
                for name in config.get_custom_providers().keys():
                    console.print(f"  custom:{name}", style="dim")
                return
            selected_provider = "custom"
        
        client = get_client(selected_provider, api_key, custom_config)
        
        # Get default model
        if selected_provider == "custom" and custom_config:
            selected_model = model or custom_config.get("default_model", "")
        else:
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
            with console.status("Generating response..."):
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
            console.print("No configuration found", style="yellow")
            return
        
        table = Table(title="Configuration")
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
        
        # Get current version
        from . import __version__ as current_version
        
        # Always attempt upgrade to get the latest version from GitHub
        # The version comparison was flawed - just upgrade and let uv handle it
        
        console.print("Upgrading aix via uv tool...", style="cyan")
        result = subprocess.run([
            uv_path, "tool", "install", "aix", 
            "--from", "git+https://github.com/bhadzhiev/AIeXporter.git", "--force"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            # Get the new version after upgrade
            info_result = subprocess.run([
                uv_path, "tool", "run", "aix", "--version"
            ], capture_output=True, text=True)
            
            if info_result.returncode == 0:
                import re
                version_match = re.search(r'version (\d+\.\d+\.\d+)', info_result.stdout)
                if version_match:
                    new_version = version_match.group(1)
                    console.print(f"Successfully upgraded aix to version {new_version}", style="green")
                else:
                    console.print("Successfully upgraded aix", style="green")
            else:
                console.print("Successfully upgraded aix", style="green")
            return True
        else:
            console.print("Upgrade failed", style="red")
            console.print("Error:", result.stderr, style="red")
            return False
            
    except Exception as e:
        console.print(f"Upgrade failed: {e}", style="red")
        return False

# Collection commands
@app.command("collection-create")
def collection_create(
    name: str = typer.Argument(..., help="Name of the collection to create"),
    description: str = typer.Option("", "--description", "-d", help="Description of the collection"),
    templates: List[str] = typer.Option([], "--template", "-t", help="Template names to add to collection"),
    tags: List[str] = typer.Option([], "--tag", help="Tags for the collection")
):
    """Create a new template collection."""
    console = Console()
    manager = CollectionManager()
    
    # Validate that all specified templates exist
    storage = PromptStorage()
    missing_templates = []
    for template_name in templates:
        if not storage.prompt_exists(template_name):
            missing_templates.append(template_name)
    
    if missing_templates:
        console.print(f"Error: Templates not found: {', '.join(missing_templates)}", style="red")
        console.print("Use 'aix list' to see available templates", style="yellow")
        return
    
    if manager.collection_storage.collection_exists(name):
        console.print(f"Collection '{name}' already exists", style="red")
        return
    
    success = manager.create_collection(name, description, templates, tags)
    if success:
        console.print(f"Created collection '{name}' with {len(templates)} templates", style="green")
        if description:
            console.print(f"Description: {description}")
        if tags:
            console.print(f"Tags: {', '.join(tags)}")
    else:
        console.print(f"Failed to create collection '{name}'", style="red")

@app.command("collection-list")
def collection_list():
    """List all available collections."""
    console = Console()
    manager = CollectionManager()
    
    collections = manager.collection_storage.list_collections()
    current_collection = manager.collection_storage.get_current_collection()
    
    if not collections:
        console.print("No collections found", style="yellow")
        console.print("Create a collection with: aix collection-create <name>", style="cyan")
        return
    
    table = Table(title="Collections")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Templates", style="green", justify="center")
    table.add_column("Tags", style="blue")
    table.add_column("Status", style="magenta")
    
    for collection in collections:
        status = "Current" if collection.name == current_collection else ""
        tags_str = ", ".join(collection.tags) if collection.tags else ""
        
        table.add_row(
            collection.name,
            collection.description[:50] + ("..." if len(collection.description) > 50 else ""),
            str(len(collection.templates)),
            tags_str,
            status
        )
    
    console.print(table)
    
    if current_collection:
        console.print(f"\nCurrently loaded: {current_collection}", style="green")
    else:
        console.print("\nNo collection currently loaded", style="yellow")
        console.print("Load a collection with: aix collection-load <name>", style="cyan")

@app.command("collection-load")
def collection_load(
    name: str = typer.Argument(..., help="Name of the collection to load"),
):
    """Load a collection as the current working collection."""
    console = Console()
    manager = CollectionManager()
    
    if not manager.collection_storage.collection_exists(name):
        console.print(f"Collection '{name}' not found", style="red")
        console.print("Use 'aix collection-list' to see available collections", style="cyan")
        return
    
    success = manager.load_collection(name)
    if success:
        collection = manager.collection_storage.get_collection(name)
        console.print(f"Loaded collection '{name}'", style="green")
        
        if collection.description:
            console.print(f"Description: {collection.description}")
        
        console.print(f"Templates: {len(collection.templates)}")
        
        # Show template validation
        validation = manager.collection_storage.validate_collection_templates(name, manager.prompt_storage)
        if validation["missing"]:
            console.print(f"Warning: Missing templates: {', '.join(validation['missing'])}", style="yellow")
        
        console.print("\nUse 'aix list' to see templates in this collection", style="cyan")
    else:
        console.print(f"Failed to load collection '{name}'", style="red")

@app.command("collection-unload")
def collection_unload():
    """Unload the current collection."""
    console = Console()
    manager = CollectionManager()
    
    current = manager.collection_storage.get_current_collection()
    if not current:
        console.print("No collection currently loaded", style="yellow")
        return
    
    success = manager.collection_storage.clear_current_collection()
    if success:
        console.print(f"Unloaded collection '{current}'", style="green")
        console.print("Now working with all templates", style="cyan")
    else:
        console.print("Failed to unload collection", style="red")

@app.command("collection-add")
def collection_add(
    template_name: str = typer.Argument(..., help="Name of the template to add"),
):
    """Add a template to the current collection."""
    console = Console()
    manager = CollectionManager()
    
    current = manager.collection_storage.get_current_collection()
    if not current:
        console.print("No collection currently loaded", style="red")
        console.print("Load a collection with: aix collection-load <name>", style="cyan")
        return
    
    if not manager.prompt_storage.prompt_exists(template_name):
        console.print(f"Template '{template_name}' not found", style="red")
        console.print("Use 'aix list --all' to see all available templates", style="cyan")
        return
    
    success = manager.add_template_to_current_collection(template_name)
    if success:
        console.print(f"Added template '{template_name}' to collection '{current}'", style="green")
    else:
        console.print(f"Template '{template_name}' is already in collection '{current}'", style="yellow")

@app.command("collection-remove")
def collection_remove(
    template_name: str = typer.Argument(..., help="Name of the template to remove"),
):
    """Remove a template from the current collection."""
    console = Console()
    manager = CollectionManager()
    
    current = manager.collection_storage.get_current_collection()
    if not current:
        console.print("No collection currently loaded", style="red")
        console.print("Load a collection with: aix collection-load <name>", style="cyan")
        return
    
    success = manager.remove_template_from_current_collection(template_name)
    if success:
        console.print(f"Removed template '{template_name}' from collection '{current}'", style="green")
    else:
        console.print(f"Template '{template_name}' not found in collection '{current}'", style="yellow")

@app.command("collection-info")
def collection_info(
    name: Optional[str] = typer.Argument(None, help="Collection name (defaults to current)")
):
    """Show detailed information about a collection."""
    console = Console()
    manager = CollectionManager()
    
    if not name:
        name = manager.collection_storage.get_current_collection()
        if not name:
            console.print("No collection currently loaded and no name specified", style="red")
            return
    
    collection = manager.collection_storage.get_collection(name)
    if not collection:
        console.print(f"Collection '{name}' not found", style="red")
        return
    
    # Create info panel
    info_text = f"[bold cyan]{collection.name}[/bold cyan]\n"
    if collection.description:
        info_text += f"Description: {collection.description}\n"
    if collection.tags:
        info_text += f"Tags: {', '.join(collection.tags)}\n"
    if collection.author:
        info_text += f"Author: {collection.author}\n"
    if collection.created_at:
        info_text += f"Created: {collection.created_at[:10]}\n"
    if collection.updated_at:
        info_text += f"Updated: {collection.updated_at[:10]}\n"
    
    console.print(Panel(info_text, title="Collection Info"))
    
    # Show templates
    if collection.templates:
        validation = manager.collection_storage.validate_collection_templates(name, manager.prompt_storage)
        
        table = Table(title=f"Templates in '{name}'")
        table.add_column("Template", style="cyan")
        table.add_column("Status", style="green")
        
        for template_name in collection.templates:
            status = "Available" if template_name in validation["valid"] else "Missing"
            table.add_row(template_name, status)
        
        console.print(table)
        
        if validation["missing"]:
            console.print(f"\nWarning: {len(validation['missing'])} missing templates", style="yellow")
    else:
        console.print("No templates in this collection", style="yellow")

@app.command("collection-delete")
def collection_delete(
    name: str = typer.Argument(..., help="Name of the collection to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """Delete a collection."""
    console = Console()
    manager = CollectionManager()
    
    if not manager.collection_storage.collection_exists(name):
        console.print(f"Collection '{name}' not found", style="red")
        return
    
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete collection '{name}'?")
        if not confirm:
            console.print("Cancelled", style="yellow")
            return
    
    success = manager.collection_storage.delete_collection(name)
    if success:
        console.print(f"Deleted collection '{name}'", style="green")
    else:
        console.print(f"Failed to delete collection '{name}'", style="red")

@app.command("collection-export")
def collection_export(
    name: str = typer.Argument(..., help="Name of the collection to export"),
    output: Path = typer.Option(".", "--output", "-o", help="Output directory or file path"),
    include_templates: bool = typer.Option(True, "--templates/--no-templates", help="Include templates in export"),
    format: str = typer.Option("yaml", "--format", "-f", help="Export format (yaml or json)")
):
    """Export a collection to a file or bundle."""
    console = Console()
    manager = CollectionManager()
    
    if not manager.collection_storage.collection_exists(name):
        console.print(f"Collection '{name}' not found", style="red")
        return
    
    output_path = Path(output)
    
    try:
        success = manager.export_collection(name, output_path, include_templates, format)
        if success:
            if include_templates:
                bundle_file = output_path / f"{name}-bundle.tar.gz"
                console.print(f"Collection '{name}' exported as bundle to: {bundle_file}", style="green")
                console.print("Bundle includes collection metadata and all templates", style="dim")
            else:
                collection_file = output_path / f"{name}.{format}"
                console.print(f"Collection '{name}' metadata exported to: {collection_file}", style="green")
                console.print("Note: Templates not included (use --templates to include)", style="yellow")
        else:
            console.print(f"Failed to export collection '{name}'", style="red")
    except Exception as e:
        console.print(f"Export failed: {e}", style="red")

@app.command("collection-import")
def collection_import(
    path: Path = typer.Argument(..., help="Path to collection file or bundle to import"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing collection and templates")
):
    """Import a collection from a file or bundle."""
    console = Console()
    manager = CollectionManager()
    
    import_path = Path(path)
    if not import_path.exists():
        console.print(f"Import file not found: {import_path}", style="red")
        return
    
    console.print(f"Importing collection from: {import_path}", style="cyan")
    
    try:
        result = manager.import_collection(import_path, overwrite)
        
        if result["success"]:
            console.print(f"Successfully imported collection '{result['collection_name']}'", style="green")
            
            if result["imported_templates"]:
                console.print(f"Imported {len(result['imported_templates'])} templates:", style="green")
                for template in result["imported_templates"]:
                    console.print(f"  - {template}")
            
            if result["skipped_templates"]:
                console.print(f"Skipped {len(result['skipped_templates'])} existing templates:", style="yellow")
                for template in result["skipped_templates"]:
                    console.print(f"  - {template}")
                console.print("Use --overwrite to replace existing templates", style="dim")
            
            console.print(f"\nUse 'aix collection-load {result['collection_name']}' to work with this collection", style="cyan")
        else:
            console.print("Import failed:", style="red")
            for error in result["errors"]:
                console.print(f"  - {error}", style="red")
                
    except Exception as e:
        console.print(f"Import failed: {e}", style="red")

# Provider management commands
provider_app = typer.Typer(help="Manage custom API providers")

@provider_app.command("add")
def provider_add(
    name: str = typer.Argument(..., help="Name of the custom provider"),
    base_url: str = typer.Argument(..., help="Base URL for the API endpoint"),
    default_model: Optional[str] = typer.Option(None, "--model", help="Default model for this provider"),
    header: Optional[List[str]] = typer.Option(None, "--header", help="Custom headers in key:value format"),
    auth_type: str = typer.Option("bearer", "--auth-type", help="Authentication type (bearer, api-key)")
):
    """Add a custom API provider."""
    config = Config()
    
    # Parse headers
    headers = {}
    if header:
        for h in header:
            if ":" not in h:
                console.print(f"Invalid header format: {h}. Use key:value format", style="red")
                return
            key, value = h.split(":", 1)
            headers[key.strip()] = value.strip()
    
    success = config.add_custom_provider(
        name=name,
        base_url=base_url,
        default_model=default_model,
        headers=headers,
        auth_type=auth_type
    )
    
    if success:
        console.print(f"Custom provider '{name}' added successfully!", style="green")
        console.print(f"Usage: aix run <prompt> --provider custom:{name}", style="cyan")
    else:
        console.print(f"Failed to add custom provider '{name}'", style="red")

@provider_app.command("list")
def provider_list():
    """List all custom providers."""
    config = Config()
    custom_providers = config.get_custom_providers()
    
    if not custom_providers:
        console.print("No custom providers configured", style="yellow")
        console.print("Add one with: aix provider add <name> <base-url>", style="dim")
        return
    
    table = Table(title="Custom Providers")
    table.add_column("Name", style="cyan")
    table.add_column("Base URL", style="green")
    table.add_column("Default Model", style="yellow")
    table.add_column("Auth Type", style="blue")
    
    for name, config_data in custom_providers.items():
        table.add_row(
            name,
            config_data.get("base_url", ""),
            config_data.get("default_model", "Not set"),
            config_data.get("auth_type", "bearer")
        )
    
    console.print(table)

@provider_app.command("remove")
def provider_remove(
    name: str = typer.Argument(..., help="Name of the custom provider to remove")
):
    """Remove a custom provider."""
    config = Config()
    
    if config.remove_custom_provider(name):
        console.print(f"Custom provider '{name}' removed successfully!", style="green")
    else:
        console.print(f"Custom provider '{name}' not found", style="red")

@provider_app.command("info")
def provider_info(
    name: str = typer.Argument(..., help="Name of the custom provider")
):
    """Show detailed information about a custom provider."""
    config = Config()
    provider_config = config.get_custom_provider(name)
    
    if not provider_config:
        console.print(f"Custom provider '{name}' not found", style="red")
        return
    
    console.print(f"[bold cyan]Custom Provider: {name}[/bold cyan]")
    console.print(f"Base URL: {provider_config.get('base_url', 'Not set')}")
    console.print(f"Default Model: {provider_config.get('default_model', 'Not set')}")
    console.print(f"Auth Type: {provider_config.get('auth_type', 'bearer')}")
    
    headers = provider_config.get('headers', {})
    if headers:
        console.print("Custom Headers:")
        for key, value in headers.items():
            console.print(f"  {key}: {value}")
    else:
        console.print("Custom Headers: None")

app.add_typer(provider_app, name="provider")

@app.command()
def upgrade():
    """Upgrade aix to the latest version from GitHub."""
    success = perform_upgrade()
    # Only show "Now running" message if we actually performed an upgrade
    # The perform_upgrade function will handle the "already up to date" message

if __name__ == "__main__":
    app()