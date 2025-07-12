"""
Undo/Redo ViewModel for BelfryCAD.

This ViewModel manages undo/redo operations and integrates with the existing
undo/redo system while providing signals for UI updates.
"""

from typing import List, Dict, Any, Optional, Callable
from PySide6.QtCore import QObject, Signal

from ...models.document import Document
from ...models.cad_object import CADObject, Point


class UndoRedoViewModel(QObject):
    """Presentation logic for undo/redo operations with signals"""
    
    # Undo/Redo signals
    undo_available = Signal(bool)  # can_undo
    redo_available = Signal(bool)  # can_redo
    undo_stack_changed = Signal()  # stack changed
    operation_undone = Signal(str)  # operation_description
    operation_redone = Signal(str)  # operation_description
    
    def __init__(self, document_viewmodel, max_undo_levels: int = 50):
        super().__init__()
        self._document_viewmodel = document_viewmodel
        self._max_undo_levels = max_undo_levels
        self._undo_stack: List[Dict[str, Any]] = []
        self._redo_stack: List[Dict[str, Any]] = []
        self._is_undoing = False
        self._is_redoing = False
        
        # Connect to document changes to automatically create undo states
        self._document_viewmodel.document_modified.connect(self._on_document_modified)
        self._document_viewmodel.object_added.connect(self._on_object_added)
        self._document_viewmodel.object_removed.connect(self._on_object_removed)
        self._document_viewmodel.object_moved.connect(self._on_object_moved)
    
    @property
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self._undo_stack) > 0
    
    @property
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self._redo_stack) > 0
    
    @property
    def undo_count(self) -> int:
        """Get number of available undo operations"""
        return len(self._undo_stack)
    
    @property
    def redo_count(self) -> int:
        """Get number of available redo operations"""
        return len(self._redo_stack)
    
    def save_state(self, operation_description: str = "Operation"):
        """Save current document state for undo"""
        if self._is_undoing or self._is_redoing:
            return
        
        # Create snapshot of current document state
        state = self._create_document_snapshot()
        state['description'] = operation_description
        
        # Add to undo stack
        self._undo_stack.append(state)
        
        # Clear redo stack when new operation is performed
        self._redo_stack.clear()
        
        # Limit undo stack size
        if len(self._undo_stack) > self._max_undo_levels:
            self._undo_stack.pop(0)
        
        # Emit signals
        self.undo_available.emit(self.can_undo)
        self.redo_available.emit(self.can_redo)
        self.undo_stack_changed.emit()
    
    def undo(self):
        """Undo the last operation"""
        if not self.can_undo:
            return
        
        self._is_undoing = True
        
        try:
            # Save current state for redo
            current_state = self._create_document_snapshot()
            self._redo_stack.append(current_state)
            
            # Restore previous state
            previous_state = self._undo_stack.pop()
            self._restore_document_snapshot(previous_state)
            
            # Emit signals
            self.undo_available.emit(self.can_undo)
            self.redo_available.emit(self.can_redo)
            self.undo_stack_changed.emit()
            self.operation_undone.emit(previous_state.get('description', 'Undo'))
            
        finally:
            self._is_undoing = False
    
    def redo(self):
        """Redo the last undone operation"""
        if not self.can_redo:
            return
        
        self._is_redoing = True
        
        try:
            # Save current state for undo
            current_state = self._create_document_snapshot()
            self._undo_stack.append(current_state)
            
            # Restore next state
            next_state = self._redo_stack.pop()
            self._restore_document_snapshot(next_state)
            
            # Emit signals
            self.undo_available.emit(self.can_undo)
            self.redo_available.emit(self.can_redo)
            self.undo_stack_changed.emit()
            self.operation_redone.emit(next_state.get('description', 'Redo'))
            
        finally:
            self._is_redoing = False
    
    def clear_undo_stack(self):
        """Clear the undo stack"""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.undo_available.emit(False)
        self.redo_available.emit(False)
        self.undo_stack_changed.emit()
    
    def get_undo_operations(self) -> List[str]:
        """Get list of available undo operations"""
        return [state.get('description', 'Operation') for state in self._undo_stack]
    
    def get_redo_operations(self) -> List[str]:
        """Get list of available redo operations"""
        return [state.get('description', 'Operation') for state in self._redo_stack]
    
    def _create_document_snapshot(self) -> Dict[str, Any]:
        """Create a snapshot of the current document state"""
        document = self._document_viewmodel.document
        
        # Snapshot all objects
        objects_snapshot = {}
        for object_id, cad_object in document.objects.items():
            objects_snapshot[object_id] = {
                'object_type': cad_object.object_type,
                'points': [(p.x, p.y) for p in cad_object.points],
                'properties': cad_object.properties.copy(),
                'layer_id': cad_object.layer_id,
                'visible': cad_object.visible,
                'locked': cad_object.locked
            }
        
        # Snapshot layer manager
        layers_snapshot = {}
        for layer_id, layer in document.layer_manager.layers.items():
            layers_snapshot[layer_id] = {
                'name': layer.properties.name,
                'visible': layer.properties.visible,
                'locked': layer.properties.locked,
                'color': layer.properties.color,
                'line_width': layer.properties.line_width,
                'line_style': layer.properties.line_style,
                'layer_type': layer.properties.layer_type,
                'objects': layer.objects.copy()
            }
        
        # Snapshot selection
        selection_snapshot = self._document_viewmodel.selected_object_ids.copy()
        
        return {
            'objects': objects_snapshot,
            'layers': layers_snapshot,
            'selection': selection_snapshot,
            'document_modified': document.modified,
            'filename': document.filename
        }
    
    def _restore_document_snapshot(self, snapshot: Dict[str, Any]):
        """Restore document state from snapshot"""
        document = self._document_viewmodel.document
        
        # Clear current document
        document.objects.clear()
        document.layer_manager.layers.clear()
        
        # Restore layers
        for layer_id, layer_data in snapshot['layers'].items():
            layer = document.layer_manager.get_layer(layer_id)
            if not layer:
                # Create layer if it doesn't exist
                layer = document.layer_manager.add_layer(layer_data['name'])
                layer = document.layer_manager.get_layer(layer_id)
            
            # Restore layer properties
            layer.properties.visible = layer_data['visible']
            layer.properties.locked = layer_data['locked']
            layer.properties.color = layer_data['color']
            layer.properties.line_width = layer_data['line_width']
            layer.properties.line_style = layer_data['line_style']
            layer.properties.layer_type = layer_data['layer_type']
            layer.objects = layer_data['objects']
        
        # Restore objects
        for object_id, object_data in snapshot['objects'].items():
            # Create points
            points = [Point(x, y) for x, y in object_data['points']]
            
            # Create CAD object
            cad_object = CADObject(
                object_data['object_type'],
                points,
                object_data['properties']
            )
            cad_object.object_id = object_id  # Preserve original ID
            cad_object.layer_id = object_data['layer_id']
            cad_object.visible = object_data['visible']
            cad_object.locked = object_data['locked']
            
            # Add to document
            document.objects[object_id] = cad_object
        
        # Restore selection
        self._document_viewmodel._selected_object_ids = snapshot['selection']
        
        # Restore document properties
        document.modified = snapshot['document_modified']
        document.filename = snapshot['filename']
        
        # Emit document change signals
        self._document_viewmodel.document_changed.emit()
        if document.modified:
            self._document_viewmodel.document_modified.emit()
    
    def _on_document_modified(self):
        """Handle document modification"""
        if not self._is_undoing and not self._is_redoing:
            # Auto-save state for undo
            self.save_state("Document Modified")
    
    def _on_object_added(self, object_id: str, cad_object: CADObject):
        """Handle object addition"""
        if not self._is_undoing and not self._is_redoing:
            self.save_state(f"Added {cad_object.object_type.value}")
    
    def _on_object_removed(self, object_id: str):
        """Handle object removal"""
        if not self._is_undoing and not self._is_redoing:
            self.save_state("Object Removed")
    
    def _on_object_moved(self, object_id: str, dx: float, dy: float):
        """Handle object movement"""
        if not self._is_undoing and not self._is_redoing:
            self.save_state("Object Moved")
    
    def begin_operation(self, description: str):
        """Begin a compound operation"""
        # This could be used for grouping multiple operations
        # For now, just save the current state
        self.save_state(description)
    
    def end_operation(self):
        """End a compound operation"""
        # This could be used for grouping multiple operations
        # For now, just save the current state
        self.save_state("Operation Complete") 