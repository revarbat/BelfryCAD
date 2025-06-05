"""
Base Tool System

This module implements the base tool system based on the original TCL
tools.tcl. It provides a foundation for all drawing and editing tools
in the pyTkCAD application.
"""

from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QCursor
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field

from src.core.cad_objects import CADObject, Point


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
    SCREWHOLES = "ScrewHoles"


class SnapType(Enum):
    """Types of snaps available for tools"""
    GRID = "grid"
    ENDPOINT = "endpoint"
    CENTER = "center"
    MIDPOINT = "midpoint"
    INTERSECTION = "intersection"
    TANGENT = "tangent"
    PERPENDICULAR = "perpendicular"
    PARALLEL = "parallel"
    EXTENSION = "extension"
    NEAREST = "nearest"
    NONE = "none"
    ALL = "all"


@dataclass
class ToolDefinition:
    """Definition of a tool's properties"""
    token: str                     # Unique identifier for the tool
    name: str                      # Human-readable name
    category: ToolCategory         # Tool category
    icon: str = ""                 # Icon for the tool in the toolbox
    cursor: str = "crosshair"      # Cursor shape when tool is active
    snaps: List[SnapType] = field(default_factory=lambda: [SnapType.ALL])
    is_creator: bool = True        # Whether the tool creates objects
    show_controls: bool = False    # Whether to show control points
    keyboard_shortcut: str = ""    # Optional keyboard shortcut
    secondary_key: str = ""        # Secondary key for palette selection
    node_info: List[str] = field(default_factory=list)  # Info about nodes


class Tool(QObject):
    """Base class for all drawing and editing tools"""

    # Signal emitted when an object is created
    object_created = Signal(CADObject)

    def __init__(self, scene: QGraphicsScene, document, preferences):
        """Initialize the tool"""
        super().__init__()
        self.scene = scene
        self.document = document
        self.preferences = preferences
        self.state = ToolState.INIT
        self.points: List[Point] = []
        self.temp_objects = []  # QGraphicsItems for temporary preview objects

        # Set up default definitions - subclasses should override this
        self.definitions = self._get_definition()
        # For compatibility, keep the first definition as primary
        self.definition = self.definitions[0] if self.definitions else None

        # Set up mouse event bindings
        self._setup_bindings()

    def _get_definition(self) -> List[ToolDefinition]:
        """Return the tool definitions - override in subclasses"""
        return [ToolDefinition(
            token="TOOL",
            name="Base Tool",
            category=ToolCategory.SELECTOR,
            icon="default",
            cursor="crosshair",
            is_creator=True
        )]

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass  # Override in subclasses

    def activate(self):
        """Called when the tool is activated"""
        self.state = ToolState.ACTIVE
        self.points = []
        # Set cursor on the view(s) that use this scene
        for view in self.scene.views():
            cursor_name = self.definition.cursor
            cursor_shape = getattr(Qt, f'{cursor_name}Cursor', Qt.CrossCursor)
            view.setCursor(QCursor(cursor_shape))

    def deactivate(self):
        """Called when the tool is deactivated"""
        self.clear_temp_objects()
        self.state = ToolState.INIT
        # Reset cursor on the view(s) that use this scene
        for view in self.scene.views():
            view.setCursor(QCursor(Qt.ArrowCursor))

    def clear_temp_objects(self):
        """Clear any temporary preview objects"""
        for graphics_item in self.temp_objects:
            self.scene.removeItem(graphics_item)
        self.temp_objects = []

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

    def handle_key_press(self, event):
        """Handle keyboard press event"""
        # Override in subclasses
        pass

    def handle_key_release(self, event):
        """Handle keyboard release event"""
        # Override in subclasses
        pass

    def create_object(self) -> Optional[CADObject]:
        """Create a CAD object from the collected points"""
        # Override in subclasses
        return None

    def get_snap_point(self, x: float, y: float) -> Point:
        """Get the snapped point based on snap settings"""
        # TODO: Implement snap logic
        return Point(x, y)

    def draw_preview(self, current_x: float, current_y: float):
        """Draw a preview of the object being created"""
        # Override in subclasses
        pass

    def complete(self):
        """Complete the current tool operation and create the object"""
        if self.state == ToolState.DRAWING:
            obj = self.create_object()
            if obj:
                self.document.objects.add_object(obj)
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

    def __init__(self, scene: QGraphicsScene, document, preferences):
        self.scene = scene
        self.document = document
        self.preferences = preferences
        self.tools: Dict[str, Tool] = {}
        self.active_tool = None
        self.tool_change_callbacks: List[Callable] = []

    def register_tool(self, tool_class):
        """Register a tool with the manager"""
        tool = tool_class(self.scene, self.document, self.preferences)
        # Register all definitions from this tool
        for definition in tool.definitions:
            self.tools[definition.token] = tool
        return tool

    def activate_tool(self, token: str):
        """Activate a tool by its token"""
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

    def get_active_tool(self) -> Optional[Tool]:
        """Get the currently active tool"""
        return self.active_tool

    def add_tool_change_listener(self, callback: Callable):
        """Add a listener for tool change events"""
        self.tool_change_callbacks.append(callback)
