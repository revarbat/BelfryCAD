"""
CadArcGraphicsItem - A graphics item for drawing arcs with optional arrowheads.
"""

import math
from enum import Enum
from typing import Optional, List
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import (
    Qt, QPen, QColor, QBrush,
    QPainterPath, QPainterPathStroker, QPolygonF
)
from PySide6.QtWidgets import (
    QGraphicsItem, QAbstractGraphicsShapeItem,
    QGraphicsPathItem, QGraphicsPolygonItem, QApplication
)


class CadArcArrowheadEndcaps(Enum):
    NONE = 0
    START = 1
    END = 2
    BOTH = 3


class CadArcGraphicsItem(QAbstractGraphicsShapeItem):
    """A graphics item for drawing arcs with optional arrowheads."""

    def __init__(
            self,
            center_point: QPointF,
            radius: float,
            start_angle: float,
            span_angle: float,
            arrowheads: CadArcArrowheadEndcaps = CadArcArrowheadEndcaps.NONE,
            parent: Optional[QGraphicsItem] = None,
            pen: QPen = QPen(QColor(0, 0, 0), 1.0)
    ):
        super().__init__(parent)
        
        # Store arc parameters
        self._center_point = center_point
        self._radius = radius
        self._start_angle = start_angle
        self._span_angle = span_angle
        
        # Styling properties - will be set via setPen()
        self._arrowheads = arrowheads
        
        # Graphics items
        self._arc_item = None
        self._arrowhead_items = []
        
        # Set up the graphics item
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, True)
        
        # Ensure the item is visible
        self.setVisible(True)
        self.setPen(pen)
        
        # Create the arc
        self._create_arc()

    def _create_arc(self):
        """Create the arc graphics item."""
        # Calculate end angle
        start_angle = self._start_angle
        end_angle = start_angle + self._span_angle
        
        # Convert angles to radians
        start_rad = math.radians(self._start_angle)
        end_rad = math.radians(end_angle)
        
        # Calculate start and end points
        start_point = QPointF(
            self._center_point.x() + math.cos(start_rad) * self._radius,
            self._center_point.y() + math.sin(start_rad) * self._radius
        )
        end_point = QPointF(
            self._center_point.x() + math.cos(end_rad) * self._radius,
            self._center_point.y() + math.sin(end_rad) * self._radius
        )
        
        # Create arc path
        arc_path = QPainterPath()
        arc_path.moveTo(start_point)
        
        # Normalize span angle to -180 to 180 for Qt's arcTo
        span_angle = self._span_angle
        while span_angle > 360:
            span_angle -= 360
        while span_angle < -360:
            span_angle += 360
        
        scale = self.transform().m11()
        circum = 2 * math.pi * self._radius
        shy_span = 10 * scale/ circum * 360
        trimmed_span_angle = span_angle
        trimmed_start_angle = start_angle
        if self._arrowheads in [CadArcArrowheadEndcaps.START, CadArcArrowheadEndcaps.BOTH]:
            trimmed_span_angle -= math.copysign(shy_span, span_angle)
            trimmed_start_angle += math.copysign(shy_span, span_angle)
            trimmed_start_rad = math.radians(trimmed_start_angle)
            trimmed_start_point = QPointF(
                self._center_point.x() + math.cos(trimmed_start_rad) * self._radius,
                self._center_point.y() + math.sin(trimmed_start_rad) * self._radius
            )
            arc_path.moveTo(trimmed_start_point)
        if self._arrowheads in [CadArcArrowheadEndcaps.END, CadArcArrowheadEndcaps.BOTH]:
            trimmed_span_angle -= math.copysign(shy_span, span_angle)

        # Draw the arc
        arc_path.arcTo(
            self._center_point.x() - self._radius,
            self._center_point.y() - self._radius,
            self._radius * 2,
            self._radius * 2,
            -trimmed_start_angle,
            -trimmed_span_angle  # Negative for clockwise
        )
        
        # Create arc graphics item
        self._arc_item = QGraphicsPathItem(arc_path, self)
        # Use the pen from the parent class (QAbstractGraphicsShapeItem)
        self._arc_item.setPen(self.pen())
        
        # Create arrowheads if requested
        if self._arrowheads != CadArcArrowheadEndcaps.NONE:
            self._create_arrowheads(start_point, end_point, start_rad, end_rad, span_angle)

    def _create_arrowheads(self, start_point: QPointF, end_point: QPointF, 
                          start_rad: float, end_rad: float, span_angle: float):
        """Create arrowheads at the start and end of the arc."""
        # Clear existing arrowheads
        for item in self._arrowhead_items:
            if item.scene():
                item.scene().removeItem(item)
        self._arrowhead_items.clear()
        
        scale = self.transform().m11()
        shy_span = 10 * scale / self._radius
        arrow_spin = math.pi/2 - shy_span / 2
        if span_angle < 0:
            arrow_spin = -arrow_spin

        if self._arrowheads in [CadArcArrowheadEndcaps.START, CadArcArrowheadEndcaps.BOTH]:
            # Create start arrowhead (pointing outward from center)
            start_arrow_vector = QPointF(
                math.cos(start_rad-arrow_spin) * 10,
                math.sin(start_rad-arrow_spin) * 10
            )
            self._create_arrowhead(start_point, start_arrow_vector)
        
        if self._arrowheads in [CadArcArrowheadEndcaps.END, CadArcArrowheadEndcaps.BOTH]:
            # Create end arrowhead (pointing outward from center)
            end_arrow_vector = QPointF(
                math.cos(end_rad+arrow_spin) * 10,
                math.sin(end_rad+arrow_spin) * 10
            )
            self._create_arrowhead(end_point, end_arrow_vector)

    def _create_arrowhead(self, arrow_tip: QPointF, arrow_vector: QPointF):
        """Create an arrowhead at the specified position."""
        arrow_length = math.sqrt(arrow_vector.x()**2 + arrow_vector.y()**2)
        if arrow_length == 0:
            return
        
        arrow_unit = arrow_vector * (1.0 / arrow_length)
        arrow_pvec = QPointF(-arrow_unit.y(), arrow_unit.x())
        
        # Create arrowhead polygon
        pen_width = self.pen().widthF()
        poly = QPolygonF([
            arrow_tip,
            arrow_tip + arrow_pvec * (pen_width / 2 + arrow_length / 4) - arrow_vector,
            arrow_tip - arrow_pvec * (pen_width / 2 + arrow_length / 4) - arrow_vector
        ])
        
        arrowhead = QGraphicsPolygonItem(poly, self)
        # Use the pen color from the parent class
        pen = QPen(self.pen().color(), 0)
        brush = QBrush(self.pen().color())
        arrowhead.setPen(pen)
        arrowhead.setBrush(brush)
        self._arrowhead_items.append(arrowhead)

    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of the arc."""
        if not self._arc_item:
            return QRectF()
        
        # Get the bounding rect of the arc
        rect = self._arc_item.boundingRect()
        
        # Include arrowheads if they exist
        for arrowhead in self._arrowhead_items:
            rect = rect.united(arrowhead.boundingRect())
        
        return rect

    def shape(self) -> QPainterPath:
        """Return the shape for hit testing."""
        if not self._arc_item:
            return QPainterPath()
        
        # Combine arc and arrowhead shapes
        shape = self._arc_item.shape()
        
        for arrowhead in self._arrowhead_items:
            shape.addPath(arrowhead.shape())
        
        stroker = QPainterPathStroker()
        stroker.setWidth(self.pen().widthF())
        stroker.setCapStyle(self.pen().capStyle())
        stroker.setJoinStyle(self.pen().joinStyle())
        shape = stroker.createStroke(shape)

        return shape

    def paint(self, painter, option, widget=None):
        """Paint the arc (delegated to child items) and selection indication."""
        # The actual painting is done by the child QGraphicsPathItem and QGraphicsPolygonItem
        # But we need to draw selection indication if this item is selected
        
        if self.isSelected():
            # Draw selection indication
            # Create selection pen using Qt's standard selection color
            # standard_selection_color = QApplication.palette().highlight().color()
            selection_pen = QPen(Qt.GlobalColor.red, 3.0)
            selection_pen.setStyle(Qt.PenStyle.DashLine)
            selection_pen.setCosmetic(True)
            
            # Draw selection rectangle around the bounding rect
            painter.setPen(selection_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            path = self.shape()
            painter.drawPath(path)

    # Property setters
    def setCenterPoint(self, center_point: QPointF):
        """Set the center point of the arc."""
        self._center_point = center_point
        self._recreate_arc()

    def setRadius(self, radius: float):
        """Set the radius of the arc."""
        self._radius = radius
        self._recreate_arc()

    def setStartAngle(self, start_angle: float):
        """Set the start angle of the arc in degrees."""
        self._start_angle = start_angle
        self._recreate_arc()

    def setSpanAngle(self, span_angle: float):
        """Set the span angle of the arc in degrees."""
        self._span_angle = span_angle
        self._recreate_arc()

    def setPen(self, pen):
        """Set the pen for the arc."""
        super().setPen(pen)
        self._update_style()

    def setArrowheads(self, arrowheads: CadArcArrowheadEndcaps):
        """Set the arrowheads of the arc."""
        self._arrowheads = arrowheads
        self._recreate_arc()

    def _recreate_arc(self):
        """Recreate the arc with current parameters."""
        # Remove existing items
        if self._arc_item:
            if self._arc_item.scene():
                self._arc_item.scene().removeItem(self._arc_item)
            self._arc_item = None
        
        for item in self._arrowhead_items:
            if item.scene():
                item.scene().removeItem(item)
        self._arrowhead_items.clear()
        
        # Create new arc
        self._create_arc()
        self.prepareGeometryChange()
        self.update()

    def _update_style(self):
        """Update the style of existing items."""
        if self._arc_item:
            self._arc_item.setPen(self.pen())
        
        for arrowhead in self._arrowhead_items:
            pen = QPen(self.pen().color(), 0)
            brush = QBrush(self.pen().color())
            arrowhead.setPen(pen)
            arrowhead.setBrush(brush)
        
        self.update()

    # Property getters
    @property
    def center_point(self) -> QPointF:
        """Get the center point of the arc."""
        return self._center_point

    @property
    def radius(self) -> float:
        """Get the radius of the arc."""
        return self._radius

    @property
    def start_angle(self) -> float:
        """Get the start angle of the arc in degrees."""
        return self._start_angle

    @property
    def span_angle(self) -> float:
        """Get the span angle of the arc in degrees."""
        return self._span_angle

    @property
    def end_angle(self) -> float:
        """Get the end angle of the arc in degrees."""
        return self._start_angle + self._span_angle 

    @property
    def arrowheads(self) -> CadArcArrowheadEndcaps:
        """Get the arrowheads of the arc."""
        return self._arrowheads
    