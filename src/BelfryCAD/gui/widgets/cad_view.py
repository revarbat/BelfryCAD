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
        self._rubber_band_rect = QRectF()
        self._is_rubber_banding = False
        self._start_pos = QPointF()
        self._current_pos = QPointF()
        self._dash_offset = 0.0

        # Enable mouse tracking to receive mouse move events
        self.setMouseTracking(True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setInteractive(True)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.resetTransform()
        dpi = self.physicalDpiX()
        self.scale(dpi, -dpi)

        # Create timer for rubber band updates
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_rubber_band)
        self._update_timer.setInterval(16)  # ~60 FPS

    def mousePressEvent(self, event):
        """Handle mouse press events for rubber band selection."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Convert view coordinates to scene coordinates
            scene_pos = self.mapToScene(event.position().toPoint())

            # Get all items at the scene position, sorted by z-value (top to bottom)
            items = self.scene().items(scene_pos)

            # Find the first non-background item
            item = None
            for scene_item in items:
                if not isinstance(scene_item, (RulersForeground, GridBackground)):
                    item = scene_item
                    break

            if item is None:
                # Start rubber band selection
                self._is_rubber_banding = True
                self._start_pos = scene_pos
                self._rubber_band_rect = QRectF()
                self.setCursor(Qt.CursorShape.CrossCursor)
                # Capture mouse to receive all mouse events
                self.grabMouse()
                # Start timer for rubber band updates
                self._update_timer.start()
                # Accept the event to prevent further processing
                event.accept()
            else:
                # Let the scene handle item selection and interaction
                self._is_rubber_banding = False
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events for rubber band selection."""
        if self._is_rubber_banding:
            # Update rubber band rectangle in scene coordinates
            current_pos = self.mapToScene(event.position().toPoint())
            self._rubber_band_rect = QRectF(self._start_pos, current_pos).normalized()
            self.viewport().update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events for rubber band selection."""
        if self._is_rubber_banding and event.button() == Qt.MouseButton.LeftButton:
            # Let the timer handle the selection completion
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def drawForeground(self, painter, rect):
        """Draw the rubber band selection rectangle."""
        super().drawForeground(painter, rect)

        if self._is_rubber_banding and not self._rubber_band_rect.isNull():
            painter.save()
            pen = QPen(QColor(0, 0, 255), 1)
            pen.setCosmetic(True)
            pen.setDashPattern([8.0, 4.0])  # Larger dash pattern: 8 pixels dash, 4 pixels gap
            pen.setDashOffset(self._dash_offset)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(0, 0, 255, 0)))  # Transparent fill
            painter.drawRect(self._rubber_band_rect)
            painter.restore()

    def _update_rubber_band(self):
        """Update the rubber band rectangle."""
        if self._is_rubber_banding:
            # Check if mouse button is still pressed
            if not (QApplication.mouseButtons() & Qt.MouseButton.LeftButton):
                # Mouse button released, finish selection
                self._finish_rubber_band_selection()
                return

            # Animate dash offset
            self._dash_offset += 0.5
            if self._dash_offset > 10.0:
                self._dash_offset = 0.0

            # Get current mouse position relative to the view
            current_view_pos = self.mapFromGlobal(QCursor.pos())
            current_scene_pos = self.mapToScene(current_view_pos)
            self._rubber_band_rect = QRectF(self._start_pos, current_scene_pos).normalized()
            self.viewport().update()

    def _finish_rubber_band_selection(self):
        """Finish the rubber band selection."""
        if not self._is_rubber_banding:
            return

        # Get current cursor position for final selection
        current_view_pos = self.mapFromGlobal(QCursor.pos())
        current_scene_pos = self.mapToScene(current_view_pos)
        selection_rect = QRectF(self._start_pos, current_scene_pos).normalized()

        # Select items in the rectangle
        items = self.scene().items(selection_rect, Qt.ItemSelectionMode.IntersectsItemShape)
        for item in items:
            # Check if this item has a viewmodel reference in data slot 0
            viewmodel = item.data(0)
            if viewmodel and hasattr(viewmodel, 'object_type'):
                item.setSelected(True)

        # Reset rubber band state
        self._is_rubber_banding = False
        self._rubber_band_rect = QRectF()
        self.viewport().update()
        self.setCursor(Qt.CursorShape.ArrowCursor)
        # Release mouse capture
        self.releaseMouse()
        # Stop timer
        self._update_timer.stop()
