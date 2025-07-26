"""
Base CAD item class for graphics items with animated selection and control points.
"""

from typing import List, Optional, TYPE_CHECKING
from PySide6.QtWidgets import QGraphicsItem, QGraphicsDropShadowEffect
from PySide6.QtCore import QPointF, QEvent
from PySide6.QtGui import QPen, QColor, QBrush, Qt
from .control_points import ControlPoint

if TYPE_CHECKING:
    from ...main_window import MainWindow
    from ...grid_info import GridInfo


class CadItem(QGraphicsItem):
    """Base class for all CAD graphics items."""

    def __init__(self,
            main_window: 'MainWindow',
            color: QColor = QColor(0, 0, 0),
            line_width: Optional[float] = 1.0):
        super().__init__()
        self._color = color
        self._line_width = line_width
        self._main_window = main_window
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setHandlesChildEvents(False)

        # Selection blur effect
        self._selection_blur_effect = None

        # Control point items (children)
        self._control_point_items = []
        
        # Track selection state for detecting changes
        self._was_singly_selected = False
        
        # Control points are now managed by the scene, not created automatically
        # QTimer.singleShot(0, self._create_control_points_impl)

    def __del__(self):
        """Destructor to clean up blur effect."""
        try:
            if hasattr(self, '_selection_blur_effect') and self._selection_blur_effect:
                self.setGraphicsEffect(None) # type: ignore
                self._selection_blur_effect = None
        except:
            pass

    def itemChange(self, change, value):
        """Handle item state changes using Qt's built-in system."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value:  # Becoming selected
                self._apply_selection_blur()
                # Check selection state (control points managed by scene)
                self._check_selection_state()
            else:  # Becoming deselected
                self._remove_selection_blur()
                self._was_singly_selected = False
        elif change == QGraphicsItem.GraphicsItemChange.ItemSceneChange:
            # Item is being removed from scene
            if value is None:  # Being removed from scene
                self._remove_selection_blur()
                self._was_singly_selected = False
        elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Control points are managed by the scene, which will update them as needed
            pass
        return super().itemChange(change, value)

    def _is_singly_selected(self):
        """Check if this item is the only selected item in the scene."""
        if not self.scene():
            return False
        
        # Get all selected items in the scene
        selected_items = [item for item in self.scene().items() 
                         if hasattr(item, 'isSelected') and item.isSelected()]
        
        # Return True if this item is the only selected item
        return len(selected_items) == 1 and self in selected_items

    def _check_selection_state(self):
        """Check if control points should be shown or hidden based on selection state."""
        # Control points are now managed by the scene, not by individual CAD items
        # The scene will handle showing/hiding control points based on selection
        if self.isSelected() and self._is_singly_selected():
            # Single selection - control points will be shown by the scene
            self._was_singly_selected = True
        else:
            # Not selected or multiple selection - control points will be hidden by the scene
            self._was_singly_selected = False

    def _apply_selection_blur(self):
        """Apply blue blur effect when item is selected."""
        if not self._selection_blur_effect:
            self._selection_blur_effect = QGraphicsDropShadowEffect()
            self._selection_blur_effect.setBlurRadius(8.0)
            self._selection_blur_effect.setColor(QColor(255, 0, 0, 255))  # Blue with alpha
            self._selection_blur_effect.setOffset(0, 0)
            self.setGraphicsEffect(self._selection_blur_effect)

    def _remove_selection_blur(self):
        """Remove blur effect when item is deselected."""
        if self._selection_blur_effect:
            self.setGraphicsEffect(None) # type: ignore
            self._selection_blur_effect = None

    def paint(self, painter, option, widget=None):
        """Main paint method that handles selection and calls paint_item."""
        # Draw the main item normally (blur effect is handled by graphics effect)
        self.paint_item(painter, option, widget)

    def paint_item_with_selection(self, painter, option, widget=None):
        """Paint the item with selection effect. Override in subclasses for custom selection behavior."""
        # Default behavior: call paint_item normally (blur effect is handled by graphics effect)
        self.paint_item(painter, option, widget)

    def paint_item_with_color(self, painter, option, widget=None, color=None):
        """Paint the item with a specific color. Override in subclasses."""
        # Default implementation: call paint_item
        self.paint_item(painter, option, widget)

    def _get_line_width(self):
        """Get the line width for this CAD item. Override in subclasses."""
        return 1.0  # Default line width

    def paint_item(self, painter, option, widget=None):
        """Override this method to paint the specific CAD item."""
        pass

    def createControlPoints(self):
        """Show control points for this CAD item. Called when item is singly selected."""
        # Control points are now managed by the scene, not by the CAD item
        # Clean up any old control points that might exist
        self.destroyControlPoints()
        pass

    def destroyControlPoints(self):
        """Destroy all control points for this CAD item."""
        if not hasattr(self, '_control_point_items'):
            return

        for item in self._control_point_items:
            try:
                if item:
                    item.getter = None
                    item.setter = None
                    item.setParentItem(None)
            except (RuntimeError, AttributeError, TypeError):
                pass

        self._control_point_items.clear()

    def updateControlPoints(self):
        """Update control point positions and values."""
        if not hasattr(self, '_control_point_items') or not self._control_point_items:
            return

        # Call the subclass implementation to update control points
        try:
            self.updateControls()
        except Exception as e:
            print(f"Error updating control points: {e}")

    def createControls(self):
        """Override to create and return a list of control points."""
        control_points = []
        # Call the subclass implementation
        try:
            control_points = self._create_controls_impl()
            if control_points:
                # Store the control points in the expected attribute
                self._control_point_items.extend(control_points)
                # Hide control points by default
                for cp in control_points:
                    if cp:
                        cp.setVisible(False)
        except (RuntimeError, AttributeError, TypeError):
            pass
        return control_points

    def _create_controls_impl(self):
        """Override to create and return a list of control points."""
        return []

    def _create_control_points_impl(self):
        """Create control points immediately after instantiation."""
        try:
            control_points = self.createControls()
            if control_points:
                self._control_point_items.extend(control_points)
                # Hide control points by default
                self.hideControls()
        except (RuntimeError, AttributeError, TypeError):
            pass

    def updateControls(self):
        """Override to update control point positions and values."""
        pass

    def getControlPoints(self, exclude_cps: Optional[List['ControlPoint']] = None) -> List[QPointF]:
        """
        Return a list of QPointF positions where control points should be positioned.
        This method should return the same positions that updateControls() sets
        for the control points, but without creating the actual control point objects.
        ControlDatums should not be included in this list.
        
        Args:
            exclude_cps: List of ControlPoint objects to exclude from the result.
                        Control points associated with these objects will be excluded.
        
        Returns:
            List of QPointF positions for control points (excluding ControlDatums and excluded points)
        """
        # Default implementation returns empty list
        # Subclasses should override this method
        return []
    
    def _should_exclude_control_point(self, cp_index: int, exclude_cps: Optional[List['ControlPoint']] = None) -> bool:
        """
        Helper method to determine if a control point at the given index should be excluded.
        
        Args:
            cp_index: Index of the control point to check
            exclude_cps: List of ControlPoint objects to exclude from the result.
        
        Returns:
            True if the control point should be excluded, False otherwise
        """
        if not exclude_cps:
            return False
        
        # Get the control point objects for this CAD item
        control_point_objects = self._get_control_point_objects()
        
        if cp_index < len(control_point_objects):
            cp_object = control_point_objects[cp_index]
            return cp_object in exclude_cps
        
        return False
    
    def _get_control_point_objects(self) -> List['ControlPoint']:
        """
        Get the list of ControlPoint objects for this CAD item.
        This method should be overridden by subclasses to provide the actual control point objects.
        
        Returns:
            List of ControlPoint objects for this CAD item
        """
        # Default implementation returns empty list
        # Subclasses should override this method
        return []

    def hideControls(self):
        """Hide all control points and control datums for this CAD item."""
        # Control points are now managed by the scene, not by the CAD item
        # Clean up any old control points that might exist
        self.destroyControlPoints()
        pass

    def showControls(self):
        """Show all control points and control datums for this CAD item."""
        # Update ControlDatum precision to match current scene precision
        precision = self.main_window.cad_scene.get_precision()
        self.update_control_datums_precision(precision)

    def update_control_datums_precision(self, new_precision: int):
        """Update precision for all ControlDatums in this CAD item."""
        for control_item in self._control_point_items:
            if hasattr(control_item, 'update_precision'):
                control_item.update_precision(new_precision)

    def moveBy(self, dx, dy):
        """Move all underlying points by the specified offset. If the subclass has a 'points' property, move all points. Otherwise, must be overridden by subclass."""
        if hasattr(self, 'points') and hasattr(self, 'points'):
            pts = self.points
            # Support both list and tuple of points
            try:
                new_pts = [QPointF(pt.x() + dx, pt.y() + dy) for pt in pts]
                self.points = new_pts
                self.update()
            except Exception:
                raise NotImplementedError("Subclass must implement moveBy or provide a points property.")
        else:
            raise NotImplementedError("Subclass must implement moveBy or provide a points property.")

    def sceneEvent(self, event):
        """Handle scene events to detect selection changes."""
        if event.type() == QEvent.Type.GraphicsSceneMouseRelease:
            # Check selection state after mouse release (when selection might have changed)
            if self.isSelected():
                self._check_selection_state()
        return super().sceneEvent(event)
    
    def get_dashed_construction_pen(self) -> QPen:
        """Get a dashed construction pen with #7f7f7f color, 2.0 line width, and cosmetic style."""
        pen = QPen(QColor(0x7f, 0x7f, 0x7f))  # #7f7f7f color
        pen.setWidthF(2.0)
        pen.setCosmetic(True)
        pen.setDashPattern([3.0, 3.0])
        return pen

    def get_solid_construction_pen(self) -> QPen:
        """Get a solid construction pen with #7f7f7f color, 2.0 line width, and cosmetic style."""
        pen = QPen(QColor(0x7f, 0x7f, 0x7f))  # #7f7f7f color
        pen.setWidthF(2.0)
        pen.setCosmetic(True)
        pen.setStyle(Qt.PenStyle.SolidLine)
        return pen

    def get_construction_brush(self) -> QBrush:
        """Get a construction brush with #7f7f7f color."""
        return QBrush(QColor(0x7f, 0x7f, 0x7f))

    def draw_arrow(self, painter, point, angle, length, width):
        """Draw an arrow at the given point with the given angle and length."""
        painter.save()
        painter.translate(point)
        painter.rotate(angle)
        painter.drawLine(QPointF(0, 0), QPointF(length-2.5*width, 0))
        painter.drawPolygon([
            QPointF(length, 0),
            QPointF(length - 3.5 * width, 0.75 * width),
            QPointF(length - 3.5 * width, -0.75 * width),
            QPointF(length, 0)
        ])
        painter.restore()
    
    def draw_radius_arrow(self, painter, point, angle, radius, line_width):
        if not self._is_singly_selected():
            return
        painter.save()
        rad_len = radius - line_width/2
        painter.setPen(self.get_solid_construction_pen())
        painter.setBrush(self.get_construction_brush())
        scale = painter.transform().m11()
        arrow_w = 4.0 / scale
        self.draw_arrow(painter, point, angle, rad_len, arrow_w)
        painter.restore()

    def draw_diameter_arrow(self, painter, point, angle, diameter, line_width):
        if not self._is_singly_selected():
            return
        painter.save()
        radius = diameter/2
        rad_len = radius - line_width/2
        painter.setPen(self.get_solid_construction_pen())
        painter.setBrush(self.get_construction_brush())
        scale = painter.transform().m11()
        arrow_w = 4.0 / scale
        self.draw_arrow(painter, point, angle, rad_len, arrow_w)
        self.draw_arrow(painter, point, angle+180, rad_len, arrow_w)
        painter.restore()

    def draw_center_cross(self, painter, point):
        """Draw a center cross at the given point."""
        if not self._is_singly_selected():
            return
        painter.save()
        scale = painter.transform().m11()
        cross_rad = 60.0 / scale
        painter.translate(point)
        pen = self.get_dashed_construction_pen()
        pen.setDashPattern([10.0, 2.0, 2.0, 2.0])
        painter.setPen(pen)
        painter.drawLine(QPointF(0, 0), QPointF(cross_rad, 0))
        painter.drawLine(QPointF(0, 0), QPointF(0, cross_rad))
        painter.drawLine(QPointF(0, 0), QPointF(-cross_rad, 0))
        painter.drawLine(QPointF(0, 0), QPointF(0, -cross_rad))
        painter.restore()
    
    def draw_construction_circle(self, painter, point, radius):
        """Draw a construction circle at the given point."""
        if not self._is_singly_selected():
            return
        painter.save()
        painter.translate(point)
        painter.setPen(self.get_dashed_construction_pen())
        painter.drawEllipse(QPointF(0, 0), radius, radius)
        painter.restore()

    def draw_construction_line(self, painter, point1, point2):
        """Draw a construction line between two points."""
        if not self._is_singly_selected():
            return
        painter.save()
        painter.setPen(self.get_dashed_construction_pen())
        painter.drawLine(point1, point2)
        painter.restore()

    @property
    def main_window(self) -> 'MainWindow':
        return self._main_window

    @property
    def grid_info(self) -> 'GridInfo':
        mainwin = self.main_window
        return mainwin.grid_info

    def is_metric(self):
        return self.grid_info.is_metric

    @property
    def color(self) -> QColor:
        return self._color

    @color.setter
    def color(self, value):
        if value is None:
            value = QColor(0, 0, 0)
        self._color = value
        self.update()

    @property
    def line_width(self) -> float:
        if self._line_width is None:
            return 2.0
        return self._line_width

    @line_width.setter
    def line_width(self, value):
        self.prepareGeometryChange()  # Line width affects bounding rect
        self._line_width = value
        self.update()

