#!/usr/bin/env python3
"""
Setup configuration for the Voice Dictation Tool
Simple pip-installable package with CLI entry point
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

setup(
    name="voice-dictate",
    version="0.1.0",
    description="A powerful voice dictation tool with AI transcription and vector search",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Benjamin Mizrany",
    author_email="benjamayden@example.com",
    url="https://github.com/benjamayden/dictate",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        'console_scripts': [
            'dictate=dictate.cli:main',
        ],
    },
    install_requires=[
        'sounddevice>=0.4.6',
        'soundfile>=0.12.1',
        'google-genai>=0.1.0',
        'chromadb>=0.4.0',
        'python-dotenv>=1.0.0',
        'click>=8.0.0',
        'rich>=13.0.0',
        'numpy>=1.24.3',
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Capture/Recording",
        "Topic :: Text Processing :: Linguistic",
    ],
)
