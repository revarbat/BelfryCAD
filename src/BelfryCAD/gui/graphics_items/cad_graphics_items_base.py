"""
Base class for custom CAD graphics items with proper selection indication.

This module provides a base class that handles selection indication by drawing
a thicker outline in the selection color behind the normal shape.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QBrush
from PySide6.QtWidgets import QAbstractGraphicsShapeItem, QGraphicsItem, QApplication


class CadGraphicsItemBase(QAbstractGraphicsShapeItem):
    """Base class for custom CAD graphics items with selection indication."""
    
    def __init__(self, pen: Optional[QPen] = None, brush: Optional[QBrush] = None, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)
        
        # Set up selection flags
        self._setup_selection_flags()
    
    def _setup_selection_flags(self):
        """Configure this item to be selectable and movable."""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
    
    def paint(self, painter, option, widget=None):
        """Paint the graphics item with selection indication if selected."""
        if self.isSelected():
            # Step 1: Draw selection outline (thicker, selection color)
            painter.save()
            # selection_color = QApplication.palette().highlight().color()
            selection_pen = QPen(Qt.GlobalColor.red, 3.0)
            selection_pen.setCosmetic(True)
            selection_pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(selection_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)  # No fill for selection outline
            shape = self.shape()
            painter.drawPath(shape)
            painter.restore()
        
        # Step 2: Draw normal shape (over the selection outline if selected)
        self._draw_shape_geometry(painter)
    
    def _draw_shape_geometry(self, painter):
        """
        Draw the specific shape geometry.
        
        This method must be implemented by subclasses to draw their specific
        shape (line, circle, etc.) using the current pen and brush.
        
        Args:
            painter: QPainter instance configured with the appropriate pen/brush
        """
        raise NotImplementedError("Subclasses must implement _draw_shape_geometry()")
    
