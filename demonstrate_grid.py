#!/usr/bin/env python3
"""
Final Grid Demonstration - Shows grid alignment with rulers
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from src.gui.main_window import MainWindow
from src.core.config import Config
from src.core.preferences import PreferencesManager
from src.core.document import Document

def demonstrate_grid():
    """Create a demonstration of the grid functionality"""
    
    print("🎯 Grid Implementation Demonstration")
    print("=" * 50)
    
    app = QApplication(sys.argv)
    
    # Create application components
    config = Config()
    preferences = PreferencesManager(config)
    document = Document(preferences)
    
    # Create main window with grid
    window = MainWindow(config, preferences, document)
    window.show()
    
    print("✅ Main window created with grid functionality")
    print("📏 Grid features:")
    print("   • Dotted lines every 5 coordinate units")
    print("   • Light gray color (200,200,200)")
    print("   • Aligned with ruler major tickmarks")
    print("   • Updates when scrolling/panning")
    print("   • Behind axis lines and drawing objects")
    
    # Add a timer to create some test objects after a short delay
    def add_test_objects():
        print("🔧 Adding test objects to demonstrate grid alignment...")
        
        # Add some test lines at grid positions for visual verification
        from PySide6.QtGui import QPen, QColor
        from PySide6.QtCore import Qt
        
        test_pen = QPen(QColor(255, 0, 0))
        test_pen.setWidth(3)
        
        # Add a square at grid position (0,0) to (10,10)
        window.scene.addRect(0, 0, 10, 10, test_pen)
        
        # Add a line from (-15,-15) to (15,15) 
        window.scene.addLine(-15, -15, 15, 15, test_pen)
        
        # Add some circles at grid intersections
        circle_pen = QPen(QColor(0, 0, 255))
        circle_pen.setWidth(2)
        
        for x in range(-20, 25, 5):
            for y in range(-20, 25, 5):
                if abs(x) <= 20 and abs(y) <= 20:  # Only near center
                    window.scene.addEllipse(x-1, y-1, 2, 2, circle_pen)
        
        print("✨ Test objects added at grid-aligned positions")
        print("👀 Look for:")
        print("   • Red square from (0,0) to (10,10)")
        print("   • Red diagonal line") 
        print("   • Blue dots at grid intersections")
        print("   • All should align with dotted grid lines")
    
    # Create timer to add test objects after UI is ready
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(add_test_objects)
    timer.start(1000)  # 1 second delay
    
    print("\n🚀 Starting demonstration...")
    print("📋 Instructions:")
    print("   1. Observe the dotted grid lines in the canvas")
    print("   2. Check alignment with ruler tickmarks")
    print("   3. Try scrolling - grid should update")
    print("   4. Test objects will appear in 1 second")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(demonstrate_grid())
