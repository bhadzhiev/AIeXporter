# Publishing Guide

## How to Publish aix to GitHub

### 1. **Set up remote repository**
```bash
git remote add publish https://github.com/bhadzhiev/AIeXporter.git
```

### 2. **Push code to GitHub**
```bash
git push -u publish master:main
```

### 3. **Create GitHub release**
```bash
# Tags are now created automatically by the pre-push hook
# But you need to create GitHub releases manually:

# Create a release from an existing tag
gh release create v0.3.1 --title "Release v0.3.1" --notes "Release notes here"

# Or create a release with auto-generated notes
gh release create v0.3.1 --generate-notes

# Mark a release as latest
gh release edit v0.3.1 --latest
```

### 4. Install from GitHub (for users)
```bash
# Users can install directly from GitHub
uv tool install aix --from git+https://github.com/bhadzhiev/AIeXporter.git

# Or via pip
pip install git+https://github.com/bhadzhiev/AIeXporter.git
```

## Manual Push Commands

If you have authentication issues, use these commands:

```bash
# Using GitHub CLI (recommended)
gh auth login
git push https://$(gh auth token)@github.com/bhadzhiev/AIeXporter.git master:main

# Using personal access token
git push https://YOUR_TOKEN@github.com/bhadzhiev/AIeXporter.git master:main
```

## Ready for Distribution

Your repository is now configured with:
- UV-compatible `pyproject.toml`
- GitHub Actions for automated builds
- PyPI publishing workflow
- Cross-platform executable building
- CLI command (`aix`)

## User Installation

Once published, users can install with:

```bash
# Via UV (recommended)
uv tool install aix

# Via pip
pip install aix

# From GitHub directly
uv tool install aix --from git+https://github.com/bhadzhiev/AIeXporter.git
```

## Automated Release Process

### Version Bumping (Automatic)
1. **Commit with conventional commits**: `feat:`, `fix:`, `chore:`, etc.
2. **Push to main**: Pre-push hook automatically bumps version and updates changelog
3. **Tags created**: Git tags are automatically created and pushed

### GitHub Releases (Automatic)
1. **Auto-created**: Pre-push hook now creates GitHub releases automatically
2. **Auto-generated notes**: Uses GitHub's auto-generated release notes
3. **Fallback option**: Manual creation if GitHub CLI is not available or authenticated

### Publishing Workflow
```bash
# 1. Make changes and commit with conventional commits
git commit -m "feat: add new awesome feature"

# 2. Push (triggers automatic version bump)
git push

# 3. GitHub release is created automatically!
# (No manual step needed)

# 4. Optionally: publish to PyPI (if configured)
```

## Next Steps

1. **Automated workflow working** ✅ Pre-push hook handles version bumping
2. **GitHub releases created** ✅ All versions now have releases 
3. **Create PyPI account** at https://pypi.org (optional)
4. **Set up GitHub secrets** for PyPI publishing (optional)
5. **Share installation instructions** with users