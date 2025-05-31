"""
Base Tool System

This module implements the base tool system based on the original TCL
tools.tcl. It provides a foundation for all drawing and editing tools
in the pyTkCAD application.
"""

import tkinter as tk
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
    """Categories of tools based on the original TCL toolgroups"""
    SELECTOR = "Selector"
    NODES = "Nodes"
    LINES = "Lines"
    CIRCLES = "Circles"
    ARCS = "Arcs"
    BEZIERS = "Beziers"
    ELLIPSES = "Ellipses"
    CONICS = "Conics"
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
    node_info: List[str] = field(default_factory=list)  # Info about nodes


class Tool:
    """Base class for all drawing and editing tools"""

    def __init__(self, canvas: tk.Canvas, document, preferences):
        """Initialize the tool"""
        self.canvas = canvas
        self.document = document
        self.preferences = preferences
        self.state = ToolState.INIT
        self.points: List[Point] = []
        self.temp_objects = []  # Canvas IDs of temporary preview objects

        # Set up default definition - subclasses should override this
        self.definition = self._get_definition()

        # Set up mouse event bindings
        self._setup_bindings()

    def _get_definition(self) -> ToolDefinition:
        """Return the tool definition - override in subclasses"""
        return ToolDefinition(
            token="TOOL",
            name="Base Tool",
            category=ToolCategory.SELECTOR,
            icon="default",
            cursor="crosshair",
            is_creator=True
        )

    def _setup_bindings(self):
        """Set up mouse and keyboard event bindings"""
        pass  # Override in subclasses

    def activate(self):
        """Called when the tool is activated"""
        self.state = ToolState.ACTIVE
        self.points = []
        self.canvas.config(cursor=self.definition.cursor)

    def deactivate(self):
        """Called when the tool is deactivated"""
        self.clear_temp_objects()
        self.state = ToolState.INIT
        self.canvas.config(cursor="")

    def clear_temp_objects(self):
        """Clear any temporary preview objects"""
        for obj_id in self.temp_objects:
            self.canvas.delete(obj_id)
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
        """Complete the current tool operation"""
        self.state = ToolState.COMPLETE
        self.clear_temp_objects()

        # If this is a creator tool, create the object
        if self.definition.is_creator and len(self.points) > 0:
            obj = self.create_object()
            if obj:
                # Add to document
                self.document.objects.add_object(obj)
                self.document.mark_modified()

        # Reset for next operation
        self.points = []
        self.state = ToolState.ACTIVE

    def cancel(self):
        """Cancel the current tool operation"""
        self.clear_temp_objects()
        self.points = []
        self.state = ToolState.ACTIVE


class ToolManager:
    """Manages the creation, registration and activation of tools"""

    def __init__(self, canvas: tk.Canvas, document, preferences):
        self.canvas = canvas
        self.document = document
        self.preferences = preferences
        self.tools: Dict[str, Tool] = {}
        self.active_tool = None
        self.tool_change_callbacks: List[Callable] = []

    def register_tool(self, tool_class):
        """Register a tool with the manager"""
        tool = tool_class(self.canvas, self.document, self.preferences)
        self.tools[tool.definition.token] = tool
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