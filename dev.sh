#!/bin/bash
# Development helper script for PyTkCAD

# Change to the script's directory
cd "$(dirname "$0")"

case "$1" in
    "activate")
        echo "To activate the virtual environment, run:"
        echo "source venv/bin/activate"
        ;;
    "install")
        echo "Installing dependencies..."
        source venv/bin/activate
        pip install -r requirements.txt
        ;;
    "run")
        echo "Running PyTkCAD..."
        source venv/bin/activate
        python main.py
        ;;
    "setup")
        echo "Setting up virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        echo "Setup complete! Use './dev.sh run' to start the application."
        ;;
    *)
        echo "PyTkCAD Development Helper"
        echo "Usage: $0 {setup|install|run|activate}"
        echo ""
        echo "Commands:"
        echo "  setup    - Create virtual environment and install dependencies"
        echo "  install  - Install/update dependencies"
        echo "  run      - Run the PyTkCAD application"
        echo "  activate - Show command to activate virtual environment"
        ;;
esac
