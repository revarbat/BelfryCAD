"""
Undo/Redo Command System for BelfryCAD

This module provides a command pattern implementation for undo/redo functionality,
based on design patterns from the TCL implementation.
"""

from typing import List, Optional, Any, Dict
from abc import ABC, abstractmethod
import copy
from dataclasses import dataclass

from BelfryCAD.core.cad_objects import CADObject
from BelfryCAD.core.layer_types import Layer


@dataclass
class ObjectState:
    """Represents the state of a CAD object for undo/redo operations."""
    object_id: int
    object_type: Any
    coords: List[Any]
    attributes: Dict[str, Any]
    layer: Optional[str] = None
    visible: bool = True
    selected: bool = False


class Command(ABC):
    """Abstract base class for all undoable commands."""

    def __init__(self, description: str = ""):
        self.description = description

    @abstractmethod
    def execute(self) -> bool:
        """Execute the command. Returns True if successful."""
        pass

    @abstractmethod
    def undo(self) -> bool:
        """Undo the command. Returns True if successful."""
        pass

    def redo(self) -> bool:
        """Redo the command. Default implementation calls execute."""
        return self.execute()


class CreateObjectCommand(Command):
    """Command to create a new CAD object."""

    def __init__(self, document, obj: CADObject, description: str = "Create Object"):
        super().__init__(description)
        self.document = document
        self.obj = obj
        self.object_id = obj.object_id

    def execute(self) -> bool:
        """Add the object to the document."""
        try:
            if hasattr(self.document, 'objects'):
                self.document.objects.add_object(self.obj)
                return True
        except Exception as e:
            print(f"Error executing CreateObjectCommand: {e}")
        return False

    def undo(self) -> bool:
        """Remove the object from the document."""
        try:
            if hasattr(self.document, 'objects'):
                self.document.objects.remove_object(self.object_id)
                return True
        except Exception as e:
            print(f"Error undoing CreateObjectCommand: {e}")
        return False


class DeleteObjectCommand(Command):
    """Command to delete a CAD object."""

    def __init__(self, document, obj: CADObject, description: str = "Delete Object"):
        super().__init__(description)
        self.document = document
        self.object_state = self._capture_object_state(obj)

    def _capture_object_state(self, obj: CADObject) -> ObjectState:
        """Capture the complete state of an object."""
        return ObjectState(
            object_id=obj.object_id,
            object_type=obj.object_type,
            coords=copy.deepcopy(obj.coords),
            attributes=copy.deepcopy(obj.attributes),
            layer=getattr(obj, 'layer', None),
            visible=getattr(obj, 'visible', True),
            selected=getattr(obj, 'selected', False)
        )

    def _restore_object(self, state: ObjectState) -> CADObject:
        """Restore an object from its state."""
        from BelfryCAD.core.cad_objects import CADObject
        obj = CADObject(
            object_type=state.object_type,
            coords=copy.deepcopy(state.coords),
            attributes=copy.deepcopy(state.attributes),
            object_id=state.object_id
        )
        if state.layer is not None:
            obj.layer = state.layer
        obj.visible = state.visible
        obj.selected = state.selected
        return obj

    def execute(self) -> bool:
        """Remove the object from the document."""
        try:
            if hasattr(self.document, 'objects'):
                self.document.objects.remove_object(self.object_state.object_id)
                return True
        except Exception as e:
            print(f"Error executing DeleteObjectCommand: {e}")
        return False

    def undo(self) -> bool:
        """Restore the object to the document."""
        try:
            if hasattr(self.document, 'objects'):
                obj = self._restore_object(self.object_state)
                self.document.objects.add_object(obj)
                return True
        except Exception as e:
            print(f"Error undoing DeleteObjectCommand: {e}")
        return False


class ModifyObjectCommand(Command):
    """Command to modify a CAD object's properties."""

    def __init__(self, document, obj: CADObject, new_coords=None,
                 new_attributes=None, description: str = "Modify Object"):
        super().__init__(description)
        self.document = document
        self.object_id = obj.object_id
        self.old_state = self._capture_object_state(obj)

        # Store new values
        self.new_coords = copy.deepcopy(new_coords) if new_coords else None
        self.new_attributes = copy.deepcopy(new_attributes) if new_attributes else None

    def _capture_object_state(self, obj: CADObject) -> ObjectState:
        """Capture the complete state of an object."""
        return ObjectState(
            object_id=obj.object_id,
            object_type=obj.object_type,
            coords=copy.deepcopy(obj.coords),
            attributes=copy.deepcopy(obj.attributes),
            layer=getattr(obj, 'layer', None),
            visible=getattr(obj, 'visible', True),
            selected=getattr(obj, 'selected', False)
        )

    def _apply_changes(self, obj: CADObject):
        """Apply the new changes to an object."""
        if self.new_coords is not None:
            obj.coords = copy.deepcopy(self.new_coords)
        if self.new_attributes is not None:
            obj.attributes.update(copy.deepcopy(self.new_attributes))

    def _restore_state(self, obj: CADObject, state: ObjectState):
        """Restore an object to a previous state."""
        obj.coords = copy.deepcopy(state.coords)
        obj.attributes = copy.deepcopy(state.attributes)
        if state.layer is not None:
            obj.layer = state.layer
        obj.visible = state.visible
        obj.selected = state.selected

    def execute(self) -> bool:
        """Apply the modifications to the object."""
        try:
            if hasattr(self.document, 'objects'):
                obj = self.document.objects.get_object(self.object_id)
                if obj:
                    self._apply_changes(obj)
                    return True
        except Exception as e:
            print(f"Error executing ModifyObjectCommand: {e}")
        return False

    def undo(self) -> bool:
        """Restore the object to its previous state."""
        try:
            if hasattr(self.document, 'objects'):
                obj = self.document.objects.get_object(self.object_id)
                if obj:
                    self._restore_state(obj, self.old_state)
                    return True
        except Exception as e:
            print(f"Error undoing ModifyObjectCommand: {e}")
        return False


