#!/usr/bin/env python3
"""
Test script to verify SVG icon loading is working correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QIcon

def test_svg_icon_loading():
    """Test that SVG icons can be loaded properly"""
    app = QApplication(sys.argv)
    
    # Test a few key icons that should have been converted to SVG
    test_icons = [
        'tool-line',
        'tool-circle2pt', 
        'tool-rectangle',
        'tool-arc2ptrad',
        'tool-bezier',
        'tool-text'
    ]
    
    images_dir = os.path.join(os.path.dirname(__file__), 'images')
    svg_dir = images_dir  # SVG files are in main images directory
    
    success_count = 0
    total_count = len(test_icons)
    
    print("Testing SVG icon loading...")
    print(f"SVG directory: {svg_dir}")
    print()
    
    for icon_name in test_icons:
        svg_path = os.path.join(svg_dir, f"{icon_name}.svg")
        png_path = os.path.join(images_dir, f"{icon_name}.png")
        
        svg_exists = os.path.exists(svg_path)
        png_exists = os.path.exists(png_path)
        
        print(f"Testing {icon_name}:")
        print(f"  SVG exists: {svg_exists}")
        print(f"  PNG exists: {png_exists}")
        
        if svg_exists:
            try:
                # Test SVG loading
                svg_icon = QIcon(svg_path)
                if not svg_icon.isNull():
                    print(f"  ✓ SVG loaded successfully")
                    success_count += 1
                    
                    # Get icon sizes to verify it's working
                    sizes = svg_icon.availableSizes()
                    if sizes:
                        print(f"  Available sizes: {sizes}")
                    else:
                        print(f"  Vector icon (scalable)")
                else:
                    print(f"  ✗ SVG failed to create QIcon")
            except Exception as e:
                print(f"  ✗ SVG exception: {e}")
        elif png_exists:
            print(f"  ⚠ No SVG available, PNG exists as fallback")
        else:
            print(f"  ✗ Neither SVG nor PNG found")
        
        print()
    
    print(f"Result: {success_count}/{total_count} SVG icons loaded successfully")
    
    if success_count == total_count:
        print("🎉 All test SVG icons loaded successfully!")
        return True
    elif success_count > 0:
        print("⚠ Some SVG icons loaded successfully, others may need PNG fallback")
        return True
    else:
        print("❌ No SVG icons could be loaded")
        return False

if __name__ == "__main__":
    success = test_svg_icon_loading()
    sys.exit(0 if success else 1)
