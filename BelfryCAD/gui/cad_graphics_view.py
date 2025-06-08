"""
CADGraphicsView - Custom graphics view for CAD operations
"""

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QEvent


class CADGraphicsView(QGraphicsView):
    """Custom graphics view for CAD drawing operations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Handle dragging ourselves
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        # Enable scrollbars
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Enable mouse wheel scrolling
        self.setInteractive(True)

        # Enable mouse tracking to receive mouse move events
        # even when no buttons are pressed
        self.setMouseTracking(True)

        # Enable touch events for multitouch scrolling
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, True)

        self.tool_manager = None  # Will be set by the main window
        self.drawing_manager = None  # Will be set by the main window

    def set_tool_manager(self, tool_manager):
        """Set the tool manager for handling events"""
        self.tool_manager = tool_manager

    def set_drawing_manager(self, drawing_manager):
        """Set the drawing manager for coordinate transformations"""
        self.drawing_manager = drawing_manager

    def wheelEvent(self, event):
        """Handle mouse wheel events for scrolling"""
        from PySide6.QtCore import Qt

        # Get wheel delta values
        delta = event.angleDelta()

        # Scroll speed multiplier
        scroll_speed = 30

        # Handle horizontal scrolling (Shift+wheel or horizontal wheel)
        if (
            event.modifiers() & Qt.KeyboardModifier.ShiftModifier or
            delta.x() != 0
        ):
            # Horizontal scrolling
            scroll_amount = delta.y() if delta.x() == 0 else delta.x()
            # Normalize wheel delta
            scroll_amount = int(scroll_amount / 120 * scroll_speed)

            # Use the view's built-in scrolling methods
            h_bar = self.horizontalScrollBar()
            new_value = h_bar.value() - scroll_amount
            h_bar.setValue(new_value)

        else:
            # Vertical scrolling (normal wheel movement)
            # Normalize wheel delta
            scroll_amount = int(delta.y() / 120 * scroll_speed)

            # Use the view's built-in scrolling methods
            v_bar = self.verticalScrollBar()
            new_value = v_bar.value() - scroll_amount
            v_bar.setValue(new_value)

        # Accept the event to prevent it from being passed to parent
        event.accept()

    def event(self, event):
        """Override event handler to catch touch events for multitouch
        scrolling"""
        # Handle multitouch pan gestures for two-finger scrolling
        if (hasattr(event, 'type') and
                event.type() == QEvent.Type.TouchUpdate):
            if (hasattr(event, 'touchPoints') and
                    len(event.touchPoints()) == 2):
                return self._handle_two_finger_scroll(event)

        return super().event(event)

    def _handle_two_finger_scroll(self, event):
        """Handle two-finger touch events for scrolling"""
        touch_points = event.touchPoints()
        if len(touch_points) != 2:
            return False

        # Calculate the center point movement between current and last
        # positions
        current_center = ((touch_points[0].pos() +
                          touch_points[1].pos()) / 2)
        last_center = ((touch_points[0].lastPos() +
                       touch_points[1].lastPos()) / 2)

        # Calculate the delta movement
        delta = current_center - last_center

        # Convert to scroll amounts (invert Y for natural scrolling)
        scroll_speed = 3.0  # Adjust sensitivity as needed
        scroll_x = int(delta.x() * scroll_speed)
        scroll_y = int(-delta.y() * scroll_speed)  # Invert Y for natural

        # Apply scrolling
        if scroll_x != 0:
            h_bar = self.horizontalScrollBar()
            new_value = h_bar.value() + scroll_x
            h_bar.setValue(new_value)

        if scroll_y != 0:
            v_bar = self.verticalScrollBar()
            new_value = v_bar.value() + scroll_y
            v_bar.setValue(new_value)

        event.accept()
        return True

    def mousePressEvent(self, event):
        """Handle mouse press events and forward to active tool"""
        if self.tool_manager and self.tool_manager.get_active_tool():
            # Convert to scene coordinates
            scene_pos = self.mapToScene(event.pos())

            # Convert Qt scene coordinates to CAD coordinates using
            # drawing manager
            if self.drawing_manager:
                # Use descale_coords to convert from Qt (Y-down) to CAD
                # (Y-up) coordinates
                cad_coords = self.drawing_manager.descale_coords(
                    [scene_pos.x(), scene_pos.y()])
                cad_x, cad_y = cad_coords[0], cad_coords[1]
            else:
                # Fallback to scene coordinates if no drawing manager
                cad_x, cad_y = scene_pos.x(), scene_pos.y()

            # Create a simple event object with CAD coordinates and x/y
            # attrs
            class SceneEvent:
                def __init__(self, scene_pos, cad_x, cad_y):
                    self._scene_pos = scene_pos
                    self.x = cad_x  # Use CAD coordinates
                    self.y = cad_y  # Use CAD coordinates

                def scenePos(self):
                    return self._scene_pos

            scene_event = SceneEvent(scene_pos, cad_x, cad_y)
            self.tool_manager.get_active_tool().handle_mouse_down(
                scene_event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events and forward to active tool"""
        if self.tool_manager and self.tool_manager.get_active_tool():
            scene_pos = self.mapToScene(event.pos())

            # Convert Qt scene coordinates to CAD coordinates using
            # drawing manager
            if self.drawing_manager:
                # Use descale_coords to convert from Qt (Y-down) to CAD
                # (Y-up) coordinates
                cad_coords = self.drawing_manager.descale_coords(
                    [scene_pos.x(), scene_pos.y()])
                cad_x, cad_y = cad_coords[0], cad_coords[1]
            else:
                # Fallback to scene coordinates if no drawing manager
                cad_x, cad_y = scene_pos.x(), scene_pos.y()

            class SceneEvent:
                def __init__(self, scene_pos, cad_x, cad_y):
                    self._scene_pos = scene_pos
                    self.x = cad_x  # Use CAD coordinates
                    self.y = cad_y  # Use CAD coordinates

                def scenePos(self):
                    return self._scene_pos

            scene_event = SceneEvent(scene_pos, cad_x, cad_y)
            self.tool_manager.get_active_tool().handle_mouse_move(
                scene_event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events and forward to active tool"""
        if self.tool_manager and self.tool_manager.get_active_tool():
            scene_pos = self.mapToScene(event.pos())

            # Convert Qt scene coordinates to CAD coordinates using
            # drawing manager
            if self.drawing_manager:
                # Use descale_coords to convert from Qt (Y-down) to CAD
                # (Y-up) coordinates
                cad_coords = self.drawing_manager.descale_coords(
                    [scene_pos.x(), scene_pos.y()])
                cad_x, cad_y = cad_coords[0], cad_coords[1]
            else:
                # Fallback to scene coordinates if no drawing manager
                cad_x, cad_y = scene_pos.x(), scene_pos.y()

            class SceneEvent:
                def __init__(self, scene_pos, cad_x, cad_y):
                    self._scene_pos = scene_pos
                    self.x = cad_x  # Use CAD coordinates
                    self.y = cad_y  # Use CAD coordinates

                def scenePos(self):
                    return self._scene_pos

            scene_event = SceneEvent(scene_pos, cad_x, cad_y)
            # Check if tool has handle_mouse_up method (selector tool has it)
            active_tool = self.tool_manager.get_active_tool()
            if hasattr(active_tool, 'handle_mouse_up'):
                active_tool.handle_mouse_up(scene_event)
            elif hasattr(active_tool, 'handle_drag'):
                active_tool.handle_drag(scene_event)
        else:
            super().mouseReleaseEvent(event)
