"""
Tool ViewModel for BelfryCAD.

This ViewModel manages tool state and operations, coordinating between
different tools and the document.
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent

from ...models.cad_object import CADObject, Point, ObjectType
from ...models.document import Document


class ToolState(Enum):
    """Tool states"""
    IDLE = "idle"
    ACTIVE = "active"
    DRAWING = "drawing"
    EDITING = "editing"
    SELECTING = "selecting"


class ToolViewModel(QObject):
    """Presentation logic for tools with signals"""
    
    # Tool signals
    tool_activated = Signal(str)  # tool_token
    tool_deactivated = Signal(str)  # tool_token
    tool_state_changed = Signal(str, str)  # tool_token, state
    tool_progress = Signal(str, float)  # tool_token, progress (0.0-1.0)
    
    # Drawing signals
    drawing_started = Signal(str, QPointF)  # tool_token, start_point
    drawing_point_added = Signal(str, QPointF)  # tool_token, point
    drawing_finished = Signal(str, CADObject)  # tool_token, created_object
    drawing_cancelled = Signal(str)  # tool_token
    
    # Selection signals
    selection_started = Signal(str, QPointF)  # tool_token, start_point
    selection_updated = Signal(str, QPointF, QPointF)  # tool_token, start_point, current_point
    selection_finished = Signal(str, list)  # tool_token, selected_object_ids
    
    def __init__(self, document_viewmodel):
        super().__init__()
        self._document_viewmodel = document_viewmodel
        self._active_tool_token: Optional[str] = None
        self._tool_states: Dict[str, ToolState] = {}
        self._drawing_points: List[QPointF] = []
        self._selection_start_point: Optional[QPointF] = None
        
    @property
    def active_tool_token(self) -> Optional[str]:
        """Get active tool token"""
        return self._active_tool_token
    
    @property
    def active_tool_state(self) -> Optional[ToolState]:
        """Get active tool state"""
        if self._active_tool_token:
            return self._tool_states.get(self._active_tool_token, ToolState.IDLE)
        return None
    
    def activate_tool(self, tool_token: str):
        """Activate a tool"""
        if self._active_tool_token != tool_token:
            # Deactivate current tool
            if self._active_tool_token:
                self.deactivate_tool(self._active_tool_token)
            
            # Activate new tool
            self._active_tool_token = tool_token
            self._tool_states[tool_token] = ToolState.ACTIVE
            self.tool_activated.emit(tool_token)
            self.tool_state_changed.emit(tool_token, ToolState.ACTIVE.value)
    
    def deactivate_tool(self, tool_token: str):
        """Deactivate a tool"""
        if tool_token == self._active_tool_token:
            self._active_tool_token = None
        
        if tool_token in self._tool_states:
            self._tool_states[tool_token] = ToolState.IDLE
            self.tool_deactivated.emit(tool_token)
            self.tool_state_changed.emit(tool_token, ToolState.IDLE.value)
        
        # Clear drawing state
        self._clear_drawing_state()
    
    def handle_mouse_press(self, event: QGraphicsSceneMouseEvent):
        """Handle mouse press events"""
        if not self._active_tool_token:
            return
        
        scene_pos = event.scenePos()
        
        if self._active_tool_token == "selector":
            self._handle_selector_mouse_press(scene_pos)
        elif self._active_tool_token == "line":
            self._handle_line_mouse_press(scene_pos)
        elif self._active_tool_token == "circle":
            self._handle_circle_mouse_press(scene_pos)
        elif self._active_tool_token == "rectangle":
            self._handle_rectangle_mouse_press(scene_pos)
    
    def handle_mouse_move(self, event: QGraphicsSceneMouseEvent):
        """Handle mouse move events"""
        if not self._active_tool_token:
            return
        
        scene_pos = event.scenePos()
        
        if self._active_tool_token == "selector":
            self._handle_selector_mouse_move(scene_pos)
        elif self._active_tool_token in ["line", "circle", "rectangle"]:
            self._handle_drawing_mouse_move(scene_pos)
    
    def handle_mouse_release(self, event: QGraphicsSceneMouseEvent):
        """Handle mouse release events"""
        if not self._active_tool_token:
            return
        
        scene_pos = event.scenePos()
        
        if self._active_tool_token == "selector":
            self._handle_selector_mouse_release(scene_pos)
        elif self._active_tool_token in ["line", "circle", "rectangle"]:
            self._handle_drawing_mouse_release(scene_pos)
    
    def _handle_selector_mouse_press(self, scene_pos: QPointF):
        """Handle selector tool mouse press"""
        self._tool_states["selector"] = ToolState.SELECTING
        self._selection_start_point = scene_pos
        self.selection_started.emit("selector", scene_pos)
        self.tool_state_changed.emit("selector", ToolState.SELECTING.value)
    
    def _handle_selector_mouse_move(self, scene_pos: QPointF):
        """Handle selector tool mouse move"""
        if self._selection_start_point:
            self.selection_updated.emit("selector", self._selection_start_point, scene_pos)
    
    def _handle_selector_mouse_release(self, scene_pos: QPointF):
        """Handle selector tool mouse release"""
        if self._selection_start_point:
            # Select objects at point or in rectangle
            if (scene_pos - self._selection_start_point).manhattanLength() < 5:
                # Single point selection
                self._document_viewmodel.select_objects_at_point(scene_pos)
            else:
                # Rectangle selection
                min_x = min(self._selection_start_point.x(), scene_pos.x())
                max_x = max(self._selection_start_point.x(), scene_pos.x())
                min_y = min(self._selection_start_point.y(), scene_pos.y())
                max_y = max(self._selection_start_point.y(), scene_pos.y())
                
                selected_ids = self._document_viewmodel.document.select_objects_in_rectangle(
                    min_x, min_y, max_x, max_y
                )
                self._document_viewmodel._selected_object_ids = selected_ids
                self._document_viewmodel.selection_changed.emit(selected_ids)
            
            self.selection_finished.emit("selector", self._document_viewmodel.selected_object_ids)
        
        self._tool_states["selector"] = ToolState.ACTIVE
        self._selection_start_point = None
        self.tool_state_changed.emit("selector", ToolState.ACTIVE.value)
    
    def _handle_line_mouse_press(self, scene_pos: QPointF):
        """Handle line tool mouse press"""
        self._tool_states["line"] = ToolState.DRAWING
        self._drawing_points = [scene_pos]
        self.drawing_started.emit("line", scene_pos)
        self.tool_state_changed.emit("line", ToolState.DRAWING.value)
    
    def _handle_circle_mouse_press(self, scene_pos: QPointF):
        """Handle circle tool mouse press"""
        self._tool_states["circle"] = ToolState.DRAWING
        self._drawing_points = [scene_pos]
        self.drawing_started.emit("circle", scene_pos)
        self.tool_state_changed.emit("circle", ToolState.DRAWING.value)
    
    def _handle_rectangle_mouse_press(self, scene_pos: QPointF):
        """Handle rectangle tool mouse press"""
        self._tool_states["rectangle"] = ToolState.DRAWING
        self._drawing_points = [scene_pos]
        self.drawing_started.emit("rectangle", scene_pos)
        self.tool_state_changed.emit("rectangle", ToolState.DRAWING.value)
    
    def _handle_drawing_mouse_move(self, scene_pos: QPointF):
        """Handle drawing tool mouse move"""
        if self._active_tool_token in ["line", "circle", "rectangle"] and self._drawing_points:
            self.drawing_point_added.emit(self._active_tool_token, scene_pos)
    
    def _handle_drawing_mouse_release(self, scene_pos: QPointF):
        """Handle drawing tool mouse release"""
        if self._active_tool_token in ["line", "circle", "rectangle"] and self._drawing_points:
            self._drawing_points.append(scene_pos)
            
            # Create object based on tool type
            created_object = self._create_object_from_drawing()
            if created_object:
                object_id = self._document_viewmodel.add_object(created_object)
                self.drawing_finished.emit(self._active_tool_token, created_object)
            
            # Reset drawing state
            self._clear_drawing_state()
            self._tool_states[self._active_tool_token] = ToolState.ACTIVE
            self.tool_state_changed.emit(self._active_tool_token, ToolState.ACTIVE.value)
    
    def _create_object_from_drawing(self) -> Optional[CADObject]:
        """Create CAD object from drawing points"""
        if not self._drawing_points or len(self._drawing_points) < 2:
            return None
        
        start_point = self._drawing_points[0]
        end_point = self._drawing_points[-1]
        
        model_start = Point(start_point.x(), start_point.y())
        model_end = Point(end_point.x(), end_point.y())
        
        if self._active_tool_token == "line":
            return CADObject(ObjectType.LINE, [model_start, model_end])
        elif self._active_tool_token == "circle":
            return CADObject(ObjectType.CIRCLE, [model_start, model_end])
        elif self._active_tool_token == "rectangle":
            return CADObject(ObjectType.RECTANGLE, [model_start, model_end])
        
        return None
    
    def _clear_drawing_state(self):
        """Clear drawing state"""
        self._drawing_points.clear()
    
    def cancel_current_operation(self):
        """Cancel the current tool operation"""
        if self._active_tool_token:
            if self._active_tool_token in ["line", "circle", "rectangle"]:
                self.drawing_cancelled.emit(self._active_tool_token)
                self._clear_drawing_state()
                self._tool_states[self._active_tool_token] = ToolState.ACTIVE
                self.tool_state_changed.emit(self._active_tool_token, ToolState.ACTIVE.value)
    
    def get_tool_progress(self, tool_token: str) -> float:
        """Get tool progress (0.0-1.0)"""
        if tool_token not in self._tool_states:
            return 0.0
        
        state = self._tool_states[tool_token]
        if state == ToolState.IDLE:
            return 0.0
        elif state == ToolState.ACTIVE:
            return 0.5
        elif state == ToolState.DRAWING:
            return 0.8
        else:
            return 1.0 