#!/bin/bash

# Create voice dictation command alias and notes folder alias
echo "🔗 Setting up voice dictation command aliases..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from .env file if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# Get custom alias names from environment or use defaults
DICTATE_ALIAS="${DICTATE_ALIAS_NAME:-dictate}"
NOTES_ALIAS="${NOTES_FOLDER_ALIAS:-goNotes}"

echo "📝 Creating aliases:"
echo "  - $DICTATE_ALIAS (for voice dictation)"
echo "  - $NOTES_ALIAS (to open notes folder)"

DICTATE_PATH="$SCRIPT_DIR/dictate.py"
DICTATE_ALIAS_COMMAND="alias $DICTATE_ALIAS=\"python3 $DICTATE_PATH\""

# Get the notes directory path
if [ -n "$DICTATE_RECORDINGS_DIR" ]; then
    NOTES_PATH="$DICTATE_RECORDINGS_DIR"
else
    NOTES_PATH="$SCRIPT_DIR/recordings"
fi

# Create the notes folder alias command
NOTES_ALIAS_COMMAND="alias $NOTES_ALIAS=\"open '$NOTES_PATH'\""

# Detect shell and add aliases
if [[ $SHELL == *"zsh"* ]]; then
    SHELL_RC="$HOME/.zshrc"
    echo "📝 Adding aliases to $SHELL_RC"
elif [[ $SHELL == *"bash"* ]]; then
    SHELL_RC="$HOME/.bashrc"
    echo "📝 Adding aliases to $SHELL_RC"
else
    SHELL_RC="$HOME/.profile"
    echo "📝 Adding aliases to $SHELL_RC"
fi

# Function to add or update alias
add_or_update_alias() {
    local alias_name="$1"
    local alias_command="$2"
    
    # Check if alias already exists
    if grep -q "alias $alias_name=" "$SHELL_RC" 2>/dev/null; then
        echo "⚠️  '$alias_name' alias already exists in $SHELL_RC"
        echo "Updating existing alias..."
        # Remove old alias and add new one
        grep -v "alias $alias_name=" "$SHELL_RC" > "${SHELL_RC}.tmp" && mv "${SHELL_RC}.tmp" "$SHELL_RC"
    fi
    
    # Add the alias
    echo "$alias_command" >> "$SHELL_RC"
    echo "✅ Alias '$alias_name' added/updated in $SHELL_RC"
}

# Add both aliases
add_or_update_alias "$DICTATE_ALIAS" "$DICTATE_ALIAS_COMMAND"
add_or_update_alias "$NOTES_ALIAS" "$NOTES_ALIAS_COMMAND"

echo ""
echo "🎉 All aliases created successfully!"
echo ""
echo "➡️ ❯❯❯❯  To use the aliases in current session, run: 🚀 📢"
echo "  source $SHELL_RC"
echo ""
echo "Or restart your terminal."
echo ""
echo "Then you can use:"
echo "  $DICTATE_ALIAS     # Start voice dictation"
echo "  $NOTES_ALIAS       # Open notes folder"
echo ""
echo "📁 Notes folder location: $NOTES_PATH"
