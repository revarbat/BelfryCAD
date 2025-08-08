#!/usr/bin/env python3
"""
Test script to verify that view items store their viewmodel reference in data slot 0.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import QPointF

from BelfryCAD.gui.viewmodels.cad_object_factory import CADObjectFactory
from BelfryCAD.models.cad_objects.line_cad_object import LineCadObject
from BelfryCAD.utils.geometry import Point2D

class TestViewmodelDataSlot(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Viewmodel Data Slot")
        self.setGeometry(100, 100, 800, 600)
        
        # Create layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create graphics scene and view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)
        
        # Create buttons
        self.create_line_btn = QPushButton("Create Line")
        self.create_line_btn.clicked.connect(self.create_line)
        layout.addWidget(self.create_line_btn)
        
        self.test_data_slot_btn = QPushButton("Test Data Slot")
        self.test_data_slot_btn.clicked.connect(self.test_data_slot)
        layout.addWidget(self.test_data_slot_btn)
        
        # Store created items
        self.created_items = []
        
    def create_line(self):
        """Create a line object and add it to the scene."""
        # Create a mock main window (we just need the factory)
        class MockMainWindow:
            def __init__(self):
                self.preferences_viewmodel = None
        
        mock_main_window = MockMainWindow()
        factory = CADObjectFactory(mock_main_window)
        
        # Create a line object
        start_point = Point2D(0, 0)
        end_point = Point2D(100, 100)
        line_object = LineCadObject(start_point, end_point)
        
        # Create model and viewmodel
        model, viewmodel = factory.create_line_object(start_point, end_point)
        
        # Update the view to create view items
        viewmodel.update_view(self.scene)
        
        # Store the viewmodel for testing
        self.created_items.append(viewmodel)
        
        print(f"Created line with {len(viewmodel.view_items)} view items")
        
    def test_data_slot(self):
        """Test that view items have the correct viewmodel reference in data slot 0."""
        if not self.created_items:
            print("No items created yet. Create a line first.")
            return
            
        for i, viewmodel in enumerate(self.created_items):
            print(f"\nTesting viewmodel {i}:")
            print(f"  Object type: {viewmodel.object_type}")
            print(f"  Object ID: {viewmodel.object_id}")
            
            # Check each view item
            for j, view_item in enumerate(viewmodel.view_items):
                print(f"  View item {j}:")
                
                # Check if data slot 0 contains the viewmodel
                data = view_item.data(0)
                if data is viewmodel:
                    print(f"    ✓ Data slot 0 contains correct viewmodel reference")
                else:
                    print(f"    ✗ Data slot 0 does not contain correct viewmodel reference")
                    print(f"    Expected: {viewmodel}, Got: {data}")
                
                # Check if the viewmodel has the correct object type
                if hasattr(data, 'object_type'):
                    print(f"    ✓ Data slot 0 object type: {data.object_type}")
                else:
                    print(f"    ✗ Data slot 0 object has no object_type attribute")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    test_widget = TestViewmodelDataSlot()
    test_widget.show()
    
    print("Test Viewmodel Data Slot")
    print("1. Click 'Create Line' to create a line object")
    print("2. Click 'Test Data Slot' to verify viewmodel references")
    print("3. Close the window to exit")
    
    sys.exit(app.exec()) 