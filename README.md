# aix

> *Your AI butler that lives in the terminal and doesn't judge your code*

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![AI](https://img.shields.io/badge/Powered%20by-AI%20(Obviously)-ff69b4.svg)](https://en.wikipedia.org/wiki/Artificial_intelligence)

## What is this sorcery?

aix is like having a really smart intern who lives in your terminal and can:
- **Read your mind** (via prompts)
- **Execute your commands** (safely!)
- **Talk to AI gods** (OpenAI, Anthropic, OpenRouter)
- **Never asks for coffee breaks** (because it's code)

## Why should I care?

Because typing the same prompts into ChatGPT over and over is so 2023. Now you can:

```bash
# Instead of copy-pasting into a browser...
aix run code-review --param code="def add(a,b): return a+b" --execute

# Instead of manually writing commit messages...
aix run commit-msg --enable-commands --execute

# Instead of explaining your code to rubber ducks...
aix run explain-code --param file="main.py" --execute
```

## 🎯 Quick Start (a.k.a. "I have 5 minutes")

### Step 1: Install (Choose your fighter)

```bash
# Option A: The Cool Kid Way (uv)
uv tool install aix --from git+https://github.com/bhadzhiev/prompt.git

# Option B: The "I still use pip" way
pip install git+https://github.com/bhadzhiev/prompt.git

# Option C: The "I like to suffer" way
# (clone, install deps, etc... see [Installation Guide](doc/INSTALLATION.md))
```

### Step 2: Get an API Key (a.k.a. "Pay the AI tax")

```bash
# OpenRouter = 100+ models, free tier available
aix api-key openrouter

# OpenAI = Premium experience, costs money
aix api-key openai

# Anthropic = Claude, also costs money
aix api-key anthropic
```

### Step 3: Actually use it

```bash
# Create a prompt template
aix create roast "Roast this {language} code mercilessly:\n{code}"

# Run it (dry run first because we're cowards)
aix run roast --param language=python --param code="print('hello world')" --dry-run

# Run it for real (brace yourself)
aix run roast --param language=python --param code="print('hello world')" --execute
```

## Features that will make you go "Ooooh"

| Feature | Description | Why it's cool |
|---------|-------------|---------------|
| **🎪 Dynamic Templates** | `{variables}` + `$(commands)` | Your prompts can now read your system |
| **🤖 Multi-AI Support** | OpenRouter, OpenAI, Anthropic | When one AI is down, use another |
| **🛡️ Safety First** | Allowlisted commands only | No `rm -rf /` accidents |
| **🔄 Auto-upgrade** | Self-updating tool | Future-you will thank present-you |
| **📁 File Storage** | YAML/JSON prompts | Git-friendly templates |
| **🎯 Auto-complete** | Tab completion everywhere | Because typing is hard |

## Real-world examples (a.k.a. "Show me the money")

### The "I'm too lazy to write commit messages" prompt

```bash
aix create commit "Write a commit message:\n\nChanges:\n$(git diff --staged)\n\nBe concise, follow conventional commits."

# Then just run:
aix run commit --enable-commands --execute
```

### The "Explain this mess" prompt

```bash
aix create explain "Explain this {language} code like I'm 5:\n\n{code}\n\nFocus on:\n- What it does\n- Why it might exist\n- Potential improvements"

# Usage:
aix run explain --param language=python --param code="$(cat main.py)" --execute
```

### The "Roast my code" prompt

```bash
aix create roast "Roast this {language} code:\n\n{code}\n\nBe savage but helpful. Include:\n- Style violations\n- Performance issues\n- Why the junior dev who wrote this should feel bad"
```

### The "System status report" prompt

```bash
aix create sys-report "Generate a system status report:\n\n- Host: $(hostname)\n- User: $(whoami)\n- Uptime: $(uptime)\n- Disk: $(df -h /)\n- Memory: $(free -h)\n- Git status: $(git status --porcelain | wc -l) modified files\n\nMake it sound professional but slightly snarky."

# Then:
aix run sys-report --enable-commands --dry-run
```

## Documentation (a.k.a. "The boring but necessary stuff")

We've hidden all the boring details in separate files because READMEs should be fun:

- **[Installation Guide](doc/INSTALLATION.md)** - For when `pip install` isn't working
- **[Usage Guide](doc/USAGE.md)** - For when you want to do more than just `aix --help`
- **[Template Guide](doc/TEMPLATES.md)** - For when you want to become a prompt wizard
- **[API Providers](doc/API_PROVIDERS.md)** - For when you want to know which AI to bribe
- **[Command Reference](doc/COMMANDS.md)** - For when you forget what `aix run --param` does

## 🛠️ Configuration (a.k.a. "Making it yours")

```bash
# Check what you've broken
aix config --list

# Set your favorite AI overlord
aix config --set default_provider openrouter

# Make it always upgrade (because updates are cool)
aix config --set auto_upgrade true

# Set your editor (vim vs emacs wars incoming)
aix config --set editor nano  # or vim, or code, or butterfly
```

## Advanced Usage (a.k.a. "Look mom, I'm a hacker")

### Streaming responses (for instant gratification)
```bash
aix run my-prompt --stream --execute
```

### Custom models (for the connoisseurs)
```bash
aix run my-prompt --provider openai --model gpt-4 --execute
```

### Output to file (because copy-paste is so 2022)
```bash
aix run my-prompt --output genius-idea.txt --execute
```

### Multiple parameters (the more the merrier)
```bash
aix run complex-prompt --param lang=python --param style=pep8 --param complexity=overkill --execute
```

## 🐛 Troubleshooting (a.k.a. "It doesn't work!")

### Common Issues and Solutions

| Problem | Solution |
|---------|----------|
| `aix: command not found` | Try `python -m promptconsole.cli --help` |
| `No API key found` | Run `aix api-key openrouter` |
| `Command not allowed` | Add `--enable-commands` to your run command |
| `Upgrade failed` | Run `uv tool install aix --force --from git+https://github.com/bhadzhiev/prompt.git` |
| `It still doesn't work` | Have you tried turning it off and on again? |

### Getting Help

```bash
# The magic help command
aix --help

# Command-specific help
aix run --help
aix create --help

# If all else fails, there's always Stack Overflow
```

## 🎪 Examples Gallery

### 1. The "I'm a DevOps engineer" prompt
```bash
aix create deployment "Create a deployment script for {app_name}:\n\nApp type: {app_type}\nEnvironment: {environment}\nCurrent branch: $(git branch --show-current)\nLast commit: $(git log -1 --pretty=%s)\n\nInclude:\n- Docker setup\n- Environment variables\n- Health checks\n- Rollback strategy"
```

### 2. The "I need to sound smart in meetings" prompt
```bash
aix create meeting-prep "Prepare talking points for meeting about {topic}:\n\nContext:\n$(git log --oneline -10)\n$(find . -name "*.py" -mtime -7 | head -5)\n\nMake me sound like I know what I'm doing."
```

### 3. The "Generate excuses" prompt
```bash
aix create excuse "Generate a technical excuse for why {feature} is delayed:\n\nCurrent blocker: {blocker}\nTeam size: $(whoami) # it's just me\nDeadline: {deadline}\n\nMake it sound technical but not my fault."
```

## ☕ Buy Me a Coffee

If this tool saves you from writing one more commit message manually, consider buying me a coffee:

**Revolut**: @bozhide29n

*Every coffee helps me write more sarcastic error messages.*

## 🏆 Testimonials

> "I used to spend hours writing commit messages. Now I spend hours debugging why the AI's commit messages don't make sense." - *A satisfied user*

> "It's like having a junior developer who never sleeps and doesn't complain about my code style." - *Tech Lead*

> "The auto-upgrade feature means I never have to manually update tools again. My laziness has reached new heights." - *DevOps Engineer*

## 📝 License

MIT License - do whatever you want, just don't blame me when your AI-generated commit messages confuse your team.

## Contributing

Found a bug? Want to add a feature? Have a better joke for the README?

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Test it (please)
5. Submit a PR

Bonus points if your commit messages are generated by this tool.

---

**Made with ❤️ by someone who got tired of copy-pasting prompts into ChatGPT**

*Now stop reading and go automate something!*