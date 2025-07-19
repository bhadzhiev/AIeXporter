#!/bin/bash

# Auto-commit script that generates commit message with AI

set -e

echo "🤖 Generating commit message..."

# Create a temporary prompt file
cat > /tmp/commit_prompt.txt << 'EOF'
You are an expert Git commit message writer. Output ONLY a conventional commit message.

RULES:
- Use imperative mood ("Add" not "Added")
- Max 72 chars, lowercase after colon  
- Types: feat/fix/chore/refactor/docs/test
- NO quotes, markdown, explanations
- Output ONLY the commit message, nothing else

ANALYSIS:
EOF

# Add context to the prompt
echo "Files changed: $(git diff --cached --name-only | wc -l | tr -d ' ')" >> /tmp/commit_prompt.txt
echo "" >> /tmp/commit_prompt.txt
echo "File summary:" >> /tmp/commit_prompt.txt
git diff --cached --name-only | head -10 >> /tmp/commit_prompt.txt
echo "" >> /tmp/commit_prompt.txt
echo "Change summary:" >> /tmp/commit_prompt.txt
git diff --cached --stat | head -10 >> /tmp/commit_prompt.txt

# Generate commit message using the clean template
echo "📝 Calling AI to generate message..."
COMMIT_MSG=$(aix run commit-msg-clean --enable-commands 2>/dev/null | grep -E '^(feat|fix|chore|refactor|docs|test|style|perf|build|ci):|^[a-z]+:' | head -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')

# Fallback: if no conventional commit found, try to extract last meaningful line
if [ -z "$COMMIT_MSG" ]; then
    FULL_OUTPUT=$(aix run commit-msg-clean --enable-commands 2>&1)
    COMMIT_MSG=$(echo "$FULL_OUTPUT" | grep -v '╰\|╭\|│\|Tip:\|Generated Prompt\|Executed commands' | grep -v '^[[:space:]]*$' | tail -1 | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
fi

# Clean up temp file
rm -f /tmp/commit_prompt.txt

if [ -z "$COMMIT_MSG" ]; then
    echo "❌ Failed to generate commit message"
    exit 1
fi

echo "✨ Generated message: $COMMIT_MSG"
echo ""
echo "🚀 Committing..."

# Commit with the generated message
if git commit -m "$COMMIT_MSG"; then
    echo "✅ Successfully committed with message: $COMMIT_MSG"
else
    echo "❌ Commit failed"
    exit 1
fi