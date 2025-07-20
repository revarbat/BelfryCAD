import math

from PySide6.QtWidgets import QGraphicsItem, QDialog
from PySide6.QtCore import QRectF, QLineF, Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPainter, QBrush, QFont

from ...grid_info import GridInfo, UnitSelectionDialog


class GridBackground(QGraphicsItem):
    """Custom grid background for the scene."""
    def __init__(self, grid_info: GridInfo):
        super().__init__()
        self.grid_info = grid_info
        self.setZValue(-10)  # Draw behind other items
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)

    def boundingRect(self):
        """Return the bounding rectangle of the grid."""
        return QRectF(-5000, -5000, 10000, 10000)

    def paint(self, painter, option, widget=None):
        """Draw the grid."""
        widget = self.scene().views()[0]
        viewport_rect = widget.viewport().rect()
        visible_scene_rect = widget.mapToScene(viewport_rect).boundingRect()
        scaling = widget.transform().m11()
        spacings, label_spacing = self.grid_info.get_relevant_spacings(scaling)
        spacing = spacings[-1]

        # Draw grid lines
        x0 = visible_scene_rect.left()
        x1 = visible_scene_rect.right()
        y0 = visible_scene_rect.top()
        y1 = visible_scene_rect.bottom()
        width = visible_scene_rect.width()
        height = visible_scene_rect.height()
        backing_width = 40 / scaling
        start_x = round(x0 / spacing) * spacing
        start_y = y0 // spacing * spacing

        steps = int(width / spacing + 0.5)
        for i in range(steps + 2):
            x = start_x + i * spacing
            level = 0
            for space in spacings:
                if abs(x / space - round(x / space)) > 1e-6:
                    level += 1
            line_color = self.grid_info.grid_line_color(level)
            line_width = 2.0 * math.pow(0.75, level)
            if line_width < 1.0:
                line_width = 1.0
            pen = QPen(QColor(line_color))
            pen.setWidthF(line_width)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.drawLine(QLineF(x, y0, x, y1))

        steps = int(height / spacing + 0.5)
        for i in range(steps + 2):
            y = start_y + i * spacing
            level = 0
            for space in spacings:
                if abs(y / space - round(y / space)) > 1e-6:
                    level += 1
            line_color = self.grid_info.grid_line_color(level)
            line_width = 2.0 * math.pow(0.75, level)
            if line_width < 1.0:
                line_width = 1.0
            pen = QPen(QColor(line_color))
            pen.setWidthF(line_width)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.drawLine(QLineF(x0, y, x1, y))


