#!/bin/bash
# Script to run PyTkCAD with virtual environment

# Change to the script's directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run the application
python main.py
