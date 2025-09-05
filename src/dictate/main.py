#!/usr/bin/env python3
"""
Main module for backward compatibility

This module provides the original dictate.py functionality while the new
modular structure is being developed.
"""

import sys
import os
from pathlib import Path

# Add the original dictate.py functionality
# This ensures existing users can still run the tool the same way

def main():
    """Main entry point that delegates to the original script or new CLI."""
    
    # If called directly, try to import and run the CLI
    try:
        from .cli import main as cli_main
        cli_main()
    except ImportError:
        # Fall back to original functionality
        print("New CLI dependencies not available, falling back to original script...")
        
        # Import the original dictate.py functionality
        current_dir = Path(__file__).parent.parent.parent
        original_script = current_dir / "dictate.py"
        
        if original_script.exists():
            # Execute the original script
            import subprocess
            result = subprocess.run([sys.executable, str(original_script)] + sys.argv[1:])
            sys.exit(result.returncode)
        else:
            print("Error: Original dictate.py not found")
            sys.exit(1)


if __name__ == '__main__':
    main()