class CompoundCommand(Command):
    """Command that groups multiple commands together."""

    def __init__(self, commands: List[Command], description: str = "Multiple Operations"):
        super().__init__(description)
        self.commands = commands

    def execute(self) -> bool:
        """Execute all commands in order."""
        success = True
        for cmd in self.commands:
            if not cmd.execute():
                success = False
                # Continue executing remaining commands
        return success

    def undo(self) -> bool:
        """Undo all commands in reverse order."""
        success = True
        for cmd in reversed(self.commands):
            if not cmd.undo():
                success = False
                # Continue undoing remaining commands
        return success


class UndoRedoManager:
    """Manages undo/redo operations using a command stack."""

    def __init__(self, max_undo_levels: int = 50):
        self.max_undo_levels = max_undo_levels
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.callbacks = []

    def execute_command(self, command: Command) -> bool:
        """Execute a command and add it to the undo stack."""
        if command.execute():
            # Clear redo stack when new command is executed
            self.redo_stack.clear()

            # Add to undo stack
            self.undo_stack.append(command)

            # Limit undo stack size
            while len(self.undo_stack) > self.max_undo_levels:
                self.undo_stack.pop(0)

            self._notify_callbacks()
            return True
        return False

    def undo(self) -> bool:
        """Undo the last command."""
        if not self.can_undo():
            return False

        command = self.undo_stack.pop()
        if command.undo():
            self.redo_stack.append(command)
            self._notify_callbacks()
            return True
        else:
            # If undo failed, put command back
            self.undo_stack.append(command)
            return False

    def redo(self) -> bool:
        """Redo the last undone command."""
        if not self.can_redo():
            return False

        command = self.redo_stack.pop()
        if command.redo():
            self.undo_stack.append(command)
            self._notify_callbacks()
            return True
        else:
            # If redo failed, put command back
            self.redo_stack.append(command)
            return False

    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return len(self.redo_stack) > 0

    def get_undo_description(self) -> Optional[str]:
        """Get description of the command that would be undone."""
        if self.can_undo():
            return self.undo_stack[-1].description
        return None

    def get_redo_description(self) -> Optional[str]:
        """Get description of the command that would be redone."""
        if self.can_redo():
            return self.redo_stack[-1].description
        return None

    def clear(self):
        """Clear all undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._notify_callbacks()

    def add_callback(self, callback):
        """Add a callback to be notified when undo/redo state changes."""
        self.callbacks.append(callback)

    def _notify_callbacks(self):
        """Notify all callbacks of state changes."""
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in undo/redo callback: {e}")


class CreateLayerCommand(Command):
    """Command to create a new layer."""

    def __init__(self, layer_manager, name: str = "", description: str = "Create Layer"):
        super().__init__(description)
        self.layer_manager = layer_manager
        self.name = name
        self.layer: Optional[Layer] = None

    def execute(self) -> bool:
        """Create the layer."""
        try:
            self.layer = self.layer_manager.create_layer(self.name, with_undo=False)
            return True
        except Exception as e:
            print(f"Error executing CreateLayerCommand: {e}")
            return False

    def undo(self) -> bool:
        """Delete the created layer."""
        try:
            if self.layer:
                return self.layer_manager.delete_layer(self.layer, with_undo=False)
        except Exception as e:
            print(f"Error undoing CreateLayerCommand: {e}")
        return False


class DeleteLayerCommand(Command):
    """Command to delete a layer."""

    def __init__(self, layer_manager, layer, description: str = "Delete Layer"):
        super().__init__(description)
        self.layer_manager = layer_manager
        self.layer = layer
        self.layer_data = None
        self.layer_position = None

    def _capture_layer_state(self, layer) -> dict:
        """Capture the complete state of a layer."""
        return {
            'name': layer.name,
            'visible': layer.visible,
            'locked': layer.locked,
            'color': layer.color,
            'cut_bit': layer.cut_bit,
            'cut_depth': layer.cut_depth,
            'objects': layer.objects.copy()
        }

    def execute(self) -> bool:
        """Delete the layer."""
        try:
            # Capture layer state before deletion
            self.layer_data = self._capture_layer_state(self.layer)
            self.layer_position = self.layer_manager.get_layer_position(self.layer)

            # Delete the layer
            return self.layer_manager.delete_layer(self.layer, with_undo=False)
        except Exception as e:
            print(f"Error executing DeleteLayerCommand: {e}")
            return False

    def undo(self) -> bool:
        """Restore the deleted layer."""
        try:
            if self.layer_data and self.layer_position is not None:
                # Create new layer with same properties
                new_layer = self.layer_manager.create_layer(
                    self.layer_data['name'], with_undo=False)

                # Restore properties
                new_layer.visible = self.layer_data['visible']
                new_layer.locked = self.layer_data['locked']
                new_layer.color = self.layer_data['color']
                new_layer.cut_bit = self.layer_data['cut_bit']
                new_layer.cut_depth = self.layer_data['cut_depth']
                new_layer.objects = self.layer_data['objects'].copy()

                # Restore position
                self.layer_manager.reorder_layer(new_layer, self.layer_position)

                self.layer = new_layer
                return True
        except Exception as e:
            print(f"Error undoing DeleteLayerCommand: {e}")
        return False


class ModifyLayerCommand(Command):
    """Command to modify layer properties."""

    def __init__(self, layer_manager, layer, new_properties: dict, description: str = "Modify Layer"):
        super().__init__(description)
        self.layer_manager = layer_manager
        self.layer = layer
        self.new_properties = new_properties
        self.old_properties = None

    def _capture_layer_properties(self, layer) -> dict:
        """Capture the current properties of a layer."""
        return {
            'name': layer.name,
            'visible': layer.visible,
            'locked': layer.locked,
            'color': layer.color,
            'cut_bit': layer.cut_bit,
            'cut_depth': layer.cut_depth
        }

    def execute(self) -> bool:
        """Apply the new properties to the layer."""
        try:
            # Capture old properties
            self.old_properties = self._capture_layer_properties(self.layer)

            # Apply new properties
            if 'name' in self.new_properties:
                self.layer_manager.set_layer_name(self.layer, self.new_properties['name'])
            if 'visible' in self.new_properties:
                self.layer_manager.set_layer_visible(self.layer, self.new_properties['visible'])
            if 'locked' in self.new_properties:
                self.layer_manager.set_layer_locked(self.layer, self.new_properties['locked'])
            if 'color' in self.new_properties:
                self.layer_manager.set_layer_color(self.layer, self.new_properties['color'])
            if 'cut_bit' in self.new_properties:
                self.layer_manager.set_layer_cut_bit(self.layer, self.new_properties['cut_bit'])
            if 'cut_depth' in self.new_properties:
                self.layer_manager.set_layer_cut_depth(self.layer, self.new_properties['cut_depth'])

            return True
        except Exception as e:
            print(f"Error executing ModifyLayerCommand: {e}")
            return False

    def undo(self) -> bool:
        """Restore the old properties."""
        try:
            if self.old_properties:
                # Restore old properties
                self.layer_manager.set_layer_name(self.layer, self.old_properties['name'])
                self.layer_manager.set_layer_visible(self.layer, self.old_properties['visible'])
                self.layer_manager.set_layer_locked(self.layer, self.old_properties['locked'])
                self.layer_manager.set_layer_color(self.layer, self.old_properties['color'])
                self.layer_manager.set_layer_cut_bit(self.layer, self.old_properties['cut_bit'])
                self.layer_manager.set_layer_cut_depth(self.layer, self.old_properties['cut_depth'])
                return True
        except Exception as e:
            print(f"Error undoing ModifyLayerCommand: {e}")
        return False


class ReorderLayerCommand(Command):
    """Command to reorder layers."""

    def __init__(self, layer_manager, layer, new_position: int, description: str = "Reorder Layer"):
        super().__init__(description)
        self.layer_manager = layer_manager
        self.layer = layer
        self.new_position = new_position
        self.old_position = None

    def execute(self) -> bool:
        """Move the layer to its new position."""
        old_layers = self.layer_manager._layers.copy()
        try:
            self.old_position = self.layer_manager.get_layer_position(self.layer)
            # Remove layer from old position
            self.layer_manager._layers.pop(self.old_position)
            # Insert at new position
            self.layer_manager._layers.insert(self.new_position, self.layer)
            return True
        except Exception as e:
            print(f"Error executing ReorderLayerCommand: {e}")
            # Restore original order if something went wrong
            if self.old_position is not None:
                self.layer_manager._layers = old_layers
            return False

    def undo(self) -> bool:
        """Restore the layer to its old position."""
        old_layers = self.layer_manager._layers.copy()
        try:
            if self.old_position is not None:
                # Remove layer from current position
                current_pos = self.layer_manager.get_layer_position(self.layer)
                self.layer_manager._layers.pop(current_pos)
                # Insert at old position
                self.layer_manager._layers.insert(self.old_position, self.layer)
                return True
        except Exception as e:
            print(f"Error undoing ReorderLayerCommand: {e}")
            # Restore original order if something went wrong
            if self.old_position is not None:
                self.layer_manager._layers = old_layers
        return False