#!/usr/bin/env python3
"""
Test script to specifically verify tool palette icon loading
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
from BelfryCAD.tools import available_tools

def test_icon_loading_method():
    """Test the icon loading method directly"""
    def load_tool_icon(icon_name):
        """Load an icon for a tool, preferring SVG over PNG"""
        if not icon_name:
            return None

        # Construct the path to the images directory
        base_dir = os.path.dirname(__file__)
        images_dir = os.path.join(base_dir, 'images')

        # Try SVG first, then fall back to PNG
        svg_path = os.path.join(images_dir, f"{icon_name}.svg")
        png_path = os.path.join(images_dir, f"{icon_name}.png")

        # Prefer SVG if available
        if os.path.exists(svg_path):
            try:
                icon = QIcon(svg_path)
                if not icon.isNull():
                    return icon
            except Exception as e:
                print(f"Failed to load SVG icon {svg_path}: {e}")

        # Fall back to PNG if SVG not available or failed to load
        if os.path.exists(png_path):
            try:
                pixmap = QPixmap(png_path)
                if not pixmap.isNull():
                    # Scale PNG icons to 48x48 for better visibility
                    scaled_pixmap = pixmap.scaled(
                        48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    return QIcon(scaled_pixmap)
            except Exception as e:
                print(f"Failed to load PNG icon {png_path}: {e}")

        return None
    
    return load_tool_icon

def test_tool_palette_icons():
    """Test that tool palette icons are properly loaded"""
    app = QApplication([])
    
    print("Testing tool palette icon loading...")
    print(f"Number of available tools: {len(available_tools)}")
    
    # Get the icon loader function
    icon_loader = test_icon_loading_method()
    
    # Test loading icons for each tool
    success_count = 0
    total_count = 0
    failed_tools = []
    
    for tool_class in available_tools:
        # Create an instance to get definitions (with None arguments)
        try:
            tool = tool_class(None, None, None)
            for definition in tool.definitions:
                total_count += 1
                icon_name = definition.icon
                print(f"\nTesting {definition.name} (icon: {icon_name})")
                
                # Test the icon loading
                icon = icon_loader(icon_name)
                
                if icon and not icon.isNull():
                    print(f"  ✓ Icon loaded successfully")
                    success_count += 1
                    
                    # Check if icon has available sizes
                    sizes = icon.availableSizes()
                    if sizes:
                        print(f"  Available sizes: {sizes}")
                    else:
                        print(f"  Vector icon (scalable)")
                else:
                    print(f"  ✗ Icon failed to load")
                    failed_tools.append(f"{definition.name} ({icon_name})")
        except Exception as e:
            print(f"  ✗ Error creating tool {tool_class.__name__}: {e}")
    
    print(f"\nResult: {success_count}/{total_count} tool icons loaded successfully")
    
    if failed_tools:
        print(f"\nFailed to load icons for:")
        for failed in failed_tools:
            print(f"  - {failed}")
    
    # Check which icon files actually exist
    print(f"\nChecking icon file availability...")
    images_dir = os.path.join(os.path.dirname(__file__), 'images')
    svg_count = 0
    png_count = 0
    
    for file in os.listdir(images_dir):
        if file.startswith('tool-') and file.endswith('.svg'):
            svg_count += 1
        elif file.startswith('tool-') and file.endswith('.png'):
            png_count += 1
    
    print(f"Available tool icons: {svg_count} SVG files, {png_count} PNG files")
    
    if success_count == total_count:
        print("🎉 All tool icons loaded successfully!")
        return True
    else:
        print(f"❌ {total_count - success_count} icons failed to load")
        return False

if __name__ == "__main__":
    success = test_tool_palette_icons()
    sys.exit(0 if success else 1)
