# PyTkCAD - Python CAD Application

PyTkCAD is a CAD application built with Python and PySide6, converted from the original TCL TkCAD codebase.

## Requirements

- Python 3.13+
- PySide6 6.9.0+
- Pillow 11.0.0+

## Setup and Installation

### Using Virtual Environment (Recommended)

1. **Create and setup virtual environment:**
   ```bash
   ./dev.sh setup
   ```

2. **Run the application:**
   ```bash
   ./dev.sh run
   # or
   ./run.sh
   ```

3. **Manual activation (for development):**
   ```bash
   source venv/bin/activate
   python main.py
   ```

### Alternative Installation

1. **Install dependencies globally:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

## Development

The project includes helpful development scripts:

- `./dev.sh setup` - Create virtual environment and install dependencies
- `./dev.sh run` - Run the application with virtual environment
- `./dev.sh install` - Install/update dependencies
- `./dev.sh activate` - Show command to activate virtual environment
- `./run.sh` - Simple script to run the application

## Project Structure

- `main.py` - Application entry point
- `src/` - Main source code
  - `app.py` - Main application class
  - `gui/` - GUI components (main window, dialogs)
  - `tools/` - Drawing tools (line, circle, etc.)
  - `core/` - Core functionality (document, objects)
  - `utils/` - Utility functions
- `images/` - Tool icons and UI graphics
- `requirements.txt` - Python dependencies
- `venv/` - Virtual environment (created after setup)

## Features

- Complete CAD drawing tools (line, circle, ellipse, polygon, etc.)
- Left-positioned toolbar with 32x32 icons
- Modern Qt-based user interface
- File operations (save/load)
- Zero-spacing optimized layout

## Conversion Status

✅ **100% Complete** - Fully converted from tkinter to PySide6
- All drawing tools functional
- Modern Qt interface
- Optimized toolbar and canvas layout
