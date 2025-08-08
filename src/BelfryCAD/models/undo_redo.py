"""
Undo/Redo Command System for BelfryCAD

This module provides a command pattern implementation for undo/redo functionality,
based on design patterns from the TCL implementation.
"""

from typing import List, Optional, Any, Dict
from abc import ABC, abstractmethod
import copy
from dataclasses import dataclass

from .cad_object import CadObject


@dataclass
class ObjectState:
    """Represents the state of a CAD object for undo/redo operations."""
    object_id: str
    snapshot: Dict[str, Any]


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

    def __init__(self, document, obj: CadObject, description: str = "Create Object"):
        super().__init__(description)
        self.document = document
        self.obj = obj
        self.object_id = obj.object_id

    def execute(self) -> bool:
        """Add the object to the document."""
        try:
            self.document.add_object(self.obj)
            return True
        except Exception as e:
            print(f"Error executing CreateObjectCommand: {e}")
            return False

    def undo(self) -> bool:
        """Remove the object from the document."""
        try:
            return self.document.remove_object(self.object_id)
        except Exception as e:
            print(f"Error undoing CreateObjectCommand: {e}")
            return False


class DeleteObjectCommand(Command):
    """Command to delete a CAD object."""

    def __init__(self, document, obj: CadObject, description: str = "Delete Object"):
        super().__init__(description)
        self.document = document
        self.obj = obj
        self.object_id = obj.object_id

    def execute(self) -> bool:
        """Remove the object from the document."""
        try:
            return self.document.remove_object(self.object_id)
        except Exception as e:
            print(f"Error executing DeleteObjectCommand: {e}")
            return False

    def undo(self) -> bool:
        """Restore the original object to the document."""
        try:
            self.document.add_object(self.obj)
            return True
        except Exception as e:
            print(f"Error undoing DeleteObjectCommand: {e}")
            return False


class ModifyObjectCommand(Command):
    """Command to modify a CAD object's properties via a provided apply/restore callable set."""

    def __init__(self, document, obj: CadObject, apply_fn, restore_fn, description: str = "Modify Object"):
        super().__init__(description)
        self.document = document
        self.object_id = obj.object_id
        self._apply_fn = apply_fn
        self._restore_fn = restore_fn

    def execute(self) -> bool:
        try:
            obj = self.document.get_object(self.object_id)
            if obj is None:
                return False
            self._apply_fn(obj)
            return True
        except Exception as e:
            print(f"Error executing ModifyObjectCommand: {e}")
            return False

    def undo(self) -> bool:
        try:
            obj = self.document.get_object(self.object_id)
            if obj is None:
                return False
            self._restore_fn(obj)
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
        return success

    def undo(self) -> bool:
        """Undo all commands in reverse order."""
        success = True
        for cmd in reversed(self.commands):
            if not cmd.undo():
                success = False
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


