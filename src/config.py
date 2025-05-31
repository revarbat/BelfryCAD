"""
Application configuration and constants for PyTkCAD.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

class AppConfig:
    """Application configuration class."""

    # Application information
    APP_NAME = "PyTkCAD"
    VERSION = "0.228"  # Matching the original TCL version

    # Precision settings
    PRECISION = 16

    def __init__(self):
        """Initialize application configuration."""
        self.setup_paths()
        self.setup_platform_specifics()
        self.setup_preferences()

    def setup_paths(self):
        """Set up application paths."""
        self.root_dir = Path(__file__).parent.parent
        self.src_dir = self.root_dir / "src"
        self.images_dir = self.root_dir / "images"
        self.plugins_dir = self.root_dir / "plugins"
        self.cncfonts_dir = self.root_dir / "cncfonts"

        # Create directories if they don't exist
        self.images_dir.mkdir(exist_ok=True)
        self.plugins_dir.mkdir(exist_ok=True)
        self.cncfonts_dir.mkdir(exist_ok=True)

    def setup_platform_specifics(self):
        """Set up platform-specific configurations."""
        self.platform = sys.platform

        # Determine windowing system
        if self.platform == "darwin":
            self.windowing_system = "aqua"
            # macOS preferences location
            self.prefs_dir = Path.home() / "Library" / "Preferences"
        elif self.platform == "win32":
            self.windowing_system = "win32"
            # Windows preferences location
            self.prefs_dir = Path.home()
        else:
            self.windowing_system = "x11"
            # Unix/Linux preferences location
            self.prefs_dir = Path.home()

    def setup_preferences(self):
        """Set up preferences configuration."""
        self.prefs_file = self.prefs_dir / f".{self.APP_NAME.lower()}_prefs"

        # Default preferences
        self.default_prefs = {
            "antialiasing": True,
            "grid_visible": True,
            "snap_to_grid": True,
            "show_rulers": True,
            "units": "inches",  # or "mm"
            "precision": 3,
            "auto_save": True,
            "auto_save_interval": 300,  # seconds
            "recent_files_count": 10,
            "window_geometry": "1200x800+100+100",
            "canvas_bg_color": "#ffffff",
            "grid_color": "#cccccc",
            "selection_color": "#0080ff",
        }

# Tool definitions (matching the original TCL tools)
TOOL_DEFINITIONS = {
    # CNC Tools from main.tcl
    1: {"size": "1/32", "flutes": 2, "material": "Carbide"},
    2: {"size": "1/32", "flutes": 3, "material": "Carbide"},
    3: {"size": "1/16", "flutes": 2, "material": "Carbide"},
    4: {"size": "1/16", "flutes": 3, "material": "Carbide"},
    5: {"size": "1/16", "flutes": 4, "material": "Carbide"},
    6: {"size": "1/16", "flutes": 4, "material": "HSS"},
    7: {"size": "1/8", "flutes": 2, "material": "HSS"},
    8: {"size": "1/8", "flutes": 3, "material": "Carbide"},
    9: {"size": "1/8", "flutes": 4, "material": "Carbide"},
    10: {"size": "3/16", "flutes": 3, "material": "Carbide"},
    11: {"size": "3/16", "flutes": 4, "material": "Carbide"},
    12: {"size": "1/4", "flutes": 4, "material": "Carbide"},
    13: {"size": "1/4", "flutes": 4, "material": "HSS"},
    18: {"size": "0.001", "flutes": 4, "bevel": 90, "material": "Carbide"},
    20: {"size": "0.012", "flutes": 1, "material": "HSS"},
    25: {"size": "1.025", "flutes": 23, "material": "HSS"},
}

# Mill configuration (from main.tcl)
MILL_CONFIG = {
    "discrete_speeds": True,
    "rpm_list": [1100, 1900, 2900, 4300, 6500, 10500],
    "fixed_rpm": True,
    "auto_tool_changer": False,
    "horsepower": 0.167,
    "max_feed": 15.0,
}

# Stock configuration (from main.tcl)
DEFAULT_STOCK = {
    "width": 9,
    "height": 5.5,
    "thickness": 0.0625,
    "material": "Aluminum",
}

# Drawing tool configurations
DRAWING_TOOLS = [
    "select",
    "line",
    "arc",
    "circle",
    "bezier",
    "polygon",
    "text",
    "dimension",
    "point",
    "image",
    "transform",
    "duplicate",
]

# File format support
SUPPORTED_FORMATS = {
    "native": {
        "extension": ".tkcad",
        "description": "TkCAD Native Format",
        "can_read": True,
        "can_write": True,
    },
    "svg": {
        "extension": ".svg",
        "description": "Scalable Vector Graphics",
        "can_read": True,
        "can_write": True,
    },
    "dxf": {
        "extension": ".dxf",
        "description": "AutoCAD DXF",
        "can_read": True,
        "can_write": True,
    },
}
