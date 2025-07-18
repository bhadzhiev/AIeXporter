# 🚀 Publishing Guide

## 📦 How to Publish PromptConsole to GitHub

### 1. **Set up remote repository**
```bash
git remote add publish https://github.com/bhadzhiev/prompt.git
```

### 2. **Push code to GitHub**
```bash
git push -u publish master:main
```

### 3. **Create GitHub release**
```bash
# Tag the release
git tag v0.1.0
git push publish v0.1.0
```

### 4. **Install from GitHub (for users)**
```bash
# Users can install directly from GitHub
uv tool install promptconsole --git https://github.com/bhadzhiev/prompt.git

# Or via pip
pip install git+https://github.com/bhadzhiev/prompt.git
```

## 🔧 **Manual Push Commands**

If you have authentication issues, use these commands:

```bash
# Using GitHub CLI (recommended)
gh auth login
git push https://$(gh auth token)@github.com/bhadzhiev/prompt.git master:main

# Using personal access token
git push https://YOUR_TOKEN@github.com/bhadzhiev/prompt.git master:main
```

## 🎯 **Ready for Distribution**

Your repository is now configured with:
- ✅ UV-compatible `pyproject.toml`
- ✅ GitHub Actions for automated builds
- ✅ PyPI publishing workflow
- ✅ Cross-platform executable building
- ✅ CLI commands (`promptconsole` and `pc`)

## 📋 **User Installation**

Once published, users can install with:

```bash
# Via UV (recommended)
uv tool install promptconsole

# Via pip
pip install promptconsole

# From GitHub directly
uv tool install promptconsole --git https://github.com/bhadzhiev/prompt.git
```

## 🚀 **Next Steps**

1. **Push to GitHub** using the commands above
2. **Create PyPI account** at https://pypi.org
3. **Set up GitHub secrets** for PyPI publishing
4. **Create release** from GitHub interface
5. **Share installation instructions** with users