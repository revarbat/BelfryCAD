"""
Base CadTool System

This module implements the base tool system based on the original TCL
tools.tcl. It provides a foundation for all drawing and editing tools
in the pyBelfryCad application.
"""

from typing import Dict, List, Optional, Callable

from enum import Enum
from dataclasses import dataclass, field

from PySide6.QtCore import Qt, QObject, Signal, QPointF
from PySide6.QtGui import QCursor, QPen, QColor, QBrush

from ..models.cad_object import CadObject, ObjectType
from ..cad_geometry import Point2D


class ToolState(Enum):
    """States a tool can be in during its operation"""
    INIT = "INIT"            # Initial state
    ACTIVE = "ACTIVE"        # Tool is active but not performing an operation
    DRAWING = "DRAWING"      # Tool is actively drawing
    SELECTING = "SELECTING"  # Tool is selecting objects
    EDITING = "EDITING"      # Tool is editing objects
    COMPLETE = "COMPLETE"    # Tool operation is complete


class ToolCategory(Enum):
    """Categories of tools"""
    SELECTOR = "Selector"
    NODES = "Nodes"
    LINES = "Lines"
    ARCS = "Arcs"
    ELLIPSES = "Ellipses"
    POLYGONS = "Polygons"
    TEXT = "Text"
    IMAGES = "Images"
    DIMENSIONS = "Dimensions"
    TRANSFORMS = "Transforms"
    LAYOUT = "Layout"
    DUPLICATORS = "Duplicators"
    POINTS = "Points"
    CAM = "CAM"
    MISC = "Miscellaneous"



@dataclass
class ToolDefinition:
    """Definition of a tool's properties"""
    token: str                     # Unique identifier for the tool
    name: str                      # Human-readable name
    category: ToolCategory         # CadTool category
    icon: str = ""                 # Icon for the tool in the toolbox
    cursor: str = "crosshair"      # Cursor shape when tool is active
    is_creator: bool = True        # Whether the tool creates objects
    show_controls: bool = False    # Whether to show control points
    keyboard_shortcut: str = ""    # Optional keyboard shortcut
    secondary_key: str = ""        # Secondary key for palette selection
    node_info: List[str] = field(default_factory=list)  # Info about nodes


