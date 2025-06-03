#!/usr/bin/env python3
"""
Test script to verify PNG icon loading is working correctly
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QIcon

def test_icon_loading():
    """Test that PNG icons can be loaded properly"""
    app = QApplication(sys.argv)
    
    # Test a few key icons
    test_icons = [
        'tool-dimarc',
        'tool-circlectr', 
        'tool-line',
        'tool-rectangle',
        'layer-cam',
        'node-diamond'
    ]
    
    images_dir = os.path.join(os.path.dirname(__file__), 'images')
    
    success_count = 0
    total_count = len(test_icons)
    
    for icon_name in test_icons:
        icon_path = os.path.join(images_dir, f"{icon_name}.png")
        
        if os.path.exists(icon_path):
            try:
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    icon = QIcon(pixmap)
                    if not icon.isNull():
                        print(f"✓ {icon_name}.png loaded successfully")
                        success_count += 1
                    else:
                        print(f"✗ {icon_name}.png failed to create QIcon")
                else:
                    print(f"✗ {icon_name}.png failed to load as QPixmap")
            except Exception as e:
                print(f"✗ {icon_name}.png exception: {e}")
        else:
            print(f"✗ {icon_name}.png file not found")
    
    print(f"\nResult: {success_count}/{total_count} icons loaded successfully")
    
    if success_count == total_count:
        print("🎉 All test icons loaded successfully!")
        return True
    else:
        print("❌ Some icons failed to load")
        return False

if __name__ == "__main__":
    success = test_icon_loading()
    sys.exit(0 if success else 1)
