#!/bin/bash

# Setup script for Voice Dictation Tool
echo "🎙️  Setting up Voice Dictation Tool"
echo "=================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📂 Working in directory: $SCRIPT_DIR"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "✅ Python 3 found"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✅ pip3 found"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env configuration file..."
    if [ -f "CONFIGURATION_TEMPLATE.txt" ]; then
        cp "CONFIGURATION_TEMPLATE.txt" ".env"
        echo "✅ Created .env from template"
        echo "⚠️  Please edit .env file and add your GEMINI_API_KEY"
    else
        echo "Creating basic .env file..."
        cat > .env << 'EOF'
# Google Gemini API Key (required)
GEMINI_API_KEY=your-api-key-here

# Directory where recordings will be saved (optional)
# If not set, will use ./recordings/ in the same directory as the script
DICTATE_RECORDINGS_DIR=

# Custom alias name for the terminal command (optional)
# If not set, will use 'dictate' as the default command name
DICTATE_ALIAS_NAME=
EOF
        echo "✅ Created basic .env file"
        echo "⚠️  Please edit .env file and add your GEMINI_API_KEY"
    fi
else
    echo "✅ .env file already exists"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."

pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Make the script executable
chmod +x dictate.py

# Create recordings directory if it doesn't exist
mkdir -p recordings

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit the .env file and add your GEMINI_API_KEY"
echo "2. Optionally set DICTATE_RECORDINGS_DIR in .env if you want recordings stored elsewhere"
echo "3. Optionally set DICTATE_ALIAS_NAME in .env to customize the command name (default: 'dictate')"
echo ""
echo "Usage:"
echo "  python3 dictate.py"
echo ""
echo "📝 To edit configuration:"
echo "  nano .env"
echo ""
echo "🔗 To create a global alias, run:"
echo "  ./create_alias.sh"
echo ""
echo "📖 For more info, see README.md"
