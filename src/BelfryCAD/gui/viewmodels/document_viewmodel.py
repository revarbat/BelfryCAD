"""
Document ViewModel for BelfryCAD.

This ViewModel handles presentation logic for the document and emits signals
for UI updates. It acts as the bridge between the Document model and the UI.
"""

from typing import List, Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, QPointF
from PySide6.QtWidgets import QGraphicsSceneMouseEvent

from ...models.document import Document
from ...models.cad_object import CadObject, ObjectType
from ...cad_geometry import Point2D


class DocumentViewModel(QObject):
    """Presentation logic for the document with signals"""
    
    # Document signals
    document_changed = Signal()
    document_modified = Signal()
    document_saved = Signal()
    
    # Object signals
    object_added = Signal(str, CadObject)  # object_id, object
    object_removed = Signal(str)  # object_id
    object_moved = Signal(str, float, float)  # object_id, dx, dy
    object_selected = Signal(str)  # object_id
    object_deselected = Signal(str)  # object_id
    selection_changed = Signal(list)  # selected_object_ids
    
    # Tool signals
    tool_changed = Signal(str)  # tool_token
    tool_activated = Signal(str)  # tool_token
    tool_deactivated = Signal(str)  # tool_token
    
    def __init__(self, document: Document):
        super().__init__()
        self._document = document
        self._selected_object_ids: List[str] = []
        self._active_tool_token: Optional[str] = None
        
    @property
    def document(self) -> Document:
        """Get the underlying document model"""
        return self._document
    
    @property
    def selected_object_ids(self) -> List[str]:
        """Get currently selected object IDs"""
        return self._selected_object_ids.copy()
    
    @property
    def active_tool_token(self) -> Optional[str]:
        """Get active tool token"""
        return self._active_tool_token
    
    def add_object(self, cad_object: CadObject) -> str:
        """Add object to document and emit signal"""
        object_id = self._document.add_object(cad_object)
        self.object_added.emit(object_id, cad_object)
        self.document_changed.emit()
        self.document_modified.emit()
        return object_id
    
    def remove_object(self, object_id: str) -> bool:
        """Remove object from document and emit signal"""
        if self._document.remove_object(object_id):
            self.object_removed.emit(object_id)
            self.document_changed.emit()
            self.document_modified.emit()
            return True
        return False
    
    def get_object(self, object_id: str) -> Optional[CadObject]:
        """Get object by ID"""
        return self._document.get_object(object_id)
    
    def get_all_objects(self) -> List[CadObject]:
        """Get all objects"""
        return self._document.get_all_objects()
    
    def get_visible_objects(self) -> List[CadObject]:
        """Get visible objects"""
        return self._document.get_visible_objects()
    
    def select_object(self, object_id: str):
        """Select a single object"""
        if object_id not in self._selected_object_ids:
            self._selected_object_ids = [object_id]
            self.object_selected.emit(object_id)
            self.selection_changed.emit(self._selected_object_ids)
    
    def add_to_selection(self, object_id: str):
        """Add object to selection"""
        if object_id not in self._selected_object_ids:
            self._selected_object_ids.append(object_id)
            self.object_selected.emit(object_id)
            self.selection_changed.emit(self._selected_object_ids)
    
    def remove_from_selection(self, object_id: str):
        """Remove object from selection"""
        if object_id in self._selected_object_ids:
            self._selected_object_ids.remove(object_id)
            self.object_deselected.emit(object_id)
            self.selection_changed.emit(self._selected_object_ids)
    
    def clear_selection(self):
        """Clear all selections"""
        if self._selected_object_ids:
            for object_id in self._selected_object_ids:
                self.object_deselected.emit(object_id)
            self._selected_object_ids.clear()
            self.selection_changed.emit(self._selected_object_ids)
    
    def select_objects_at_point(self, point: QPointF, tolerance: float = 5.0):
        """Select objects at a specific point"""
        model_point = Point2D(point.x(), point.y())
        selected_ids = self._document.select_objects_at_point(model_point, tolerance)
        
        # Update selection
        self._selected_object_ids = selected_ids
        for object_id in selected_ids:
            self.object_selected.emit(object_id)
        self.selection_changed.emit(self._selected_object_ids)
    
    def move_selected_objects(self, dx: float, dy: float):
        """Move selected objects"""
        if self._selected_object_ids:
            self._document.move_selected_objects(self._selected_object_ids, dx, dy)
            for object_id in self._selected_object_ids:
                self.object_moved.emit(object_id, dx, dy)
            self.document_modified.emit()
    
    def delete_selected_objects(self):
        """Delete selected objects"""
        if self._selected_object_ids:
            for object_id in self._selected_object_ids:
                self.remove_object(object_id)
            self._selected_object_ids.clear()
            self.selection_changed.emit(self._selected_object_ids)
    
    def set_active_tool(self, tool_token: str):
        """Set active tool"""
        if self._active_tool_token != tool_token:
            if self._active_tool_token:
                self.tool_deactivated.emit(self._active_tool_token)
            self._active_tool_token = tool_token
            self.tool_activated.emit(tool_token)
            self.tool_changed.emit(tool_token)
    
    def handle_mouse_press(self, event: QGraphicsSceneMouseEvent):
        """Handle mouse press events"""
        if self._active_tool_token:
            # Delegate to active tool
            # This would be handled by a ToolManager ViewModel
            pass
        else:
            # Handle selection
            scene_pos = event.scenePos()
            self.select_objects_at_point(scene_pos)
    
    def mark_saved(self):
        """Mark document as saved"""
        self._document.mark_saved()
        self.document_saved.emit()
    
    def is_modified(self) -> bool:
        """Check if document is modified"""
        return self._document.is_modified()
    
    def get_document_bounds(self):
        """Get document bounds"""
        return self._document.get_document_bounds() 