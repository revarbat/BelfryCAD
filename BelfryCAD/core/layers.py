"""
Layer management system for PyTkCAD.

This module provides functionality for managing drawing layers,
including layer creation, deletion, properties, and object management.
Translated from the original layers.tcl file.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field


@dataclass
class Layer:
    """Represents a drawing layer with its properties and contained objects."""

    layer_id: int
    name: str
    visible: bool = True
    locked: bool = False
    color: str = "black"
    cut_bit: int = 0
    cut_depth: float = 0.0
    objects: List[int] = field(default_factory=list)


class LayerManager:
    """
    Manages layers for a CAD document.

    This class handles layer creation, deletion, property management,
    and object-to-layer associations.
    """

    def __init__(self, canvas_id: str = "default"):
        """
        Initialize the layer manager.

        Args:
            canvas_id: Identifier for the canvas/document this manager serves
        """
        self.canvas_id = canvas_id
        self._layer_counter = 0
        self._layers: Dict[int, Layer] = {}
        self._layer_order: List[int] = []
        self._current_layer_id = -1

    def init_layers(self) -> None:
        """Initialize the layer system with a default layer."""
        self._layer_counter = 0
        self._layers.clear()
        self._layer_order.clear()
        self._current_layer_id = -1

        # Create and set the first layer as current
        first_layer_id = self.create_layer()
        self.set_current_layer(first_layer_id)

    def create_layer(self, name: str = "", with_undo: bool = True) -> int:
        """
        Create a new layer.

        Args:
            name: Name for the new layer. If empty, auto-generates a name.
            with_undo: Whether to remember this action for undo (not implemented yet)

        Returns:
            The ID of the newly created layer
        """
        return self._create_layer_internal(name, -1)

    def _create_layer_internal(self, name: str = "", layer_id: int = -1) -> int:
        """
        Internal layer creation method.

        Args:
            name: Name for the new layer
            layer_id: Specific ID to use (-1 for auto-increment)

        Returns:
            The ID of the newly created layer
        """
        if layer_id == -1:
            self._layer_counter += 1
            layer_id = self._layer_counter
        else:
            # Update counter if we're using a specific ID
            if layer_id > self._layer_counter:
                self._layer_counter = layer_id

        if not name:
            name = f"Layer {layer_id}"

        layer = Layer(
            layer_id=layer_id,
            name=name,
            visible=True,
            locked=False,
            color="black",
            cut_bit=0,
            cut_depth=0.0,
            objects=[]
        )

        self._layers[layer_id] = layer
        self._layer_order.append(layer_id)

        return layer_id

    def delete_layer(self, layer_id: int, with_undo: bool = True) -> bool:
        """
        Delete a layer and all its objects.

        Args:
            layer_id: ID of the layer to delete
            with_undo: Whether to remember this action for undo

        Returns:
            True if layer was deleted, False if it didn't exist
        """
        if layer_id not in self._layers:
            return False

        layer = self._layers[layer_id]

        # TODO: Delete all objects in this layer
        # This would require integration with the object management system
        # for objid in layer.objects:
        #     delete_object(objid)

        # If this was the current layer, switch to another one
        if self._current_layer_id == layer_id:
            remaining_layers = [lid for lid in self._layer_order if lid != layer_id]
            if remaining_layers:
                # Try to switch to the next layer, or first if we're deleting the last
                try:
                    current_index = self._layer_order.index(layer_id)
                    new_current = remaining_layers[min(current_index, len(remaining_layers) - 1)]
                except (ValueError, IndexError):
                    new_current = remaining_layers[0]
                self.set_current_layer(new_current)
            else:
                self._current_layer_id = -1

        # Remove from data structures
        del self._layers[layer_id]
        self._layer_order.remove(layer_id)

        # Reset counters if no layers remain
        if not self._layers:
            self._layer_counter = 0
            self._current_layer_id = -1

        return True

    def layer_exists(self, layer_id: int) -> bool:
        """Check if a layer exists."""
        return layer_id in self._layers

    def get_layer_by_name(self, name: str) -> Optional[int]:
        """
        Find a layer ID by name.

        Args:
            name: Name to search for

        Returns:
            Layer ID if found, None otherwise
        """
        for layer_id, layer in self._layers.items():
            if layer.name == name:
                return layer_id
        return None

    def get_layer_ids(self) -> List[int]:
        """Get all layer IDs in order."""
        return self._layer_order.copy()

    def get_current_layer(self) -> int:
        """
        Get the current layer ID.

        Returns:
            Current layer ID, or -1 if no layers exist
        """
        if not self._layers:
            return -1

        if self._current_layer_id == -1 or self._current_layer_id not in self._layers:
            # Auto-create a layer if none exist
            if not self._layers:
                self._current_layer_id = self.create_layer()
            else:
                self._current_layer_id = self._layer_order[0]

        return self._current_layer_id

    def set_current_layer(self, layer_id: int) -> bool:
        """
        Set the current layer.

        Args:
            layer_id: ID of layer to make current

        Returns:
            True if successful, False if layer doesn't exist
        """
        if layer_id not in self._layers:
            return False
        self._current_layer_id = layer_id
        return True

    def get_layer_position(self, layer_id: int) -> int:
        """
        Get the position of a layer in the layer order.

        Args:
            layer_id: Layer ID to find

        Returns:
            Position index, or -1 if not found
        """
        try:
            return self._layer_order.index(layer_id)
        except ValueError:
            return -1

    def reorder_layer(self, layer_id: int, new_position: int) -> bool:
        """
        Move a layer to a new position in the layer order.

        Args:
            layer_id: Layer to move
            new_position: New position (0 = top)

        Returns:
            True if successful, False if layer doesn't exist
        """
        if layer_id not in self._layers:
            return False

        try:
            old_position = self._layer_order.index(layer_id)
            self._layer_order.pop(old_position)
            self._layer_order.insert(new_position, layer_id)
            return True
        except ValueError:
            return False

    def reorder_layers(self, new_order: List[int]) -> bool:
        """
        Reorder all layers according to a new ordering.

        Args:
            new_order: List of layer IDs in desired order

        Returns:
            True if successful, False if invalid order provided
        """
        # Verify all layers exist and no duplicates
        if (len(new_order) != len(self._layer_order) or
            set(new_order) != set(self._layer_order)):
            return False

        # Update the order
        self._layer_order = new_order.copy()
        return True

    # Layer property getters and setters
    def get_layer_name(self, layer_id: int) -> str:
        """Get layer name."""
        if layer_id in self._layers:
            return self._layers[layer_id].name
        return ""

    def set_layer_name(self, layer_id: int, name: str) -> bool:
        """Set layer name."""
        if layer_id in self._layers:
            self._layers[layer_id].name = name
            return True
        return False

    def is_layer_visible(self, layer_id: int) -> bool:
        """Check if layer is visible."""
        if layer_id in self._layers:
            return self._layers[layer_id].visible
        return False

    def set_layer_visible(self, layer_id: int, visible: bool) -> bool:
        """Set layer visibility."""
        if layer_id in self._layers:
            self._layers[layer_id].visible = visible
            return True
        return False

    def is_layer_locked(self, layer_id: int) -> bool:
        """Check if layer is locked."""
        if layer_id in self._layers:
            return self._layers[layer_id].locked
        return False

    def set_layer_locked(self, layer_id: int, locked: bool) -> bool:
        """Set layer locked state."""
        if layer_id in self._layers:
            self._layers[layer_id].locked = locked
            return True
        return False

    def get_layer_color(self, layer_id: int) -> str:
        """Get layer color."""
        if layer_id in self._layers:
            return self._layers[layer_id].color
        return "black"

    def set_layer_color(self, layer_id: int, color: str) -> bool:
        """Set layer color."""
        if layer_id in self._layers:
            self._layers[layer_id].color = color
            return True
        return False

    def get_layer_cut_bit(self, layer_id: int) -> int:
        """Get layer cut bit setting."""
        if layer_id in self._layers:
            return self._layers[layer_id].cut_bit
        return 0

    def set_layer_cut_bit(self, layer_id: int, cut_bit: int) -> bool:
        """Set layer cut bit setting."""
        if layer_id in self._layers:
            self._layers[layer_id].cut_bit = cut_bit
            return True
        return False

    def get_layer_cut_depth(self, layer_id: int) -> float:
        """Get layer cut depth setting."""
        if layer_id in self._layers:
            return self._layers[layer_id].cut_depth
        return 0.0

    def set_layer_cut_depth(self, layer_id: int, cut_depth: float) -> bool:
        """Set layer cut depth setting."""
        if layer_id in self._layers:
            self._layers[layer_id].cut_depth = cut_depth
            return True
        return False

    # Object management methods
    def get_layer_objects(self, layer_id: int) -> List[int]:
        """Get list of object IDs in a layer."""
        if layer_id in self._layers:
            return self._layers[layer_id].objects.copy()
        return []

    def add_object_to_layer(self, layer_id: int, object_id: int) -> bool:
        """
        Add an object to a layer.

        Args:
            layer_id: Layer to add object to
            object_id: Object ID to add

        Returns:
            True if successful, False if layer doesn't exist
        """
        if layer_id in self._layers:
            layer = self._layers[layer_id]
            if object_id not in layer.objects:
                layer.objects.append(object_id)
            return True
        return False

    def remove_object_from_layer(self, layer_id: int, object_id: int) -> bool:
        """
        Remove an object from a layer.

        Args:
            layer_id: Layer to remove object from
            object_id: Object ID to remove

        Returns:
            True if successful, False if layer doesn't exist or object not in layer
        """
        if layer_id in self._layers:
            layer = self._layers[layer_id]
            try:
                layer.objects.remove(object_id)
                return True
            except ValueError:
                pass  # Object wasn't in the layer
        return False

    def arrange_object_in_layer(self, layer_id: int, object_id: int, relative_position: Union[str, int]) -> bool:
        """
        Arrange an object's position within its layer.

        Args:
            layer_id: Layer containing the object
            object_id: Object to move
            relative_position: Either "top", "bottom", or integer offset

        Returns:
            True if successful, False otherwise
        """
        if layer_id not in self._layers:
            return False

        layer = self._layers[layer_id]

        try:
            current_pos = layer.objects.index(object_id)
        except ValueError:
            return False  # Object not in layer

        # Remove object from current position
        layer.objects.pop(current_pos)

        # Calculate new position
        if relative_position == "top":
            new_pos = 0
        elif relative_position == "bottom":
            new_pos = len(layer.objects)  # Append to end
        else:
            # Relative integer offset
            new_pos = max(0, min(len(layer.objects), current_pos + int(relative_position)))

        # Insert at new position
        layer.objects.insert(new_pos, object_id)
        return True

    def move_object_to_layer(self, object_id: int, from_layer_id: int, to_layer_id: int) -> bool:
        """
        Move an object from one layer to another.

        Args:
            object_id: Object to move
            from_layer_id: Source layer
            to_layer_id: Destination layer

        Returns:
            True if successful, False if either layer doesn't exist or object not found
        """
        # Check both layers exist
        if from_layer_id not in self._layers or to_layer_id not in self._layers:
            return False

        # Remove from source layer
        if not self.remove_object_from_layer(from_layer_id, object_id):
            return False

        # Add to destination layer
        return self.add_object_to_layer(to_layer_id, object_id)

    # Serialization methods
    def serialize_layer(self, layer_id: int) -> Dict[str, Any]:
        """
        Serialize a layer to a dictionary.

        Args:
            layer_id: Layer ID to serialize

        Returns:
            Dictionary containing layer data
        """
        if layer_id not in self._layers:
            return {}

        layer = self._layers[layer_id]
        return {
            "layerid": layer_id,
            "pos": self.get_layer_position(layer_id),
            "name": layer.name,
            "visible": layer.visible,
            "locked": layer.locked,
            "color": layer.color,
            "cutbit": layer.cut_bit,
            "cutdepth": layer.cut_depth
        }

    def deserialize_layer(self, layer_data: Dict[str, Any], force_new: bool = False) -> int:
        """
        Deserialize a layer from a dictionary.

        Args:
            layer_data: Dictionary containing layer data
            force_new: If True, always create a new layer ID

        Returns:
            Layer ID of the deserialized layer
        """
        required_fields = ["layerid", "name", "visible", "locked", "color", "cutbit", "cutdepth", "pos"]
        for field in required_fields:
            if field not in layer_data:
                raise ValueError(f"Serialization data missing required field: {field}")

        target_layer_id = layer_data["layerid"]
        if force_new:
            target_layer_id = -1

        if target_layer_id == -1:
            # Create new layer
            layer_id = self._create_layer_internal(layer_data["name"])
        elif not self.layer_exists(target_layer_id):
            # Create layer with specific ID
            layer_id = self._create_layer_internal(layer_data["name"], target_layer_id)
        else:
            # Update existing layer
            layer_id = target_layer_id
            self._layers[layer_id].name = layer_data["name"]

        # Set all properties
        layer = self._layers[layer_id]
        layer.visible = layer_data["visible"]
        layer.locked = layer_data["locked"]
        layer.color = layer_data["color"]
        layer.cut_bit = layer_data["cutbit"]
        layer.cut_depth = layer_data["cutdepth"]

        # Reorder to correct position
        self.reorder_layer(layer_id, layer_data["pos"])

        return layer_id

    def get_layer_info(self, layer_id: int) -> Optional[Layer]:
        """
        Get complete layer information.

        Args:
            layer_id: Layer ID to get info for

        Returns:
            Layer object if exists, None otherwise
        """
        return self._layers.get(layer_id)

    def get_all_layers(self) -> Dict[int, Layer]:
        """Get all layers as a dictionary."""
        return self._layers.copy()

    def get_layer_data(self, layer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get layer data in a format compatible with the drawing system.

        Args:
            layer_id: Layer ID to get data for

        Returns:
            Dictionary with layer data or None if layer doesn't exist
        """
        if layer_id not in self._layers:
            return None

        layer = self._layers[layer_id]
        return {
            'id': str(layer_id),  # Convert to string for UI compatibility
            'name': layer.name,
            'color': layer.color,
            'visible': layer.visible,
            'locked': layer.locked,
            'cut_bit': layer.cut_bit,
            'cut_depth': layer.cut_depth,
            'object_count': len(layer.objects)
        }

    def get_all_layers_data(self) -> List[Dict[str, Any]]:
        """
        Get data for all layers in order, formatted for the layer window.

        Returns:
            List of layer data dictionaries
        """
        layers_data = []
        for layer_id in self._layer_order:
            layer_data = self.get_layer_data(layer_id)
            if layer_data:
                layers_data.append(layer_data)
        return layers_data
