"""
Layer ViewModel for BelfryCAD.

This ViewModel handles presentation logic for layers and emits signals
for UI updates when layer properties change.
"""

from typing import List, Optional
from PySide6.QtCore import QObject, Signal

from ...models.layer import Layer, LayerManager


class LayerViewModel(QObject):
    """Presentation logic for layers with signals"""
    
    # Layer signals
    layer_added = Signal(str, Layer)  # layer_id, layer
    layer_removed = Signal(str)  # layer_id
    layer_visibility_changed = Signal(str, bool)  # layer_id, is_visible
    layer_lock_changed = Signal(str, bool)  # layer_id, is_locked
    layer_color_changed = Signal(str, str)  # layer_id, color
    layer_name_changed = Signal(str, str)  # layer_id, name
    active_layer_changed = Signal(str)  # layer_id
    
    def __init__(self, layer_manager: LayerManager):
        super().__init__()
        self._layer_manager = layer_manager
        self._active_layer_id: Optional[str] = None
        
        # Set active layer to first layer
        if layer_manager.get_all_layers():
            self._active_layer_id = layer_manager.get_all_layers()[0].layer_id
    
    @property
    def active_layer_id(self) -> Optional[str]:
        """Get active layer ID"""
        return self._active_layer_id
    
    @property
    def layer_manager(self) -> LayerManager:
        """Get the underlying layer manager"""
        return self._layer_manager
    
    def get_all_layers(self) -> List[Layer]:
        """Get all layers"""
        return self._layer_manager.get_all_layers()
    
    def get_visible_layers(self) -> List[Layer]:
        """Get visible layers"""
        return self._layer_manager.get_visible_layers()
    
    def get_unlocked_layers(self) -> List[Layer]:
        """Get unlocked layers"""
        return self._layer_manager.get_unlocked_layers()
    
    def get_layer(self, layer_id: str) -> Optional[Layer]:
        """Get layer by ID"""
        return self._layer_manager.get_layer(layer_id)
    
    def add_layer(self, name: str) -> str:
        """Add a new layer"""
        layer_id = self._layer_manager.add_layer(name)
        layer = self._layer_manager.get_layer(layer_id)
        if layer:
            self.layer_added.emit(layer_id, layer)
        return layer_id
    
    def remove_layer(self, layer_id: str) -> bool:
        """Remove a layer"""
        if self._layer_manager.remove_layer(layer_id):
            self.layer_removed.emit(layer_id)
            
            # If we removed the active layer, set a new active layer
            if layer_id == self._active_layer_id:
                layers = self.get_all_layers()
                if layers:
                    self.set_active_layer(layers[0].layer_id)
                else:
                    self._active_layer_id = None
                    self.active_layer_changed.emit("")
            
            return True
        return False
    
    def set_active_layer(self, layer_id: str):
        """Set active layer"""
        if self._active_layer_id != layer_id and self._layer_manager.get_layer(layer_id):
            self._active_layer_id = layer_id
            self.active_layer_changed.emit(layer_id)
    
    def get_active_layer(self) -> Optional[Layer]:
        """Get active layer"""
        if self._active_layer_id:
            return self._layer_manager.get_layer(self._active_layer_id)
        return None
    
    def toggle_layer_visibility(self, layer_id: str):
        """Toggle layer visibility"""
        layer = self._layer_manager.get_layer(layer_id)
        if layer:
            layer.toggle_visibility()
            self.layer_visibility_changed.emit(layer_id, layer.is_visible())
    
    def toggle_layer_lock(self, layer_id: str):
        """Toggle layer lock"""
        layer = self._layer_manager.get_layer(layer_id)
        if layer:
            layer.toggle_lock()
            self.layer_lock_changed.emit(layer_id, layer.is_locked())
    
    def set_layer_color(self, layer_id: str, color: str):
        """Set layer color"""
        layer = self._layer_manager.get_layer(layer_id)
        if layer:
            layer.set_color(color)
            self.layer_color_changed.emit(layer_id, color)
    
    def set_layer_name(self, layer_id: str, name: str):
        """Set layer name"""
        layer = self._layer_manager.get_layer(layer_id)
        if layer:
            layer.properties.name = name
            self.layer_name_changed.emit(layer_id, name)
    
    def get_layer_visibility(self, layer_id: str) -> bool:
        """Get layer visibility"""
        layer = self._layer_manager.get_layer(layer_id)
        return layer.is_visible() if layer else False
    
    def get_layer_lock(self, layer_id: str) -> bool:
        """Get layer lock state"""
        layer = self._layer_manager.get_layer(layer_id)
        return layer.is_locked() if layer else False
    
    def get_layer_color(self, layer_id: str) -> str:
        """Get layer color"""
        layer = self._layer_manager.get_layer(layer_id)
        return layer.get_color() if layer else "#000000"
    
    def get_layer_name(self, layer_id: str) -> str:
        """Get layer name"""
        layer = self._layer_manager.get_layer(layer_id)
        return layer.properties.name if layer else ""
    
    def move_object_to_layer(self, object_id: str, layer_id: str) -> bool:
        """Move an object to a different layer"""
        result = self._layer_manager.move_object_to_layer(object_id, "", layer_id)
        return result is not None
    
    def get_layer_for_object(self, object_id: str) -> Optional[Layer]:
        """Find which layer contains an object"""
        return self._layer_manager.get_layer_for_object(object_id)
    
    def get_objects_in_layer(self, layer_id: str) -> List[str]:
        """Get object IDs in a specific layer"""
        layer = self._layer_manager.get_layer(layer_id)
        return layer.objects if layer else [] 