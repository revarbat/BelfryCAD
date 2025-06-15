"""
Layer management system for PyTkCAD.

This module provides functionality for managing drawing layers,
including layer creation, deletion, properties, and object management.
Translated from the original layers.tcl file.
"""

from typing import Dict, List, Optional, Any, Union
from .layer_types import Layer
from BelfryCAD.core.undo_redo import (
    CreateLayerCommand, DeleteLayerCommand, ModifyLayerCommand, ReorderLayerCommand
)


class LayerManager:
    """
    Manages layers for a CAD document.

    This class handles layer creation, deletion, property management,
    and object-to-layer associations.
    """

    _next_id: int = 1
    
    def __init__(self, canvas_id: str = "default"):
        """
        Initialize the layer manager.

        Args:
            canvas_id: Identifier for the canvas/document this manager serves
        """
        self.canvas_id = canvas_id
        self._layers: List[Layer] = []
        self._current_layer: Optional[Layer] = None
        self._undo_manager = None

    def set_undo_manager(self, undo_manager):
        """Set the undo manager for this layer manager."""
        self._undo_manager = undo_manager

    def init_layers(self) -> None:
        """Initialize the layer system with a default layer."""
        self._layers.clear()
        self._current_layer = None

        # Create and set the first layer as current
        first_layer = self.create_layer()
        self.set_current_layer(first_layer)

    def create_layer(self, name: str = "", with_undo: bool = True) -> Layer:
        """
        Create a new layer.

        Args:
            name: Name for the new layer. If empty, auto-generates a name.
            with_undo: Whether to remember this action for undo

        Returns:
            The newly created Layer object
        """
        if not name:
            name = f"Layer {self._next_id}"
        self._next_id += 1

        if with_undo and self._undo_manager:
            command = CreateLayerCommand(self, name)
            if self._undo_manager.execute_command(command) and command.layer is not None:
                return command.layer
            # If command execution failed or layer is None, fall through to direct creation

        layer = Layer(
            name=name,
            visible=True,
            locked=False,
            color="black",
            cut_bit=0,
            cut_depth=0.0,
            objects=[]
        )

        self._layers.append(layer)
        return layer

    def delete_layer(self, layer: Layer, with_undo: bool = True) -> bool:
        """
        Delete a layer and all its objects.

        Args:
            layer: Layer object to delete
            with_undo: Whether to remember this action for undo

        Returns:
            True if layer was deleted, False if it didn't exist
        """
        if layer not in self._layers:
            return False

        if with_undo and self._undo_manager:
            command = DeleteLayerCommand(self, layer)
            return self._undo_manager.execute_command(command)

        # If this was the current layer, switch to another one
        if self._current_layer == layer:
            remaining_layers = [l for l in self._layers if l != layer]
            if remaining_layers:
                # Try to switch to the next layer, or first if we're deleting the last
                try:
                    current_index = self._layers.index(layer)
                    new_current = remaining_layers[min(
                        current_index, len(remaining_layers) - 1)]
                except (ValueError, IndexError):
                    new_current = remaining_layers[0]
                self.set_current_layer(new_current)
            else:
                self._current_layer = None

        # Remove from data structures
        self._layers.remove(layer)

        return True

    def layer_exists(self, layer: Layer) -> bool:
        """Check if a layer exists."""
        return layer in self._layers

    def get_layer_by_name(self, name: str) -> Optional[Layer]:
        """
        Find a layer by name.

        Args:
            name: Name to search for

        Returns:
            Layer object if found, None otherwise
        """
        for layer in self._layers:
            if layer.name == name:
                return layer
        return None

    def get_layers(self) -> List[Layer]:
        """Get all layers in order."""
        return self._layers.copy()

    def get_current_layer(self) -> Optional[Layer]:
        """
        Get the current layer.

        Returns:
            Current layer object, or None if no layers exist
        """
        if not self._layers:
            return None

        if self._current_layer is None or self._current_layer not in self._layers:
            # Auto-create a layer if none exist
            if not self._layers:
                self._current_layer = self.create_layer()
            else:
                self._current_layer = self._layers[0]

        return self._current_layer

    def set_current_layer(self, layer: Layer) -> bool:
        """
        Set the current layer.

        Args:
            layer: Layer object to make current

        Returns:
            True if successful, False if layer doesn't exist
        """
        if layer not in self._layers:
            return False
        self._current_layer = layer
        return True

    def get_layer_position(self, layer: Layer) -> int:
        """
        Get the position of a layer in the layer order.

        Args:
            layer: Layer object to find

        Returns:
            Position index, or -1 if not found
        """
        try:
            return self._layers.index(layer)
        except ValueError:
            return -1

    def reorder_layer(self, layer: Layer, new_position: int, with_undo: bool = True) -> bool:
        """
        Move a layer to a new position in the layer order.

        Args:
            layer: Layer to move
            new_position: New position (0 = top)
            with_undo: Whether to remember this action for undo

        Returns:
            True if successful, False if layer doesn't exist
        """
        if layer not in self._layers:
            return False

        if with_undo and self._undo_manager:
            command = ReorderLayerCommand(self, layer, new_position)
            return self._undo_manager.execute_command(command)

        try:
            old_position = self._layers.index(layer)
            self._layers.pop(old_position)
            self._layers.insert(new_position, layer)
            return True
        except ValueError:
            return False

    def reorder_layers(self, new_order: List[Layer]) -> bool:
        """
        Reorder all layers according to a new ordering.

        Args:
            new_order: List of layers in desired order

        Returns:
            True if successful, False if invalid order provided
        """
        # Verify all layers exist and no duplicates
        if (len(new_order) != len(self._layers) or
                set(new_order) != set(self._layers)):
            return False

        # Update the order
        self._layers = new_order.copy()
        return True

    # Layer property getters and setters
    def get_layer_name(self, layer: Layer) -> str:
        """Get layer name."""
        return layer.name

    def set_layer_name(self, layer: Layer, name: str, with_undo: bool = True) -> bool:
        """Set layer name."""
        if layer in self._layers:
            if with_undo and self._undo_manager:
                command = ModifyLayerCommand(self, layer, {'name': name})
                return self._undo_manager.execute_command(command)
            layer.name = name
            return True
        return False

    def is_layer_visible(self, layer: Layer) -> bool:
        """Check if layer is visible."""
        return layer.visible

    def set_layer_visible(self, layer: Layer, visible: bool, with_undo: bool = True) -> bool:
        """Set layer visibility."""
        if layer in self._layers:
            if with_undo and self._undo_manager:
                command = ModifyLayerCommand(self, layer, {'visible': visible})
                return self._undo_manager.execute_command(command)
            layer.visible = visible
            return True
        return False

    def is_layer_locked(self, layer: Layer) -> bool:
        """Check if layer is locked."""
        return layer.locked

    def set_layer_locked(self, layer: Layer, locked: bool, with_undo: bool = True) -> bool:
        """Set layer locked state."""
        if layer in self._layers:
            if with_undo and self._undo_manager:
                command = ModifyLayerCommand(self, layer, {'locked': locked})
                return self._undo_manager.execute_command(command)
            layer.locked = locked
            return True
        return False

    def get_layer_color(self, layer: Layer) -> str:
        """Get layer color."""
        return layer.color

    def set_layer_color(self, layer: Layer, color: str, with_undo: bool = True) -> bool:
        """Set layer color."""
        if layer in self._layers:
            if with_undo and self._undo_manager:
                command = ModifyLayerCommand(self, layer, {'color': color})
                return self._undo_manager.execute_command(command)
            layer.color = color
            return True
        return False

    def get_layer_cut_bit(self, layer: Layer) -> int:
        """Get layer cut bit setting."""
        return layer.cut_bit

    def set_layer_cut_bit(self, layer: Layer, cut_bit: int, with_undo: bool = True) -> bool:
        """Set layer cut bit setting."""
        if layer in self._layers:
            if with_undo and self._undo_manager:
                command = ModifyLayerCommand(self, layer, {'cut_bit': cut_bit})
                return self._undo_manager.execute_command(command)
            layer.cut_bit = cut_bit
            return True
        return False

    def get_layer_cut_depth(self, layer: Layer) -> float:
        """Get layer cut depth setting."""
        return layer.cut_depth

    def set_layer_cut_depth(self, layer: Layer, cut_depth: float, with_undo: bool = True) -> bool:
        """Set layer cut depth setting."""
        if layer in self._layers:
            if with_undo and self._undo_manager:
                command = ModifyLayerCommand(self, layer, {'cut_depth': cut_depth})
                return self._undo_manager.execute_command(command)
            layer.cut_depth = cut_depth
            return True
        return False

    # Object management methods
    def get_layer_objects(self, layer: Layer) -> List[int]:
        """Get list of object IDs in a layer."""
        return layer.objects.copy()

    def add_object_to_layer(self, layer: Layer, object_id: int) -> bool:
        """
        Add an object to a layer.

        Args:
            layer: Layer to add object to
            object_id: Object ID to add

        Returns:
            True if successful, False if layer doesn't exist
        """
        if layer in self._layers:
            if object_id not in layer.objects:
                layer.objects.append(object_id)
            return True
        return False

    def remove_object_from_layer(self, layer: Layer, object_id: int) -> bool:
        """
        Remove an object from a layer.

        Args:
            layer: Layer to remove object from
            object_id: Object ID to remove

        Returns:
            True if successful, False if layer doesn't exist or object not in layer
        """
        if layer in self._layers:
            try:
                layer.objects.remove(object_id)
                return True
            except ValueError:
                pass  # Object wasn't in the layer
        return False

    def arrange_object_in_layer(self, layer: Layer, object_id: int, relative_position: Union[str, int]) -> bool:
        """
        Arrange an object's position within its layer.

        Args:
            layer: Layer containing the object
            object_id: Object to move
            relative_position: Either "top", "bottom", or integer offset

        Returns:
            True if successful, False otherwise
        """
        if layer not in self._layers:
            return False

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
            new_pos = max(0, min(len(layer.objects),
                          current_pos + int(relative_position)))

        # Insert at new position
        layer.objects.insert(new_pos, object_id)
        return True

    def move_object_to_layer(self, object_id: int, from_layer: Layer, to_layer: Layer) -> bool:
        """
        Move an object from one layer to another.

        Args:
            object_id: Object to move
            from_layer: Source layer
            to_layer: Destination layer

        Returns:
            True if successful, False if either layer doesn't exist or object not found
        """
        # Check both layers exist
        if from_layer not in self._layers or to_layer not in self._layers:
            return False

        # Remove from source layer
        if not self.remove_object_from_layer(from_layer, object_id):
            return False

        # Add to destination layer
        return self.add_object_to_layer(to_layer, object_id)

    # Serialization methods
    def serialize_layer(self, layer: Layer) -> Dict[str, Any]:
        """
        Serialize a layer to a dictionary.

        Args:
            layer: Layer object to serialize

        Returns:
            Dictionary containing layer data
        """
        if layer not in self._layers:
            return {}

        return {
            "pos": self.get_layer_position(layer),
            "name": layer.name,
            "visible": layer.visible,
            "locked": layer.locked,
            "color": layer.color,
            "cutbit": layer.cut_bit,
            "cutdepth": layer.cut_depth
        }

    def deserialize_layer(self, layer_data: Dict[str, Any], force_new: bool = False) -> Layer:
        """
        Deserialize a layer from a dictionary.

        Args:
            layer_data: Dictionary containing layer data
            force_new: If True, always create a new layer

        Returns:
            Layer object of the deserialized layer
        """
        required_fields = ["name", "visible", "locked", "color", "cutbit", "cutdepth", "pos"]
        for field in required_fields:
            if field not in layer_data:
                raise ValueError(f"Serialization data missing required field: {field}")

        # Create new layer
        layer = self.create_layer(layer_data["name"])

        # Set all properties
        layer.visible = layer_data["visible"]
        layer.locked = layer_data["locked"]
        layer.color = layer_data["color"]
        layer.cut_bit = layer_data["cutbit"]
        layer.cut_depth = layer_data["cutdepth"]

        # Reorder to correct position
        self.reorder_layer(layer, layer_data["pos"])

        return layer

    def get_layer_info(self, layer: Layer) -> Optional[Layer]:
        """
        Get complete layer information.

        Args:
            layer: Layer object to get info for

        Returns:
            Layer object if exists, None otherwise
        """
        return layer if layer in self._layers else None

    def get_all_layers(self) -> List[Layer]:
        """Get all layers as a list."""
        return self._layers.copy()

    def get_layer_data(self, layer: Layer) -> Optional[Dict[str, Any]]:
        """
        Get layer data in a format compatible with the drawing system.

        Args:
            layer: Layer object to get data for

        Returns:
            Dictionary with layer data or None if layer doesn't exist
        """
        if layer not in self._layers:
            return None

        return {
            'id': str(self.get_layer_position(layer)),  # Convert position to string for UI compatibility
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
        for layer in self._layers:
            layer_data = self.get_layer_data(layer)
            if layer_data:
                layers_data.append(layer_data)
        return layers_data
