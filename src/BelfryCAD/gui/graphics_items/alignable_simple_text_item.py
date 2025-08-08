"""
AlignableSimpleTextItem - A QGraphicsSimpleTextItem with alignment support.

This class extends QGraphicsSimpleTextItem to support text alignment relative to the item's position.
"""

from typing import Union, Optional

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QFont, QColor, QBrush, QPen
from PySide6.QtWidgets import QGraphicsSimpleTextItem, QGraphicsRectItem, QGraphicsItem


class AlignableSimpleTextItem(QGraphicsSimpleTextItem):
    """A QGraphicsSimpleTextItem with alignment support."""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self._alignment = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        self._base_pos = QPointF(0, 0) # Store the base position
        
        # Background rectangle properties
        self._show_background = False
        self._background_color = QColor(255, 255, 255, 200)  # Semi-transparent white
        self._border_color = QColor(0, 0, 0)  # Black border
        self._border_width = 1.0
        self._background_padding = 4.0  # Padding around text
        self._background_rect = None
        
        self._update_position()
    
    def alignment(self) -> Qt.AlignmentFlag:
        """Get the current text alignment."""
        return self._alignment
    
    def setAlignment(self, alignment: Qt.AlignmentFlag):
        """Set the text alignment and update the position."""
        self._alignment = alignment
        self._update_position()
    
    def setText(self, text: str):
        """Set the text and update the position."""
        super().setText(text)
        self._update_position()
        if self._show_background:
            self._update_background()
    
    def setFont(self, font: Union[QFont, str]):
        """Set the font and update the position."""
        super().setFont(font)
        self._update_position()
        if self._show_background:
            self._update_background()
    
    def setPos(self, x, y=None):
        """Set the position while maintaining alignment."""
        if isinstance(x, QPointF):
            self._base_pos = x
        else:
            if y is None:
                raise ValueError("y parameter is required when x is a float")
            self._base_pos = QPointF(x, y)
        self._update_position()
    
    def pos(self) -> QPointF:
        """Get the base position (before alignment offset)."""
        return self._base_pos
    
    def setRotation(self, angle: float):
        """Set the rotation around the alignment point."""
        super().setRotation(angle)
        self._update_position()
    
    def rotation(self) -> float:
        """Get the current rotation angle."""
        return super().rotation()
    
    def setShowBackground(self, show: bool):
        """Set whether to show the background rectangle."""
        self._show_background = show
        self._update_background()
    
    def showBackground(self) -> bool:
        """Get whether the background rectangle is shown."""
        return self._show_background
    
    def setBackgroundColor(self, color: QColor):
        """Set the background color."""
        self._background_color = color
        self._update_background()
    
    def backgroundColor(self) -> QColor:
        """Get the background color."""
        return self._background_color
    
    def setBorderColor(self, color: QColor):
        """Set the border color."""
        self._border_color = color
        self._update_background()
    
    def borderColor(self) -> QColor:
        """Get the border color."""
        return self._border_color
    
    def setBorderWidth(self, width: float):
        """Set the border width."""
        self._border_width = width
        self._update_background()
    
    def borderWidth(self) -> float:
        """Get the border width."""
        return self._border_width
    
    def setBackgroundPadding(self, padding: float):
        """Set the padding around the text."""
        self._background_padding = padding
        self._update_background()
    
    def backgroundPadding(self) -> float:
        """Get the padding around the text."""
        return self._background_padding
    
    def _update_background(self):
        """Update the background rectangle."""
        # Remove existing background rectangle
        if self._background_rect:
            if self._background_rect.scene():
                self._background_rect.scene().removeItem(self._background_rect)
            self._background_rect = None
        
        if not self._show_background:
            return
        
        # Create new background rectangle
        text_rect = self.boundingRect()
        background_rect = text_rect.adjusted(
            -self._background_padding, 
            -self._background_padding, 
            self._background_padding, 
            self._background_padding
        )
        
        # Create background as a child item that stacks behind the parent
        self._background_rect = QGraphicsRectItem(background_rect, self)
        self._background_rect.setBrush(QBrush(self._background_color))
        self._background_rect.setPen(QPen(self._border_color, self._border_width))
        
        # Set the flag to ensure background is drawn behind the text
        self._background_rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent, True)
    
    def _update_position(self):
        """Update the position based on the current alignment."""
        # Get the bounding rectangle of the text
        text_rect = self.boundingRect()
        
        # Calculate the offset based on alignment
        offset_x = 0
        offset_y = 0
        
        # Horizontal alignment
        if self._alignment & Qt.AlignmentFlag.AlignLeft:
            offset_x = 0
        elif self._alignment & Qt.AlignmentFlag.AlignHCenter:
            offset_x = -text_rect.width() / 2
        elif self._alignment & Qt.AlignmentFlag.AlignRight:
            offset_x = -text_rect.width()
        
        # Vertical alignment
        if self._alignment & Qt.AlignmentFlag.AlignTop:
            offset_y = 0
        elif self._alignment & Qt.AlignmentFlag.AlignVCenter:
            offset_y = -text_rect.height() / 2
        elif self._alignment & Qt.AlignmentFlag.AlignBottom:
            offset_y = -text_rect.height()
        
        # Set the position with offset
        super().setPos(self._base_pos.x() + offset_x, self._base_pos.y() + offset_y)
        
        # Set the transform origin to the alignment point (the base position)
        # This makes rotation happen around the alignment point
        super().setTransformOriginPoint(-offset_x, -offset_y)
        
        # Background rectangle will move automatically as a child item 