class CadTool(QObject):
    """Base class for all drawing and editing tools"""

    # Signal emitted when an object is created
    object_created = Signal(CadObject)

    # Class-level tool definitions - subclasses should override this
    tool_definitions: List[ToolDefinition] = []

    def __init__(self, document_window, document, preferences):
        """Initialize the tool"""
        super().__init__()
        self.document_window = document_window
        self.document = document
        self.preferences = preferences
        self.state = ToolState.INIT
        self.points: List[Point2D] = []
        self.temp_objects: List = []  # List to track temporary preview objects

        # Set up tool definitions from class attribute
        self.definitions = self._get_definition()
        # For compatibility, keep the first definition as primary
        self.definition = self.definitions[0] if self.definitions else None

    @property
    def scene(self):
        """Get the CAD graphics scene from the document window"""
        return self.document_window.get_scene()

    @property
    def dpcm(self):
        """Get the dots per millimeter from the document window"""
        return self.document_window.get_dpcm()

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definitions - uses class-level definitions by default"""
        if self.tool_definitions:
            return self.tool_definitions
        
        # Fallback for backward compatibility
        return []

    def activate(self):
        """Called when the tool is activated"""
        self.state = ToolState.ACTIVE
        self.points = []
        # Set cursor on the view(s) that use this scene
        if self.definition and hasattr(self.definition, 'cursor'):
            for view in self.scene.views():
                cursor_name = self.definition.cursor
                # Map cursor names to Qt cursor shapes
                cursor_mapping = {
                    'arrow': Qt.CursorShape.ArrowCursor,
                    'crosshair': Qt.CursorShape.CrossCursor,
                    'text': Qt.CursorShape.IBeamCursor,
                    'pointing': Qt.CursorShape.PointingHandCursor,
                    'hand': Qt.CursorShape.PointingHandCursor,
                    'wait': Qt.CursorShape.WaitCursor,
                    'busy': Qt.CursorShape.BusyCursor,
                    'forbidden': Qt.CursorShape.ForbiddenCursor,
                    'size': Qt.CursorShape.SizeAllCursor,
                    'resize': Qt.CursorShape.SizeAllCursor,
                }
                cursor_shape = cursor_mapping.get(
                    cursor_name,
                    Qt.CursorShape.CrossCursor
                )
                view.setCursor(QCursor(cursor_shape))

    def deactivate(self):
        """Called when the tool is deactivated"""
        self.clear_temp_objects()
        self.state = ToolState.INIT
        # Reset cursor on the view(s) that use this scene
        for view in self.scene.views():
            view.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def clear_temp_objects(self):
        """Clear any temporary preview objects"""
        # Remove all temporary objects from the scene
        scene = self.scene
        if scene and self.temp_objects:
            for temp_obj in self.temp_objects:
                if hasattr(temp_obj, 'scene') and temp_obj.scene():
                    scene.removeItem(temp_obj)
            self.temp_objects.clear()

    def handle_mouse_down(self, event):
        """Handle mouse button press event"""
        # Override in subclasses
        pass

    def handle_mouse_move(self, event):
        """Handle mouse movement event"""
        # Override in subclasses
        pass

    def handle_mouse_up(self, event):
        """Handle mouse button release event"""
        # Override in subclasses
        pass

    def handle_escape(self, event):
        """Handle escape key to cancel the operation"""
        self.cancel()

    def handle_key_press(self, event):
        """Handle keyboard press event"""
        # Check for escape key
        if event.key() == Qt.Key.Key_Escape:
            self.handle_escape(event)
            event.accept()
            return
        
        # Override in subclasses for other key handling
        pass

    def handle_key_release(self, event):
        """Handle keyboard release event"""
        # Override in subclasses
        pass

    def create_object(self) -> Optional[CadObject]:
        """Create a CAD object from the collected points"""
        # Override in subclasses
        return None

    def get_snap_point(self, x: float, y: float) -> Point2D:
        """Get the snapped point based on snap settings"""
        # Get the snaps system from the main window
        if hasattr(self.document_window, 'snaps_system'):
            mouse_pos = QPointF(x, y)
            recent_points = [QPointF(p.x, p.y) for p in self.points]
            snapped_point = self.document_window.snaps_system.get_snap_point(mouse_pos, recent_points)
            if snapped_point:
                return Point2D(snapped_point.x(), snapped_point.y())
        
        # Fallback to original position if no snap system or no snap found
        return Point2D(x, y)

    def draw_points(self):
        """Draw the points on the scene"""
        scale = self.scene.views()[0].transform().m11()
        dot_size = 7 / scale
        for point in self.points:
            point_item = self.scene.addEllipse(
                point.x - dot_size / 2,
                point.y - dot_size / 2,
                dot_size, dot_size,
                pen=QPen(QColor("red"), 0.0),
                brush=QBrush(QColor("red"))
            )
            self.temp_objects.append(point_item)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw a preview of the object being created"""
        # Override in subclasses
        pass

    def complete(self):
        """Complete the current tool operation and create the object"""
        if self.state == ToolState.DRAWING:
            obj = self.create_object()
            if obj:
                self.document.add_object(obj)
                self.document.mark_modified()
                # Emit signal to notify the main window to redraw
                self.object_created.emit(obj)

            # Reset for next operation
            self.points = []
            self.clear_temp_objects()
            self.state = ToolState.ACTIVE

    def cancel(self):
        """Cancel the current tool operation"""
        self.clear_temp_objects()
        self.points = []
        self.state = ToolState.ACTIVE


class ToolManager:
    """Manages the creation, registration and activation of tools"""

    def __init__(self, document_window, document, preferences):
        print(f"ToolManager init: {document_window}, {document}, {preferences}")
        self.document_window = document_window
        self.document = document
        self.preferences = preferences
        self.tools: Dict[str, CadTool] = {}
        self.active_tool = None
        self.tool_change_callbacks: List[Callable] = []

    def register_tool(self, tool_class):
        """Register a tool class with the tool manager."""
        tool = tool_class(self.document_window, self.document, self.preferences)
        # Register all definitions from this tool
        for definition in tool.definitions:
            self.tools[definition.token] = tool
        return tool

    def activate_tool(self, token: str):
        """Activate a tool by its token."""
        if self.active_tool:
            self.active_tool.deactivate()

        if token in self.tools:
            self.active_tool = self.tools[token]
            self.active_tool.activate()

            # Notify listeners
            for callback in self.tool_change_callbacks:
                callback(token)
        else:
            self.active_tool = None

    def get_active_tool(self) -> Optional['CadTool']:
        """Get the currently active tool."""
        return self.active_tool

    def add_tool_change_listener(self, callback: Callable):
        """Add a listener for tool change events"""
        self.tool_change_callbacks.append(callback)
