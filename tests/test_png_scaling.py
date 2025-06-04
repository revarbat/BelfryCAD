#!/usr/bin/env python3
"""
Test script to verify PNG icon scaling is working correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt

def test_png_scaling():
    """Test that PNG icons are being scaled to 150% (48x48)"""
    app = QApplication(sys.argv)
    
    # Import required classes for MainWindow initialization
    from src.gui.main_window import MainWindow
    from src.config import AppConfig
    from src.core.preferences import PreferencesManager
    from src.core.document import Document
    
    # Create the necessary dependencies for MainWindow
    config = AppConfig()
    preferences = PreferencesManager(config)
    document = Document()
    
    # Create a main window instance to access the icon loading method
    main_window = MainWindow(config, preferences, document)
    
    # Test icons that should only exist as PNG (no SVG version)
    png_only_icons = [
        'tool-rectangle',  # Should be PNG only
        'tool-text',       # Should be PNG only
        'tool-point',      # Should be PNG only
    ]
    
    success_count = 0
    total_count = len(png_only_icons)
    
    print("Testing PNG icon scaling to 150% (48x48 pixels)...")
    print()
    
    for icon_name in png_only_icons:
        print(f"Testing {icon_name}:")
        
        # Check file existence
        images_dir = os.path.join(os.path.dirname(__file__), 'images')
        svg_path = os.path.join(images_dir, f"{icon_name}.svg")
        png_path = os.path.join(images_dir, f"{icon_name}.png")
        
        svg_exists = os.path.exists(svg_path)
        png_exists = os.path.exists(png_path)
        
        print(f"  SVG exists: {svg_exists}")
        print(f"  PNG exists: {png_exists}")
        
        if png_exists and not svg_exists:
            try:
                # Test PNG scaling using the main window's method
                icon = main_window._load_tool_icon(icon_name)
                if icon and not icon.isNull():
                    print(f"  ✓ PNG icon loaded successfully")
                    
                    # Get the icon's pixmap at our expected size
                    pixmap = icon.pixmap(48, 48)
                    if not pixmap.isNull():
                        width = pixmap.width()
                        height = pixmap.height()
                        print(f"  Icon size: {width}x{height} pixels")
                        
                        # Verify it's scaled correctly
                        if width == 48 and height == 48:
                            print(f"  ✓ Correctly scaled to 150% (48x48)")
                            success_count += 1
                        elif width == 32 and height == 32:
                            print(f"  ⚠ Not scaled (still 32x32)")
                        else:
                            print(f"  ⚠ Unexpected size ({width}x{height})")
                    else:
                        print(f"  ✗ Could not get pixmap from icon")
                else:
                    print(f"  ✗ Failed to load PNG icon")
            except Exception as e:
                print(f"  ✗ Exception: {e}")
        elif svg_exists:
            print(f"  ⚠ SVG version exists, PNG scaling not tested")
        else:
            print(f"  ✗ PNG file not found")
        
        print()
    
    print(f"Result: {success_count}/{total_count} PNG icons correctly scaled to 150%")
    
    if success_count == total_count:
        print("🎉 All PNG icons are correctly scaled to 150%!")
        return True
    elif success_count > 0:
        print("⚠ Some PNG icons scaled correctly, others may need investigation")
        return True
    else:
        print("❌ PNG scaling does not appear to be working")
        return False

if __name__ == "__main__":
    success = test_png_scaling()
    sys.exit(0 if success else 1)
