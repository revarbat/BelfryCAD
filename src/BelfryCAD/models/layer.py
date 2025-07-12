"""
Layer business logic model.

This module contains pure business logic for layers with no UI dependencies.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import uuid


class LayerType(Enum):
    """Types of layers"""
    NORMAL = "normal"
    CONSTRUCTION = "construction"
    DIMENSION = "dimension"
    HATCH = "hatch"


@dataclass
class LayerProperties:
    """Layer properties with pure business logic"""
    name: str
    visible: bool = True
    locked: bool = False
    color: str = "#000000"
    line_width: float = 1.0
    line_style: str = "solid"
    layer_type: LayerType = LayerType.NORMAL


class Layer:
    """Pure business logic for layers - no UI dependencies"""
    
    def __init__(self, name: str, layer_id: Optional[str] = None):
        self.layer_id = layer_id or str(uuid.uuid4())
        self.properties = LayerProperties(name=name)
        self.objects: List[str] = []  # List of object IDs
    
    def add_object(self, object_id: str):
        """Add an object to this layer"""
        if object_id not in self.objects:
            self.objects.append(object_id)
    
    def remove_object(self, object_id: str):
        """Remove an object from this layer"""
        if object_id in self.objects:
            self.objects.remove(object_id)
    
    def is_visible(self) -> bool:
        """Check if layer is visible"""
        return self.properties.visible
    
    def is_locked(self) -> bool:
        """Check if layer is locked"""
        return self.properties.locked
    
    def get_color(self) -> str:
        """Get layer color"""
        return self.properties.color
    
    def set_color(self, color: str):
        """Set layer color"""
        self.properties.color = color
    
    def get_line_width(self) -> float:
        """Get line width"""
        return self.properties.line_width
    
    def set_line_width(self, width: float):
        """Set line width"""
        self.properties.line_width = width
    
    def toggle_visibility(self):
        """Toggle layer visibility"""
        self.properties.visible = not self.properties.visible
    
    def toggle_lock(self):
        """Toggle layer lock"""
        self.properties.locked = not self.properties.locked


class LayerManager:
    """Manages layers with pure business logic"""
    
    def __init__(self):
        self.layers: Dict[str, Layer] = {}
        self._create_default_layers()
    
    def _create_default_layers(self):
        """Create default layers"""
        default_layer = Layer("Default")
        self.layers[default_layer.layer_id] = default_layer
    
    def add_layer(self, name: str) -> str:
        """Add a new layer and return its ID"""
        layer = Layer(name)
        self.layers[layer.layer_id] = layer
        return layer.layer_id
    
    def remove_layer(self, layer_id: str) -> bool:
        """Remove a layer if it exists and is not the last layer"""
        if layer_id in self.layers and len(self.layers) > 1:
            del self.layers[layer_id]
            return True
        return False
    
    def get_layer(self, layer_id: str) -> Optional[Layer]:
        """Get layer by ID"""
        return self.layers.get(layer_id)
    
    def get_all_layers(self) -> List[Layer]:
        """Get all layers"""
        return list(self.layers.values())
    
    def get_visible_layers(self) -> List[Layer]:
        """Get all visible layers"""
        return [layer for layer in self.layers.values() if layer.is_visible()]
    
    def get_unlocked_layers(self) -> List[Layer]:
        """Get all unlocked layers"""
        return [layer for layer in self.layers.values() if not layer.is_locked()]
    
    def move_object_to_layer(self, object_id: str, from_layer_id: str, to_layer_id: str):
        """Move an object from one layer to another"""
        from_layer = self.get_layer(from_layer_id)
        to_layer = self.get_layer(to_layer_id)
        
        if from_layer and to_layer:
            from_layer.remove_object(object_id)
            to_layer.add_object(object_id)
    
    def get_layer_for_object(self, object_id: str) -> Optional[Layer]:
        """Find which layer contains an object"""
        for layer in self.layers.values():
            if object_id in layer.objects:
                return layer
        return None 