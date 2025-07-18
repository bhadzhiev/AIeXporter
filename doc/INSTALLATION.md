# Installation Guide

## The Easy Way (Recommended)

```bash
# If you have uv (you should)
uv tool install aix --from git+https://github.com/bhadzhiev/prompt.git

# If you're still living in pip land
pip install -e .
```

## The "I Like to Live Dangerously" Way

```bash
# Clone the repo
git clone https://github.com/bhadzhiev/prompt.git
cd prompt

# Install dependencies
uv sync  # or pip install -e .

# Run directly
python main.py --help
```

## System Requirements

- Python 3.8+ (we're not savages)
- uv (recommended) or pip
- Internet connection (for API calls)
- A sense of humor (for error messages)

## Post-Installation

Run `aix --help` to verify installation. If you see help text, you're golden. If not, try turning it off and on again.

## Troubleshooting

- **"uv not found"**: Install uv via `curl -Ls https://astral.sh/uv/install.sh | sh`
- **"command not found"**: Try `python -m promptconsole.cli --help`
- **"it doesn't work"**: Have you tried asking nicely?