"""
CADGraphicsView - Custom graphics view for CAD operations
"""

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QCursor

from ..graphics_items.grid_graphics_items import GridBackground, RulersForeground



class CadView(QGraphicsView):
    """CAD graphics view with proper rubber band selection."""

    def __init__(self, scene=None):
        super().__init__(scene)

        # Enable mouse tracking to receive mouse move events
        self.setMouseTracking(True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        # Enable Qt's built-in rubber band selection
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setInteractive(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.resetTransform()
        dpmm = self.physicalDpiX() / 2.54
        self.scale(dpmm, -dpmm)
