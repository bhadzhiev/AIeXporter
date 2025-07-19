import typer
from rich.console import Console
from rich.prompt import Prompt
from .config import Config

console = Console()

def setup_api_key(provider: str) -> bool:
    """Interactively set up an API key for a provider."""
    config = Config()
    
    provider_info = {
        "openrouter": {
            "name": "OpenRouter",
            "signup_url": "https://openrouter.ai",
            "description": "Access to multiple AI models through one API"
        },
        "openai": {
            "name": "OpenAI",
            "signup_url": "https://platform.openai.com",
            "description": "GPT models from OpenAI"
        },
        "anthropic": {
            "name": "Anthropic",
            "signup_url": "https://console.anthropic.com",
            "description": "Claude models from Anthropic"
        }
    }
    
    if provider not in provider_info:
        console.print(f"❌ Unsupported provider: {provider}", style="red")
        return False
    
    info = provider_info[provider]
    
    console.print(f"\n🔑 Setting up {info['name']} API Key", style="bold cyan")
    console.print(f"📝 {info['description']}")
    console.print(f"🌐 Sign up at: {info['signup_url']}")
    
    # Check if key already exists
    existing_key = config.get_api_key(provider)
    if existing_key:
        console.print(f"\n⚠️  API key for {provider} already exists", style="yellow")
        if not typer.confirm("Do you want to replace it?"):
            return False
    
    # Get the API key
    api_key = Prompt.ask(f"\nEnter your {info['name']} API key", password=True)
    
    if not api_key.strip():
        console.print("❌ API key cannot be empty", style="red")
        return False
    
    # Save the API key
    success = config.set_api_key(provider, api_key.strip())
    
    if success:
        console.print(f"✅ {info['name']} API key saved successfully!", style="green")
        console.print(f"💡 Test it with: python main.py run your-prompt --execute --provider {provider}", style="dim")
        return True
    else:
        console.print(f"❌ Failed to save API key for {provider}", style="red")
        return False

