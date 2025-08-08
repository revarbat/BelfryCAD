"""
Example demonstrating the use of ConstructionLineItem.

This example shows how to create different types of construction lines
with various dash patterns and arrow tips.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QVBoxLayout, QWidget
from PySide6.QtCore import QPointF, QLineF, Qt
from PySide6.QtGui import QColor, QPainter

from src.BelfryCAD.gui.views.graphics_items.construction_line_item import (
    ConstructionLineItem, DashPattern, ArrowTip
)


def create_construction_line_demo():
    """Create a demonstration of different construction line types."""
    
    # Create application
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    # Create scene and view
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    
    # Set up the scene
    scene.setSceneRect(-50, -50, 400, 300)
    view.setRenderHint(QPainter.Antialiasing)
    
    # Create different types of construction lines
    y_offset = 0
    
    # 1. Solid construction line
    solid_line = ConstructionLineItem(
        QLineF(QPointF(50, 50 + y_offset), QPointF(200, 50 + y_offset)),
        DashPattern.SOLID
    )
    scene.addItem(solid_line)
    y_offset += 30
    
    # 2. Dashed construction line
    dashed_line = ConstructionLineItem(
        QLineF(QPointF(50, 50 + y_offset), QPointF(200, 50 + y_offset)),
        DashPattern.DASHED
    )
    scene.addItem(dashed_line)
    y_offset += 30
    
    # 3. Centerline construction line
    centerline = ConstructionLineItem(
        QLineF(QPointF(50, 50 + y_offset), QPointF(200, 50 + y_offset)),
        DashPattern.CENTERLINE
    )
    scene.addItem(centerline)
    y_offset += 30
    
    # 4. Construction line with start arrow
    start_arrow_line = ConstructionLineItem(
        QLineF(QPointF(50, 50 + y_offset), QPointF(200, 50 + y_offset)),
        DashPattern.DASHED,
        ArrowTip.START
    )
    scene.addItem(start_arrow_line)
    y_offset += 30
    
    # 5. Construction line with end arrow
    end_arrow_line = ConstructionLineItem(
        QLineF(QPointF(50, 50 + y_offset), QPointF(200, 50 + y_offset)),
        DashPattern.DASHED,
        ArrowTip.END
    )
    scene.addItem(end_arrow_line)
    y_offset += 30
    
    # 6. Construction line with both arrows
    both_arrow_line = ConstructionLineItem(
        QLineF(QPointF(50, 50 + y_offset), QPointF(200, 50 + y_offset)),
        DashPattern.SOLID,
        ArrowTip.BOTH
    )
    scene.addItem(both_arrow_line)
    y_offset += 30
    
    # 7. Diagonal construction lines
    diagonal_line1 = ConstructionLineItem(
        QLineF(QPointF(50, 50 + y_offset), QPointF(150, 100 + y_offset)),
        DashPattern.DASHED
    )
    scene.addItem(diagonal_line1)
    
    diagonal_line2 = ConstructionLineItem(
        QLineF(QPointF(200, 50 + y_offset), QPointF(300, 100 + y_offset)),
        DashPattern.CENTERLINE,
        ArrowTip.END
    )
    scene.addItem(diagonal_line2)
    
    # Fit view to scene
    view.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
    
    return view


def main():
    """Main function to run the construction line demo."""
    print("Creating ConstructionLineItem demonstration...")
    
    view = create_construction_line_demo()
    
    # Create a simple window to display the view
    window = QWidget()
    layout = QVBoxLayout()
    layout.addWidget(view)
    window.setLayout(layout)
    window.setWindowTitle("Construction Line Item Demo")
    window.resize(500, 400)
    window.show()
    
    print("Demo window created. Close the window to exit.")
    
    # Start the application
    app = QApplication.instance()
    app.exec()


if __name__ == "__main__":
    main() 