class RulersForeground(QGraphicsItem):
    """Custom grid background for the scene."""
    def __init__(self, grid_info: GridInfo):
        super().__init__()
        self.grid_info = grid_info
        self.setZValue(99999)  # Draw above other items
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemUsesExtendedStyleOption, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        """Return the bounding rectangle of the grid."""
        return QRectF(-5000, -5000, 10000, 10000)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click events to change grid units."""
        # Check if the click is in the unit label area
        widget = self.scene().views()[0]
        viewport_rect = widget.viewport().rect()
        visible_scene_rect = widget.mapToScene(viewport_rect).boundingRect()
        scaling = widget.transform().m11()
        backing_width = 40 / scaling

        x0 = visible_scene_rect.left()
        y1 = visible_scene_rect.bottom()

        # Unit label area (corner area)
        unit_label_rect = QRectF(
            x0, y1 - backing_width,
            backing_width, backing_width
        )

        if unit_label_rect.contains(event.pos()):
            # Show unit selection dialog
            dialog = UnitSelectionDialog(self.grid_info.units, widget)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_unit = dialog.get_selected_unit()
                if new_unit != self.grid_info.units:
                    self.grid_info.units = new_unit
                    # Update both grid and rulers
                    self.update()
                    # Find and update the grid background
                    for item in self.scene().items():
                        if isinstance(item, GridBackground):
                            item.update()
                            break
                    
                    # Notify the scene to refresh gear items
                    scene = self.scene()
                    if scene and hasattr(scene, 'refresh_gear_items_for_unit_change'):
                        scene.refresh_gear_items_for_unit_change()

    @staticmethod
    def draw_label(
            painter: QPainter,
            x: float, y: float,
            label: str,
            is_horizontal: bool = False,
            is_clickable: bool = False
    ):
        if is_horizontal:
            align = (
                Qt.AlignmentFlag.AlignBottom |
                Qt.AlignmentFlag.AlignHCenter
            )
            box = QRectF(-20, 0, 40, 30)
        else:
            align = (
                Qt.AlignmentFlag.AlignRight |
                Qt.AlignmentFlag.AlignVCenter
            )
            box = QRectF(0, -15, 30, 30)
        painter.save()
        scale = painter.transform().m11()
        font = QFont("Arial", 10)
        font.setPointSizeF(12.0)
        painter.setBrush(QBrush(QColor("white")))
        painter.setFont(font)
        painter.translate(x, y)
        painter.scale(1.0 / scale, -1.0 / scale)

        # Add subtle border for clickable labels
        if is_clickable:
            painter.setPen(QPen(QColor("lightgray"), 1.0))
            painter.drawRect(box.adjusted(-2, -2, 2, 2))

        painter.setPen(QPen(QColor("white"), 2.0))
        painter.drawText(box, align, label)
        painter.setPen(QPen(QColor("black"), 1.0))
        painter.drawText(box, align, label)
        painter.scale(scale, -scale)
        painter.translate(-x, -y)
        painter.restore()

    def paint(self, painter, option, widget=None):
        """Draw the grid."""
        widget = self.scene().views()[0]
        viewport_rect = widget.viewport().rect()
        visible_scene_rect = widget.mapToScene(viewport_rect).boundingRect()
        scaling = widget.transform().m11()
        spacings, label_spacing = self.grid_info.get_relevant_spacings(scaling)
        spacing = spacings[-1]

        # Draw grid lines
        x0 = visible_scene_rect.left()
        x1 = visible_scene_rect.right()
        y0 = visible_scene_rect.top()
        y1 = visible_scene_rect.bottom()
        width = visible_scene_rect.width()
        height = visible_scene_rect.height()
        backing_width = 40 / scaling
        start_x = round((x0 + backing_width) / spacing) * spacing
        start_y = y0 // spacing * spacing
        end_y = y1 - backing_width

        # Draw ruler backing
        painter.save()
        pen_white = QPen(QColor("white"), 1.0)
        pen_white.setCosmetic(True)
        brush = QBrush(QColor("white"))
        painter.setPen(pen_white)
        painter.setBrush(brush)
        painter.drawRect(QRectF(x0, y1 - backing_width, x1 - x0, backing_width))
        painter.drawRect(QRectF(x0, y0, backing_width - 1/scaling, y1 - y0))
        painter.restore()

        # Draw horizontal labels
        steps = int(width / spacing + 0.5)
        for i in range(steps + 1):
            x = start_x + i * spacing
            if abs(x / label_spacing - round(x / label_spacing)) <= 1e-6:
                label = self.grid_info.format_label(x).strip()
                RulersForeground.draw_label(
                    painter, x, y1, label, is_horizontal=True)

        # Draw vertical labels
        steps = int((end_y - start_y) / spacing + 0.5)
        end_y = y0 + height - 40 / scaling
        for i in range(steps + 1):
            y = start_y + i * spacing
            if abs(y / label_spacing - round(y / label_spacing)) <= 1e-6:
                if y < end_y:
                    label = self.grid_info.format_label(y).strip()
                    RulersForeground.draw_label(
                        painter, x0, y, label, is_horizontal=False)

        # Clear corner background
        painter.save()
        pen_white = QPen(QColor("white"), 1.0)
        pen_white.setCosmetic(True)
        brush = QBrush(QColor("white"))
        painter.setPen(pen_white)
        painter.setBrush(brush)
        painter.drawRect(
            QRectF(x0, y1 - backing_width,
                   backing_width, backing_width))
        painter.restore()

        # Draw ruler border
        painter.save()
        pen_black = QPen(QColor("black"), 1.0)
        pen_black.setCosmetic(True)
        painter.setPen(pen_black)
        painter.drawLine(QLineF(x0, y1 - backing_width, x1, y1 - backing_width))
        painter.drawLine(QLineF(x0 + backing_width, y0, x0 + backing_width, y1))
        painter.restore()


        # Draw unit label in corner
        painter.save()
        pen_black = QPen(QColor("black"), 1.0)
        pen_black.setCosmetic(True)
        painter.setPen(pen_black)
        RulersForeground.draw_label(
            painter, x0, y1 - backing_width/2,
            self.grid_info.unit_label, is_horizontal=False, is_clickable=True)
        painter.restore()


class SnapCursorItem(QGraphicsItem):
    """Custom grid cursor for the scene."""
    def __init__(self):
        super().__init__()
        self.control_size = 7
        self.setZValue(10001)  # Draw above other items
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsFocusable, False)
    
    def _get_control_size_in_scene_coords(self, painter):
        """Get control point size in scene coordinates based on current zoom level."""
        pixel_size = self.control_size
        scale = painter.transform().m11()
        return pixel_size / scale

    def boundingRect(self):
        """Return bounding rectangle for hit testing."""
        # Get the current scale from the scene to make bounding rect scale independent
        scene = self.scene()
        if scene and scene.views():
            # Get the first view's transform to determine current scale
            view = scene.views()[0]
            scale = view.transform().m11()
            # Convert pixel size to scene coordinates
            control_size = float(self.control_size) / scale
        else:
            # Fallback to a reasonable size if no scene/view available
            control_size = 0.3
        
        control_padding = control_size / 2
        return QRectF(-control_padding, -control_padding, control_size, control_size)


    def paint(self, painter, option, widget=None):
        """Paint the snap cursor as a red X-shaped cross."""
        painter.save()

        # Get the size of the cross in scene coordinates
        cross_size = self._get_control_size_in_scene_coords(painter)
        half_size = cross_size / 2

        # Set up red pen with linewidth 2 and cosmetic drawing
        cross_pen = QPen(QColor(255, 0, 0), 3.0)
        cross_pen.setCosmetic(True)
        painter.setPen(cross_pen)
        painter.setBrush(QBrush())  # No fill

        # Draw the X-shaped cross
        # Diagonal line from top-left to bottom-right
        painter.drawLine(
            QPointF(-half_size, -half_size),
            QPointF(half_size, half_size)
        )
        
        # Diagonal line from top-right to bottom-left
        painter.drawLine(
            QPointF(half_size, -half_size),
            QPointF(-half_size, half_size)
        )

        painter.restore()


