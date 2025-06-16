"""
Tool Table Dialog

This module provides a dialog for managing a list of tool specifications.
"""

from typing import List, Optional
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt

from ..mlcnc.cutting_params import ToolSpecification, ToolGeometry
from .tool_spec_dialog import ToolSpecDialog

class ToolTableDialog(QDialog):
    """Dialog for managing a list of tool specifications."""

    def __init__(self, tool_specs: Optional[List[ToolSpecification]] = None, parent=None):
        super().__init__(parent)
        self.tool_specs = tool_specs or []
        self._setup_ui()
        self._load_tools()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Tool Table")
        self.setMinimumWidth(600)
        layout = QVBoxLayout()

        # Tool list
        list_group = QGroupBox("Tools")
        list_layout = QVBoxLayout()
        
        self.tool_list = QListWidget()
        self.tool_list.setAlternatingRowColors(True)
        self.tool_list.itemDoubleClicked.connect(self._edit_tool)
        self.tool_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)  # Enable drag-and-drop
        self.tool_list.model().rowsMoved.connect(self._on_items_reordered)  # Handle reordering
        list_layout.addWidget(self.tool_list)
        
        # Buttons for tool list
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("+")
        add_button.clicked.connect(self._add_tool)
        button_layout.addWidget(add_button)
        
        delete_button = QPushButton("–")
        delete_button.clicked.connect(self._delete_tool)
        button_layout.addWidget(delete_button)

        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self._edit_tool)
        button_layout.addWidget(edit_button)
        
        button_layout.addStretch()
        
        # Add move up/down buttons
        move_up_button = QPushButton("↑")
        move_up_button.clicked.connect(self._move_tool_up)
        button_layout.addWidget(move_up_button)
        
        move_down_button = QPushButton("↓")
        move_down_button.clicked.connect(self._move_tool_down)
        button_layout.addWidget(move_down_button)
        
        list_layout.addLayout(button_layout)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)

        # Dialog buttons
        dialog_buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        dialog_buttons.addWidget(ok_button)
        dialog_buttons.addWidget(cancel_button)
        dialog_buttons.addStretch()
        layout.addLayout(dialog_buttons)

        self.setLayout(layout)

        # Connect signals
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def _load_tools(self):
        """Load tools into the list widget."""
        self.tool_list.clear()
        for tool in self.tool_specs:
            self._add_tool_to_list(tool)

    def _add_tool_to_list(self, tool: ToolSpecification):
        """Add a tool to the list widget."""
        item = QListWidgetItem()
        item.setText(self._format_tool_info(tool))
        item.setData(Qt.ItemDataRole.UserRole, tool)
        self.tool_list.addItem(item)

    def _format_tool_info(self, tool_spec: ToolSpecification) -> str:
        """Format tool information for display in the list."""
        if (
            tool_spec.diameter == 0.0 or
            tool_spec.geometry == ToolGeometry.EMPTY_SLOT
        ):  # Empty slot
            return f"Tool {tool_spec.tool_id:02d} - Empty Slot"
        return (f"Tool {tool_spec.tool_id:02d} - {tool_spec.diameter:.3f}\" {tool_spec.geometry.value} "
                f"({tool_spec.flute_count} flutes)")

    def _add_tool(self):
        """Add a new tool."""
        dialog = ToolSpecDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tool = dialog.get_tool_spec()
            # Assign next available tool ID
            existing_ids = {t.tool_id for t in self.tool_specs if t.tool_id is not None}
            next_id = 1
            while next_id in existing_ids:
                next_id += 1
            tool.tool_id = next_id
            self.tool_specs.append(tool)
            self._add_tool_to_list(tool)

    def _edit_tool(self):
        """Edit the selected tool."""
        current_item = self.tool_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a tool to edit.")
            return

        tool = current_item.data(Qt.ItemDataRole.UserRole)
        dialog = ToolSpecDialog(tool)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_tool = dialog.get_tool_spec()
            # Update the tool in our list
            index = self.tool_list.row(current_item)
            self.tool_specs[index] = updated_tool
            current_item.setText(self._format_tool_info(updated_tool))
            current_item.setData(Qt.ItemDataRole.UserRole, updated_tool)

    def _delete_tool(self):
        """Delete the selected tool."""
        current_item = self.tool_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Warning", "Please select a tool to delete.")
            return

        tool = current_item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {self._format_tool_info(tool)}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            index = self.tool_list.row(current_item)
            self.tool_list.takeItem(index)
            self.tool_specs.pop(index)

    def _on_items_reordered(self, parent, start, end, destination, row):
        """Handle reordering of items in the list."""
        # Update tool_specs list to match the new order and renumber tool IDs
        self.tool_specs = []
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            tool_spec = item.data(Qt.ItemDataRole.UserRole)
            # Create new tool spec with updated ID
            new_tool_spec = ToolSpecification(
                diameter=tool_spec.diameter,
                length=tool_spec.length,
                flute_count=tool_spec.flute_count,
                geometry=tool_spec.geometry,
                material=tool_spec.material,
                coating=tool_spec.coating,
                corner_radius=tool_spec.corner_radius,
                chamfer_angle=tool_spec.chamfer_angle,
                helix_angle=tool_spec.helix_angle,
                rake_angle=tool_spec.rake_angle,
                tool_id=i + 1  # Tool IDs start at 1
            )
            self.tool_specs.append(new_tool_spec)
            # Update the item's data with the new tool spec
            item.setData(Qt.ItemDataRole.UserRole, new_tool_spec)
            # Update the display text to show new ID
            item.setText(self._format_tool_info(new_tool_spec))

    def _move_tool_up(self):
        """Move the selected tool up in the list."""
        current_item = self.tool_list.currentItem()
        if not current_item:
            return
            
        current_row = self.tool_list.row(current_item)
        if current_row > 0:
            # Move item in list widget
            self.tool_list.takeItem(current_row)
            self.tool_list.insertItem(current_row - 1, current_item)
            self.tool_list.setCurrentItem(current_item)
            
            # Update tool_specs list
            tool = self.tool_specs.pop(current_row)
            self.tool_specs.insert(current_row - 1, tool)
            
            # Renumber all tools
            self._renumber_tools()

    def _move_tool_down(self):
        """Move the selected tool down in the list."""
        current_item = self.tool_list.currentItem()
        if not current_item:
            return
            
        current_row = self.tool_list.row(current_item)
        if current_row < self.tool_list.count() - 1:
            # Move item in list widget
            self.tool_list.takeItem(current_row)
            self.tool_list.insertItem(current_row + 1, current_item)
            self.tool_list.setCurrentItem(current_item)
            
            # Update tool_specs list
            tool = self.tool_specs.pop(current_row)
            self.tool_specs.insert(current_row + 1, tool)
            
            # Renumber all tools
            self._renumber_tools()

    def _renumber_tools(self):
        """Renumber all tools based on their position in the list."""
        for i in range(self.tool_list.count()):
            item = self.tool_list.item(i)
            tool_spec = item.data(Qt.ItemDataRole.UserRole)
            # Create new tool spec with updated ID
            new_tool_spec = ToolSpecification(
                diameter=tool_spec.diameter,
                length=tool_spec.length,
                flute_count=tool_spec.flute_count,
                geometry=tool_spec.geometry,
                material=tool_spec.material,
                coating=tool_spec.coating,
                corner_radius=tool_spec.corner_radius,
                chamfer_angle=tool_spec.chamfer_angle,
                helix_angle=tool_spec.helix_angle,
                rake_angle=tool_spec.rake_angle,
                tool_id=i + 1  # Tool IDs start at 1
            )
            self.tool_specs[i] = new_tool_spec
            # Update the item's data with the new tool spec
            item.setData(Qt.ItemDataRole.UserRole, new_tool_spec)
            # Update the display text to show new ID
            item.setText(self._format_tool_info(new_tool_spec))

    def get_tool_specs(self) -> List[ToolSpecification]:
        """Get the list of tool specifications."""
        return self.tool_specs 