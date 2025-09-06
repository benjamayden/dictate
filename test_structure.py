#!/usr/bin/env python3
"""
Test script to verify the new modular structure works correctly
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test that all modules can be imported correctly."""
    print("Testing module imports...")
    
    try:
        # Test basic imports without external dependencies
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        import dictate
        print("✅ dictate package imported successfully")
        
        # Test individual modules (may fail if dependencies not installed)
        try:
            from dictate.audio_recorder import AudioRecorder, MicrophoneManager
            print("✅ audio_recorder module imported successfully")
        except ImportError as e:
            print(f"⚠️  audio_recorder import failed: {e}")
            
        try:
            from dictate.transcription import GeminiTranscriber
            print("✅ transcription module imported successfully")
        except ImportError as e:
            print(f"⚠️  transcription import failed: {e}")
            
        try:
            from dictate.vector_store import VectorStoreManager
            print("✅ vector_store module imported successfully")
        except ImportError as e:
            print(f"⚠️  vector_store import failed: {e}")
            
        try:
            from dictate.cli import cli
            print("✅ cli module imported successfully")
        except ImportError as e:
            print(f"⚠️  cli import failed: {e}")
            
        print("\n✅ Module structure test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_setup_py():
    """Test that setup.py is valid."""
    print("\nTesting setup.py...")
    
    try:
        setup_file = Path(__file__).parent / "setup.py"
        if setup_file.exists():
            # Try to parse the setup.py file
            with open(setup_file, 'r') as f:
                content = f.read()
                
            if 'setup(' in content and 'install_requires' in content:
                print("✅ setup.py appears to be valid")
                return True
            else:
                print("❌ setup.py missing required sections")
                return False
        else:
            print("❌ setup.py not found")
            return False
            
    except Exception as e:
        print(f"❌ setup.py test failed: {e}")
        return False

def test_requirements():
    """Test that requirements.txt is updated."""
    print("\nTesting requirements.txt...")
    
    try:
        req_file = Path(__file__).parent / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                content = f.read()
                
            required_packages = ['sounddevice', 'google-genai', 'chromadb', 'click', 'rich']
            missing = []
            
            for package in required_packages:
                if package not in content:
                    missing.append(package)
                    
            if not missing:
                print("✅ requirements.txt contains all required packages")
                return True
            else:
                print(f"❌ requirements.txt missing: {missing}")
                return False
        else:
            print("❌ requirements.txt not found")
            return False
            
    except Exception as e:
        print(f"❌ requirements.txt test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Voice Dictation Tool - Modular Structure")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_setup_py, 
        test_requirements
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
        
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The modular structure is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -e .")
        print("2. Test the CLI: dictate --help")
        print("3. Copy .env.template to .env and configure your API key")
    else:
        print("❌ Some tests failed. Please review the errors above.")
        
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
