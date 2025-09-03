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

# Function to detect and select preferred microphone
select_microphone() {
    echo ""
    echo "🎤 Detecting available microphones..."
    
    # Check if python3 and sounddevice are available
    if ! python3 -c "import sounddevice" &> /dev/null; then
        echo "⚠️  Cannot detect microphones - sounddevice not yet installed"
        echo "   Microphone selection will be skipped for now"
        return
    fi
    
    # Get list of available input devices
    MIC_OUTPUT=$(python3 -c "
import sounddevice as sd
import sys
try:
    devices = sd.query_devices()
    input_devices = []
    for i, device in enumerate(devices):
        if device.get('max_input_channels', 0) > 0:
            input_devices.append((i, device['name'], device.get('max_input_channels', 0)))
    
    if not input_devices:
        print('NO_MICS_FOUND')
        sys.exit(0)
    
    for idx, (device_idx, name, channels) in enumerate(input_devices):
        print(f'{idx + 1}. {name} (Device {device_idx}, {channels} channels)')
    
    print(f'DEVICE_COUNT:{len(input_devices)}')
    for device_idx, name, channels in input_devices:
        print(f'DEVICE_INFO:{device_idx}:{name}')
except Exception as e:
    print('ERROR_DETECTING_MICS')
" 2>/dev/null)
    
    if [[ "$MIC_OUTPUT" == *"NO_MICS_FOUND"* ]] || [[ "$MIC_OUTPUT" == *"ERROR_DETECTING_MICS"* ]]; then
        echo "⚠️  No microphones detected or error occurred"
        return
    fi
    
    echo ""
    echo "Available microphones:"
    echo "$MIC_OUTPUT" | grep -E "^[0-9]+\." || true
    
    DEVICE_COUNT=$(echo "$MIC_OUTPUT" | grep "DEVICE_COUNT:" | cut -d: -f2)
    
    if [ -z "$DEVICE_COUNT" ] || [ "$DEVICE_COUNT" -eq 0 ]; then
        echo "⚠️  No microphones detected"
        return
    fi
    
    echo ""
    echo "Would you like to set a preferred microphone? (y/n)"
    read -r SET_MIC
    
    if [[ "$SET_MIC" =~ ^[Yy] ]]; then
        echo "Enter the number of your preferred microphone (1-$DEVICE_COUNT), or 0 to skip:"
        read -r MIC_CHOICE
        
        if [[ "$MIC_CHOICE" =~ ^[1-9][0-9]*$ ]] && [ "$MIC_CHOICE" -le "$DEVICE_COUNT" ]; then
            # Get the actual device index for the selected choice
            SELECTED_DEVICE=$(echo "$MIC_OUTPUT" | grep "DEVICE_INFO:" | sed -n "${MIC_CHOICE}p" | cut -d: -f2)
            SELECTED_NAME=$(echo "$MIC_OUTPUT" | grep "DEVICE_INFO:" | sed -n "${MIC_CHOICE}p" | cut -d: -f3-)
            
            if [ ! -z "$SELECTED_DEVICE" ]; then
                echo ""
                echo "✅ Selected microphone: $SELECTED_NAME (Device $SELECTED_DEVICE)"
                
                # Add or update the preferred microphone in .env
                if grep -q "^PREFERRED_MICROPHONE=" .env 2>/dev/null; then
                    # Update existing line (works on both macOS and Linux)
                    if command -v gsed >/dev/null 2>&1; then
                        gsed -i "s/^PREFERRED_MICROPHONE=.*/PREFERRED_MICROPHONE=$SELECTED_DEVICE/" .env
                    else
                        sed -i.bak "s/^PREFERRED_MICROPHONE=.*/PREFERRED_MICROPHONE=$SELECTED_DEVICE/" .env && rm .env.bak
                    fi
                else
                    # Add new line
                    echo "" >> .env
                    echo "# Preferred microphone device index (optional)" >> .env
                    echo "# Set during setup - you can change this manually if needed" >> .env
                    echo "PREFERRED_MICROPHONE=$SELECTED_DEVICE" >> .env
                fi
                
                echo "✅ Preferred microphone saved to .env file"
            else
                echo "❌ Error selecting microphone"
            fi
        elif [ "$MIC_CHOICE" -eq 0 ]; then
            echo "⏭️  Skipping microphone selection"
        else
            echo "❌ Invalid selection. Skipping microphone setup."
        fi
    else
        echo "⏭️  Skipping microphone selection"
    fi
}

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

# Select preferred microphone after dependencies are installed
select_microphone

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
echo "4. Optionally set NOTES_FOLDER_ALIAS in .env to customize the notes folder command (default: 'goNotes')"
echo "5. Your preferred microphone has been configured (if selected)"
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
