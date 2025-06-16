"""
CADGraphicsView - Custom graphics view for CAD operations
"""

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtGui import QPainter
from PySide6.QtCore import Qt, QEvent, Signal
from typing import List


class CADGraphicsView(QGraphicsView):
    """Custom graphics view for CAD drawing operations."""

    # Signal emitted when view position changes (scrolling, etc.)
    view_position_changed = Signal(float, float)  # x, y in scene coordinates

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

        # Initialize drawing context fields
        self.scale_factor: float = 1.0

        # Set default transform to invert Y-axis for CAD coordinate system
        # This makes Y increase upward (CAD convention) instead of downward
        # (Qt convention)
        factor = self.logicalDpiX() * self.scale_factor
        self.scale(factor, -factor)

        # Set transformation anchors to allow zooming and panning
        # around the mouse cursor position
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(
            QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.tool_manager = None  # Will be set by the main window
        self.drawing_manager = None  # Will be set by the main window

        # Touch gesture state tracking
        self._last_pinch_distance = None

        # Gesture state tracking for performance optimization
        self._gesture_in_progress = False
        self._native_gesture_active = False

    def _on_scale_changed(self, scale_factor):
        """Handle scale changes from CadScene to update visual zoom"""
        # Calculate the appropriate view transform scale
        # The QGraphicsView transform should reflect the CadScene scale
        # to provide visual feedback for zoom operations
        from PySide6.QtCore import QPoint
        if scale_factor != 1.0:
            print(f"new scale factor: {scale_factor}")
            print(f"  before @0,0: {self.mapToScene(QPoint(0, 0))}")
        self.resetTransform()
        if scale_factor != 1.0:
            print(f"  reset @0,0: {self.mapToScene(QPoint(0, 0))}")
        self.scale(scale_factor, -scale_factor)
        if scale_factor != 1.0:
            print(f"  after @0,0: {self.mapToScene(QPoint(0, 0))}")
            import sys; sys.exit()

    def set_tool_manager(self, tool_manager):
        """Set the tool manager for handling events"""
        self.tool_manager = tool_manager

    def set_drawing_manager(self, drawing_manager):
        """Set the drawing manager for coordinate transformations"""
        self.drawing_manager = drawing_manager

        # Connect to scale changes for visual zoom updates
        if (self.drawing_manager and
                self.drawing_manager.cad_scene and
                hasattr(self.drawing_manager.cad_scene, 'scale_changed')):
            self.drawing_manager.cad_scene.scale_changed.connect(
                self._on_scale_changed
            )

        # Connect scroll bars to ruler updates
        h_bar = self.horizontalScrollBar()
        v_bar = self.verticalScrollBar()
        h_bar.valueChanged.connect(self._update_rulers_on_scroll)
        v_bar.valueChanged.connect(self._update_rulers_on_scroll)

    def wheelEvent(self, event):
        """Handle mouse wheel events for scrolling and zooming"""
        from PySide6.QtCore import Qt

        # Get wheel delta values
        delta = event.angleDelta()
        # Check for Ctrl+wheel for zooming
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Qt maps Command key (⌘) to ControlModifier on macOS for
            # cross-platform compatibility, so this detects Cmd+wheel on
            # macOS and Ctrl+wheel on Windows/Linux

            if self.drawing_manager and self.drawing_manager.cad_scene:
                # Get current scale factor
                current_scale = self.drawing_manager.cad_scene.scale_factor

                # Calculate zoom factor (normalize wheel delta)
                zoom_delta = delta.y() / 120.0  # Standard wheel delta is 120
                zoom_factor = 1.0 + (zoom_delta * 0.2)  # 20% zoom step

                # Calculate new scale factor
                new_scale = current_scale * zoom_factor

                # Clamp zoom to reasonable limits (0.01x to 100x)
                new_scale = max(0.01, min(100.0, new_scale))

                # Apply the new scale factor
                self.drawing_manager.cad_scene.set_scale_factor(new_scale)

            # Accept the event to prevent further processing
            event.accept()
            return

        # Scroll speed multiplier
        scroll_speed = 60

        # Handle horizontal scrolling
        if delta.x() != 0:
            # Horizontal scrolling
            scroll_amount = int(delta.x() / 120 * scroll_speed)

            # Use the view's built-in scrolling methods
            h_bar = self.horizontalScrollBar()
            new_value = h_bar.value() - scroll_amount
            h_bar.setValue(new_value)

        # Handle vertical scrolling
        if delta.y() != 0:
            # Normalize wheel delta
            scroll_amount = int(delta.y() / 120 * scroll_speed)

            # Use the view's built-in scrolling methods
            v_bar = self.verticalScrollBar()
            new_value = v_bar.value() - scroll_amount
            v_bar.setValue(new_value)

        # Update rulers after scrolling
        self._update_rulers_on_scroll()

        # Accept the event to prevent it from being passed to parent
        event.accept()

    def event(self, event):
        """Override event handler to catch touch events for multitouch
        scrolling and pinch-to-zoom"""
        event_type = event.type()

        # Handle macOS trackpad pinch gestures via QNativeGestureEvent
        if (hasattr(QEvent.Type, 'NativeGesture') and
                event_type == QEvent.Type.NativeGesture):
            if hasattr(event, 'gestureType'):
                gesture_type = event.gestureType()

                # Handle gesture begin - start deferred mode
                if gesture_type == Qt.NativeGestureType.BeginNativeGesture:
                    self._native_gesture_active = True
                    self._gesture_in_progress = True
                    event.accept()
                    return True

                # Handle gesture end - redraw grid and cleanup
                elif gesture_type == Qt.NativeGestureType.EndNativeGesture:
                    self._native_gesture_active = False
                    self._gesture_in_progress = False
                    # Redraw grid now that gesture is complete to ensure
                    # 1.0 pixel line width
                    if (self.drawing_manager and
                            self.drawing_manager.cad_scene):
                        self.drawing_manager.cad_scene.redraw_grid()
                    event.accept()
                    return True

                # Handle pinch zoom gestures (macOS trackpad)
                elif gesture_type == Qt.NativeGestureType.ZoomNativeGesture:
                    if hasattr(event, 'value'):
                        zoom_value = event.value()

                        if (self.drawing_manager and
                                self.drawing_manager.cad_scene):
                            # Get current scale factor
                            current_scale = (self.drawing_manager.cad_scene
                                             .scale_factor)

                            # Convert native gesture value to zoom factor
                            # Native gesture value represents the zoom delta
                            # For pinch gestures:
                            #   negative = zoom out,
                            #   positive = zoom in
                            # Convert to multiplicative factor: 1.0 + delta
                            zoom_factor = 1.0 + zoom_value

                            # Calculate new scale factor
                            new_scale = current_scale * zoom_factor

                            # Clamp zoom to reasonable limits (0.01x to 100x)
                            new_scale = max(0.01, min(100.0, new_scale))

                            # Apply the new scale factor with deferred grid
                            # redraw during continuous gesture
                            defer_redraw = self._native_gesture_active
                            self.drawing_manager.cad_scene.set_scale_factor(
                                new_scale, defer_grid_redraw=defer_redraw)

                        event.accept()
                        return True

        # Handle touch events for touchscreen devices (non-macOS trackpad)
        if (hasattr(event, 'type') and
                event.type() in [QEvent.Type.TouchBegin,
                                 QEvent.Type.TouchUpdate,
                                 QEvent.Type.TouchEnd]):
            # Handle touch begin - start gesture tracking
            if event.type() == QEvent.Type.TouchBegin:
                if (hasattr(event, 'touchPoints') and
                        len(event.touchPoints()) == 2):
                    self._gesture_in_progress = True

            # Handle touch update - process gestures with deferred redraw
            elif event.type() == QEvent.Type.TouchUpdate:
                if (hasattr(event, 'touchPoints') and
                        len(event.touchPoints()) == 2):
                    # Handle two-finger pinch-to-zoom for touchscreen devices
                    touch_points = event.touchPoints()
                    if len(touch_points) == 2:
                        # Calculate distance between touch points
                        point1 = touch_points[0].pos()
                        point2 = touch_points[1].pos()
                        current_distance = (
                            (point1.x() - point2.x()) ** 2 +
                            (point1.y() - point2.y()) ** 2
                        ) ** 0.5

                        if self._last_pinch_distance is not None:
                            # Calculate zoom factor based on distance change
                            distance_ratio = current_distance / \
                                self._last_pinch_distance
                            if (self.drawing_manager and
                                    self.drawing_manager.cad_scene):
                                current_scale = \
                                    self.drawing_manager.cad_scene.scale_factor
                                new_scale = current_scale * distance_ratio
                                new_scale = max(0.01, min(100.0, new_scale))
                                # Use deferred redraw during continuous gesture
                                self.drawing_manager.cad_scene. \
                                    set_scale_factor(
                                        new_scale, defer_grid_redraw=True)

                        self._last_pinch_distance = current_distance
                        event.accept()
                        return True

            # Handle touch end - cleanup and redraw grid
            elif event.type() == QEvent.Type.TouchEnd:
                # Reset pinch tracking when touch ends
                self._last_pinch_distance = None
                # End gesture and redraw grid if needed
                if self._gesture_in_progress:
                    self._gesture_in_progress = False
                    if (self.drawing_manager and
                            self.drawing_manager.cad_scene):
                        self.drawing_manager.cad_scene.redraw_grid()

        return super().event(event)

    def get_scale_factor(self) -> float:
        """Get the current scale factor."""
        return self.scale_factor

    def set_scale_factor(self, scale_factor: float):
        """Set the scale factor (zoom level)."""
        self.scale_factor = scale_factor

    def scale_coords(self, coords: List[float]) -> List[float]:
        """Convert CAD coordinates to view coordinates using Qt transforms"""
        from PySide6.QtCore import QPointF

        scaled_coords = []
        for i in range(0, len(coords), 2):
            # Create point in CAD coordinates
            cad_point = QPointF(coords[i], coords[i + 1])
            # Map to view coordinates using Qt's transform system
            view_point = self.mapFromScene(cad_point)
            scaled_coords.extend([view_point.x(), view_point.y()])
        return scaled_coords

    def descale_coords(self, coords: List[float]) -> List[float]:
        """Convert view coordinates to CAD coordinates using Qt transforms"""
        from PySide6.QtCore import QPointF

        descaled_coords = []
        for i in range(0, len(coords), 2):
            # Create point in view coordinates
            view_point = QPointF(coords[i], coords[i + 1])
            # Map to scene (CAD) coordinates using Qt's transform system
            cad_point = self.mapToScene(view_point.toPoint())
            descaled_coords.extend([cad_point.x(), cad_point.y()])
        return descaled_coords

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

    def _update_rulers_on_scroll(self):
        """Update rulers when the view is scrolled."""
        if hasattr(self, 'drawing_manager') and self.drawing_manager:
            cad_scene = self.drawing_manager.cad_scene
            if cad_scene and hasattr(cad_scene, 'ruler_manager'):
                # Update rulers with current view position
                ruler_manager = cad_scene.ruler_manager
                if hasattr(ruler_manager, 'update_rulers_on_view_change'):
                    ruler_manager.update_rulers_on_view_change()
                elif hasattr(ruler_manager, 'update_rulers'):
                    ruler_manager.update_rulers()

                # Emit signal to notify other components of view change
                if hasattr(self, 'view_position_changed'):
                    # Get current view center in scene coordinates
                    center = self.mapToScene(self.viewport().rect().center())
                    self.view_position_changed.emit(center.x(), center.y())

    def scrollContentsBy(self, dx, dy):
        """Override scrollContentsBy to update rulers when scrolling."""
        # Call parent implementation for actual scrolling
        super().scrollContentsBy(dx, dy)

        # Update rulers after scrolling
        self._update_rulers_on_scroll()
