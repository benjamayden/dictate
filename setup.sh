#!/bin/bash

# Voice Dictation Tool Setup Script
# This script sets up everything needed to run the voice dictation tool

set -e  # Exit on any error

echo "🎙️  Voice Dictation Tool Setup"
echo "=============================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📂 Working in directory: $SCRIPT_DIR"

# Check if config.txt exists
if [ ! -f "config.txt" ]; then
    echo "❌ config.txt not found! Please make sure config.txt is in the same directory."
    exit 1
fi

# Check if user has added their API key
if grep -q "your-api-key-here" config.txt; then
    echo "❌ Please edit config.txt and add your Gemini API key first!"
    echo "   1. Open config.txt in any text editor"
    echo "   2. Replace 'your-api-key-here' with your actual API key"
    echo "   3. Get your API key from: https://aistudio.google.com/app/apikey"
    echo "   4. Run this setup script again"
    exit 1
fi

echo "✅ Configuration file found with API key"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    echo "   Visit: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✅ pip3 found"

# Create virtual environment
echo ""
echo "🔧 Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "   Virtual environment already exists, removing old one..."
    rm -rf .venv
fi

python3 -m venv .venv
echo "✅ Virtual environment created"

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -e .
echo "✅ Dependencies installed"

# Create .env file from config.txt
echo ""
echo "⚙️  Creating .env file..."
cp config.txt .env
echo "✅ .env file created"

# Clear API key from config.txt for security
echo "🔒 Securing config.txt file..."
sed -i.bak 's/GEMINI_API_KEY=.*/GEMINI_API_KEY=your-api-key-here/' config.txt
rm config.txt.bak 2>/dev/null || true
echo "✅ API key cleared from config.txt for security"

# Read configuration
echo ""
echo "📋 Reading configuration..."
source .env

# Set up shortcuts
echo ""
echo "🔗 Setting up shell shortcuts..."

# Determine shell and config file
SHELL_NAME=$(basename "$SHELL")
if [ "$SHELL_NAME" = "zsh" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ "$SHELL_NAME" = "bash" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
else
    echo "⚠️  Unknown shell: $SHELL_NAME"
    echo "   You may need to manually add aliases to your shell config"
    SHELL_CONFIG=""
fi

if [ -n "$SHELL_CONFIG" ]; then
    # Create backup of shell config
    if [ -f "$SHELL_CONFIG" ]; then
        cp "$SHELL_CONFIG" "${SHELL_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Remove existing dictate aliases
    if [ -f "$SHELL_CONFIG" ]; then
        grep -v "# Voice Dictation Tool alias" "$SHELL_CONFIG" > "${SHELL_CONFIG}.tmp" || true
        mv "${SHELL_CONFIG}.tmp" "$SHELL_CONFIG"
    fi
    
    # Add new aliases
    echo "" >> "$SHELL_CONFIG"
    echo "# Voice Dictation Tool aliases" >> "$SHELL_CONFIG"
    
    # Use custom alias names from config, with defaults
    RECORD_ALIAS=${DICTATE_ALIAS_NAME:-rec}
    COMMAND_ALIAS=${DICTATE_COMMAND_ALIAS:-dictate}
    NOTES_ALIAS=${NOTES_FOLDER_ALIAS:-vnotes}
    
    echo "alias $RECORD_ALIAS='cd \"$SCRIPT_DIR\" && source .venv/bin/activate && PYTHONPATH=\"$SCRIPT_DIR/src\" python -m dictate record' # Voice Dictation Tool alias" >> "$SHELL_CONFIG"
    echo "alias $COMMAND_ALIAS='cd \"$SCRIPT_DIR\" && source .venv/bin/activate && PYTHONPATH=\"$SCRIPT_DIR/src\" python -m dictate' # Voice Dictation Tool alias" >> "$SHELL_CONFIG"
    echo "alias $NOTES_ALIAS='open \"${DICTATE_RECORDINGS_DIR:-$SCRIPT_DIR/recordings}\"' # Voice Dictation Tool alias" >> "$SHELL_CONFIG"
    
    echo "✅ Shortcuts added to $SHELL_CONFIG:"
    echo "   $RECORD_ALIAS - Start voice dictation"
    echo "   $COMMAND_ALIAS - Full dictate command suite"
    echo "   $NOTES_ALIAS - Open recordings folder"
    
    # Source the shell config to make aliases available immediately
    if [ "$SHELL_NAME" = "zsh" ] && [ -n "$ZSH_VERSION" ]; then
        source "$SHELL_CONFIG" 2>/dev/null || true
    elif [ "$SHELL_NAME" = "bash" ] && [ -n "$BASH_VERSION" ]; then
        source "$SHELL_CONFIG" 2>/dev/null || true
    fi
fi

# Test installation
echo ""
echo "🧪 Testing installation..."
if PYTHONPATH="$SCRIPT_DIR/src" python -m dictate --help >/dev/null 2>&1; then
    echo "✅ Installation test passed"
else
    echo "❌ Installation test failed"
    exit 1
fi

# Create recordings directory
RECORDINGS_DIR=${DICTATE_RECORDINGS_DIR:-./recordings}
mkdir -p "$RECORDINGS_DIR"
echo "✅ Recordings directory created: $RECORDINGS_DIR"

# Success message
echo ""
echo "🎉 Setup complete!"
echo "=================="
echo ""
echo "You can now use the voice dictation tool in these ways:"
echo ""
echo "1. Using the alias (after restarting your terminal or running 'source ~/.${SHELL_NAME}rc'):"
echo "   $RECORD_ALIAS"
echo ""
echo "2. Using the direct command:"
echo "   cd $SCRIPT_DIR && source .venv/bin/activate && PYTHONPATH=\"$SCRIPT_DIR/src\" python -m dictate"
echo ""
echo "3. Opening your recordings folder:"
echo "   $NOTES_ALIAS"
echo ""
echo "📝 To get started:"
echo "   1. Restart your terminal (or run: source ~/.${SHELL_NAME}rc)"
echo "   2. Run: $RECORD_ALIAS"
echo "   3. Follow the prompts to start recording!"
echo ""
echo "🔧 To reconfigure:"
echo "   1. Edit config.txt with your new settings"
echo "   2. Run: ./setup.sh again"
echo ""
echo "📚 For help:"
echo "   $RECORD_ALIAS --help"
