#!/usr/bin/env python3
"""Simple test for preferences dialog."""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Monkey patch the relative import
import types
import importlib.util

# Load core.preferences first
prefs_path = src_path / "core" / "preferences.py"
spec = importlib.util.spec_from_file_location("core.preferences", prefs_path)
prefs_module = importlib.util.module_from_spec(spec)
sys.modules["core.preferences"] = prefs_module
spec.loader.exec_module(prefs_module)

# Load the preferences dialog
dialog_path = src_path / "gui" / "preferences_dialog.py"
with open(dialog_path, 'r') as f:
    code = f.read()

# Replace the relative import
code = code.replace("from ..core.preferences import PreferencesManager",
                   "from core.preferences import PreferencesManager")

# Create and execute the module
spec = importlib.util.spec_from_file_location("preferences_dialog", dialog_path)
dialog_module = importlib.util.module_from_spec(spec)
exec(code, dialog_module.__dict__)

# Test it
if __name__ == "__main__":
    import tkinter as tk
    
    root = tk.Tk()
    root.title("Preferences Test")
    
    button = tk.Button(root, text="Open Preferences", 
                      command=lambda: dialog_module.show_preferences(root))
    button.pack(pady=20)
    
    root.mainloop()
