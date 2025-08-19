# -*- coding: utf-8 -*-
"""
AlignableSimpleTextItem - A QGraphicsSimpleTextItem with alignment support.

This class extends QGraphicsSimpleTextItem to support text alignment relative to the item's position.
"""

from typing import Union, Optional

from PySide6.QtCore import Qt, QPointF, QRectF, QPoint
from PySide6.QtGui import (
    QFont, QColor, QBrush, QPen, QTransform,
    QFontMetrics, QPainterPath
)
from PySide6.QtWidgets import QGraphicsItem


class AlignableSimpleTextItem(QGraphicsItem):
    """A QGraphicsItem with text and alignment support."""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(parent)
        self._text = text
        self._font = QFont("Arial", 10)
        self._font.setPointSize(10)
        self._brush = QBrush(QColor(0, 0, 0))  # Default black text
        self._pen = QPen(QColor(0, 0, 0), 0.0)  # Default black outline
        self._alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        self._base_pos = QPointF(0, 0)  # Store the base position
        self._rotation = 0.0
        
        # Set up graphics item flags
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)

        self._bounds_rect = QRectF(0, 0, 0, 0)

        self._recalculate_bounds()

    def _recalculate_bounds(self):
        dpi = 128
        if self.scene() and self.scene().views():
            dpi = self.scene().views()[0].physicalDpiX()
        dpcm = dpi / 2.54

        T = QTransform()
        T.scale(1.0/dpcm, -1.0/dpcm)
        T.translate(self._base_pos.x()*dpcm, -self._base_pos.y()*dpcm)
        self.resetTransform()
        self.setTransform(T)

        """Recalculate the bounding rectangle of the text."""
        metrics = QFontMetrics(self._font)
        text_rect = QRectF(metrics.boundingRect(self._text))
        width = text_rect.width()
        height = text_rect.height()
        
        # Calculate the offset based on alignment
        offset_x = 0
        offset_y = 0
        
        # Horizontal alignment
        if self._alignment & Qt.AlignmentFlag.AlignLeft:
            offset_x = width / 2
        elif self._alignment & Qt.AlignmentFlag.AlignHCenter:
            offset_x = 0
        elif self._alignment & Qt.AlignmentFlag.AlignRight:
            offset_x = -width / 2
        
        # Vertical alignment
        if self._alignment & Qt.AlignmentFlag.AlignTop:
            offset_y = height / 2
        elif self._alignment & Qt.AlignmentFlag.AlignVCenter:
            offset_y = 0
        elif self._alignment & Qt.AlignmentFlag.AlignBottom:
            offset_y = -height / 2
        
        margin = 1
        dx = (text_rect.left() + text_rect.right()) / 2.0 - offset_x
        dy = (text_rect.top() + text_rect.bottom()) / 2.0 - offset_y
        self._bounds_rect = QRectF(
            text_rect.left() - dx - margin,
            text_rect.top() - dy - margin,
            text_rect.width() + 2 * margin,
            text_rect.height()
        )

    def boundingRect(self):
        """Return the bounding rectangle of the text."""
        return self._bounds_rect
    
    def shape(self):
        """Return the shape for hit testing."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path
    
    def paint(self, painter, option, widget=None):
        """Paint the text item."""
        painter.save()
        
        bounds_rect = self.boundingRect()
        
        # Draw the background rectangle
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QPen(QColor(255, 255, 255), 0.0))
        painter.drawRect(bounds_rect)
        painter.restore()
        
        painter.save()
        # Apply rotation
        if self._rotation != 0:
            painter.rotate(self._rotation)
        
        # Set font and colors
        painter.setFont(self._font)
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        
        # Draw the text
        painter.drawText(
            bounds_rect, Qt.AlignmentFlag.AlignCenter, self._text)
        
        painter.restore()
    
    def alignment(self) -> Qt.AlignmentFlag:
        """Get the current text alignment."""
        return self._alignment
    
    def setAlignment(self, alignment: Qt.AlignmentFlag):
        """Set the text alignment and update the position."""
        self._recalculate_bounds()
        self._alignment = alignment
    
    def setText(self, text: str):
        """Set the text and update the position."""
        self._text = text
        self._recalculate_bounds()
        self.update()  # Trigger repaint
    
    def font(self) -> QFont:
        """Get the current font."""
        return self._font
    
    def setFont(self, font: Union[QFont, str]):
        """Set the font and update the position."""
        if isinstance(font, str):
            self._font = QFont(font, 10)
        else:
            self._font = font
        self._recalculate_bounds()
        self.update()  # Trigger repaint
    
    def pos(self) -> QPointF:
        """Get the base position (before alignment offset)."""
        return self._base_pos
    
    def setPos(self, x, y=None):
        """Set the position while maintaining alignment."""
        if isinstance(x, (QPointF, QPoint)):
            self._base_pos = QPointF(x)
        else:
            if y is None:
                raise ValueError("y parameter is required when x is a float")
            self._base_pos = QPointF(x, y)
        self._recalculate_bounds()
    
    def brush(self) -> QBrush:
        """Get the current brush."""
        return self._brush
    
    def setBrush(self, brush: QBrush):
        """Set the brush for text color."""
        self._brush = brush
        self.update()
    
    def pen(self) -> QPen:
        """Get the current pen."""
        return self._pen
    
    def setPen(self, pen: QPen):
        """Set the pen for text outline."""
        self._pen = pen
        self._recalculate_bounds()
        self.update()
    
    def rotation(self) -> float:
        """Get the current rotation angle."""
        return self._rotation
    
    def setRotation(self, angle: float):
        """Set the rotation around the alignment point."""
        self._rotation = angle
        self._recalculate_bounds()
        self.update()
    
