#!/bin/bash

# Create voice dictation command alias
echo "🔗 Setting up voice dictation command alias..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from .env file if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# Get custom alias name from environment or use default
ALIAS_NAME="${DICTATE_ALIAS_NAME:-dictate}"

echo "📝 Creating alias: $ALIAS_NAME"

DICTATE_PATH="$SCRIPT_DIR/dictate.py"
ALIAS_COMMAND="alias $ALIAS_NAME=\"python3 $DICTATE_PATH\""

# Detect shell and add alias
if [[ $SHELL == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
    echo "📝 Adding alias to $SHELL_RC"
elif [[ $SHELL == *"bash"* ]]; then
    SHELL_RC="$HOME/.bashrc"
    echo "📝 Adding alias to $SHELL_RC"
else
    SHELL_RC="$HOME/.profile"
    echo "📝 Adding alias to $SHELL_RC"
fi

# Check if alias already exists
if grep -q "alias $ALIAS_NAME=" "$SHELL_RC" 2>/dev/null; then
    echo "⚠️  '$ALIAS_NAME' alias already exists in $SHELL_RC"
    echo "Updating existing alias..."
    # Remove old alias and add new one
    grep -v "alias $ALIAS_NAME=" "$SHELL_RC" > "${SHELL_RC}.tmp" && mv "${SHELL_RC}.tmp" "$SHELL_RC"
fi

# Add the alias
echo "$ALIAS_COMMAND" >> "$SHELL_RC"

echo "✅ Alias '$ALIAS_NAME' added to $SHELL_RC"
echo ""
echo "➡️ ❯❯❯❯  To use the alias in current session, run: 🚀 📢"
echo "  source $SHELL_RC"
echo ""
echo "Or restart your terminal."
echo ""
echo "Then you can run the dictation tool with just:"
echo "  $ALIAS_NAME"
