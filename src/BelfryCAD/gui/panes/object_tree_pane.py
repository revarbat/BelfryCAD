"""
Object Tree Pane

This module provides a collapsible tree view of all CAD objects and groups
with visibility toggle functionality and automatic updates.
"""

from typing import Optional, Dict, Any, Set
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QHBoxLayout, QLabel, QHeaderView, QPushButton, QColorDialog,
    QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QPixmap, QColor

from ...models.document import Document
from ...models.cad_objects.group_cad_object import GroupCadObject
from ...gui.icon_manager import IconManager


class ObjectTreePane(QWidget):
    """A pane that displays a hierarchical tree view of all CAD objects and groups."""
    
    # Signals
    object_selected = Signal(str)  # Emitted when an object is selected
    visibility_changed = Signal(str, bool)  # Emitted when object visibility changes
    color_changed = Signal(str, QColor)  # Emitted when object color changes
    name_changed = Signal(str, str)  # Emitted when object name changes (object_id, new_name)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.document: Optional[Document] = None
        self.icon_manager = IconManager()
        self.selected_object_ids: Set[str] = set()  # Track selected objects
        self.updating_selection = False  # Prevent recursive selection updates
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Object", "", ""])
        self.tree_widget.setColumnWidth(0, 200)
        self.tree_widget.setColumnWidth(1, 20)
        self.tree_widget.setColumnWidth(2, 20)
        self.tree_widget.header().setStretchLastSection(False)
        self.tree_widget.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree_widget.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.tree_widget.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        
        # Enable item editing
        self.tree_widget.setEditTriggers(QTreeWidget.EditTrigger.DoubleClicked)
        
        # Connect signals
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.tree_widget.itemSelectionChanged.connect(self.on_selection_changed)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree_widget.itemChanged.connect(self.on_item_changed)
        
        layout.addWidget(self.tree_widget)
        
    def set_document(self, document: Document):
        """Set the document to display in the tree."""
        self.document = document
        self.refresh_tree()
        
        # Connect to document signals for automatic updates
        # Note: We'll need to add these signals to the Document class
        # For now, we'll use a timer to check for changes
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.start(500)  # Check every 500ms
        
    def check_for_updates(self):
        """Check if the document has changed and update the tree if needed."""
        if not self.document:
            return
            
        # Get current object IDs in the tree
        current_ids = set()
        self.collect_object_ids(self.tree_widget.invisibleRootItem(), current_ids)
        
        # Get current object IDs in the document
        document_ids = set(self.document.objects.keys())
        
        # If they don't match, refresh the tree
        if current_ids != document_ids:
            self.refresh_tree()
            
    def collect_object_ids(self, parent_item: QTreeWidgetItem, ids: Set[str]):
        """Recursively collect all object IDs from the tree."""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            object_id = child.data(0, Qt.ItemDataRole.UserRole)
            if object_id:
                ids.add(object_id)
            self.collect_object_ids(child, ids)
                
    def refresh_tree(self):
        """Refresh the tree view with current document data."""
        if not self.document:
            return
            
        # Store current selection
        old_selection = self.selected_object_ids.copy()
        
        self.tree_widget.clear()
        
        # Get root groups
        root_groups = self.document.get_root_groups()
        
        # Add root groups
        for group in root_groups:
            group_item = self.create_group_item(group)
            self.tree_widget.addTopLevelItem(group_item)
            
        # Add root objects (objects not in any group)
        root_objects = self.document.get_root_objects()
        for obj in root_objects:
            if not isinstance(obj, GroupCadObject):  # Groups already added above
                obj_item = self.create_object_item(obj)
                self.tree_widget.addTopLevelItem(obj_item)
        
        # Restore selection
        self.restore_selection(old_selection)
                
    def create_group_item(self, group: GroupCadObject) -> QTreeWidgetItem:
        """Create a tree item for a group."""
        item = QTreeWidgetItem()
        item.setText(0, f"📁 {group.name}")
        item.setData(0, Qt.ItemDataRole.UserRole, group.object_id)
        # No icon needed since we're using the folder emoji
        
        # Add visibility toggle button
        visibility_btn = QPushButton()
        visibility_btn.setIcon(self.icon_manager.get_icon("object-visible" if group.visible else "object-invisible"))
        visibility_btn.setFixedSize(20, 20)
        visibility_btn.clicked.connect(lambda: self.toggle_visibility(group.object_id))
        self.tree_widget.setItemWidget(item, 1, visibility_btn)
        
        # Add color button
        color_btn = QPushButton()
        color_btn.setFixedSize(20, 20)
        color_btn.setStyleSheet(f"background-color: {group.color}; border: 1px solid black;")
        color_btn.clicked.connect(lambda: self.change_object_color(group.object_id))
        self.tree_widget.setItemWidget(item, 2, color_btn)
        
        # Add children
        for child_id in group.children:
            child_obj = self.document.get_object(child_id) if self.document else None
            if child_obj:
                if isinstance(child_obj, GroupCadObject):
                    child_item = self.create_group_item(child_obj)
                else:
                    child_item = self.create_object_item(child_obj)
                item.addChild(child_item)
                
        return item
        
    def create_object_item(self, obj) -> QTreeWidgetItem:
        """Create a tree item for a regular CAD object."""
        item = QTreeWidgetItem()
        
        # Get object type name and display name
        obj_type = type(obj).__name__.replace('CadObject', '').replace('_', ' ')
        display_name = obj.name if hasattr(obj, 'name') and obj.name else f"● {obj_type}"
        item.setText(0, display_name)
        item.setData(0, Qt.ItemDataRole.UserRole, obj.object_id)
        
        # Set icon based on object type
        icon_name = self.get_object_icon_name(obj)
        item.setIcon(0, self.icon_manager.get_icon(icon_name))
        
        # Add visibility toggle button
        visibility_btn = QPushButton()
        visibility_btn.setIcon(self.icon_manager.get_icon("object-visible" if obj.visible else "object-invisible"))
        visibility_btn.setFixedSize(20, 20)
        visibility_btn.clicked.connect(lambda: self.toggle_visibility(obj.object_id))
        self.tree_widget.setItemWidget(item, 1, visibility_btn)
        
        # Add color button
        color_btn = QPushButton()
        color_btn.setFixedSize(20, 20)
        color_btn.setStyleSheet(f"background-color: {obj.color}; border: 1px solid black;")
        color_btn.clicked.connect(lambda: self.change_object_color(obj.object_id))
        self.tree_widget.setItemWidget(item, 2, color_btn)
        
        return item
        
    def get_object_icon_name(self, obj) -> str:
        """Get the appropriate icon name for a CAD object."""
        obj_type = type(obj).__name__
        
        # Map object types to icon names
        icon_mapping = {
            'LineCadObject': 'obj-line',
            'ArcCadObject': 'obj-arc', 
            'CircleCadObject': 'obj-circle',
            'EllipseCadObject': 'obj-ellipse',
            'CubicBezierCadObject': 'obj-bezier',
            'GearCadObject': 'obj-gear',
            'GroupCadObject': 'obj-group'
        }
        
        return icon_mapping.get(obj_type, 'object-visible' if obj.visible else 'object-invisible')
        
    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click events."""
        if column == 0:  # Only emit for object column, not visibility column
            object_id = item.data(0, Qt.ItemDataRole.UserRole)
            if object_id:
                self.object_selected.emit(object_id)
                
    def on_selection_changed(self):
        """Handle selection changes in the tree."""
        if self.updating_selection:
            return
            
        self.updating_selection = True
        
        # Get selected items
        selected_items = self.tree_widget.selectedItems()
        new_selection = set()
        
        for item in selected_items:
            object_id = item.data(0, Qt.ItemDataRole.UserRole)
            if object_id:
                new_selection.add(object_id)
                
        # Update internal selection tracking
        self.selected_object_ids = new_selection
        
        # Emit selection signal for each selected object
        for object_id in new_selection:
            self.object_selected.emit(object_id)
            
        self.updating_selection = False
        
    def set_selection_from_scene(self, selected_object_ids: Set[str]):
        """Update tree selection based on scene selection."""
        if self.updating_selection:
            return
            
        self.updating_selection = True
        
        # Clear current selection
        self.tree_widget.clearSelection()
        
        # Select items in the tree
        for object_id in selected_object_ids:
            items = self.find_items_by_object_id(self.tree_widget.invisibleRootItem(), object_id)
            for item in items:
                item.setSelected(True)
                
        # Update internal tracking
        self.selected_object_ids = selected_object_ids.copy()
        
        self.updating_selection = False
        
    def toggle_visibility(self, object_id: str):
        """Toggle visibility of an object and all its children."""
        if not self.document:
            return
            
        obj = self.document.get_object(object_id)
        if not obj:
            return
            
        # Toggle visibility
        new_visibility = not obj.visible
        obj.visible = new_visibility
        
        # If it's a group, toggle all children
        if isinstance(obj, GroupCadObject):
            self.toggle_group_children_visibility(obj, new_visibility)
            
        # Emit signal
        self.visibility_changed.emit(object_id, new_visibility)
        
        # Refresh the tree to update icons
        self.refresh_tree()
        
    def toggle_group_children_visibility(self, group: GroupCadObject, visibility: bool):
        """Recursively toggle visibility of all children in a group."""
        for child_id in group.children:
            child_obj = self.document.get_object(child_id) if self.document else None
            if child_obj:
                child_obj.visible = visibility
                
                # If child is also a group, recurse
                if isinstance(child_obj, GroupCadObject):
                    self.toggle_group_children_visibility(child_obj, visibility)
                    
    def select_object(self, object_id: str):
        """Select an object in the tree."""
        # Find the item with the given object_id
        items = self.find_items_by_object_id(self.tree_widget.invisibleRootItem(), object_id)
        if items:
            self.tree_widget.setCurrentItem(items[0])
            self.tree_widget.scrollToItem(items[0])
            
    def find_items_by_object_id(self, parent_item, object_id: str) -> list:
        """Recursively find tree items by object ID."""
        items = []
        
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child.data(0, Qt.ItemDataRole.UserRole) == object_id:
                items.append(child)
            items.extend(self.find_items_by_object_id(child, object_id))
            
        return items
        
    def restore_selection(self, object_ids: Set[str]):
        """Restore selection to the specified object IDs."""
        if not object_ids:
            return
            
        # Find and select items
        for object_id in object_ids:
            items = self.find_items_by_object_id(self.tree_widget.invisibleRootItem(), object_id)
            for item in items:
                item.setSelected(True)
                
        # Update internal tracking
        self.selected_object_ids = object_ids.copy()

    def change_object_color(self, object_id: str):
        """Change the color of an object."""
        if not self.document:
            return
            
        obj = self.document.get_object(object_id)
        if not obj:
            return
            
        # Open color dialog
        color_dialog = QColorDialog()
        color_dialog.setCurrentColor(QColor(obj.color))
        
        if color_dialog.exec() == QColorDialog.DialogCode.Accepted:
            new_color = color_dialog.currentColor()
            obj.color = new_color.name()
            
            # Emit signal
            self.color_changed.emit(object_id, new_color)
            
            # Refresh the tree to update color buttons
            self.refresh_tree()

    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click events for item editing."""
        if column == 0:  # Only allow editing in the name column
            # Get the current text
            current_text = item.text(0)
            
            # Create a line edit widget
            line_edit = QLineEdit(self.tree_widget)
            line_edit.setText(current_text)
            line_edit.selectAll()  # Select all text in the line edit
            
            # Set the line edit's geometry to be at the item's position
            line_edit.setGeometry(self.tree_widget.visualItemRect(item))
            
            # Show the line edit and set focus
            line_edit.show()
            line_edit.setFocus()
            
            # Connect the line edit's editing finished signal
            line_edit.editingFinished.connect(lambda: self._finish_editing(item, line_edit))
            
    def _finish_editing(self, item: QTreeWidgetItem, line_edit: QLineEdit):
        """Finish editing an item's name."""
        new_text = line_edit.text().strip()
        if new_text:
            object_id = item.data(0, Qt.ItemDataRole.UserRole)
            if object_id and self.document:
                # Try to rename the object
                if self.document.rename_object(object_id, new_text):
                    # Update the item text
                    item.setText(0, new_text)
                    # Emit the name changed signal
                    self.name_changed.emit(object_id, new_text)
                else:
                    # Show error message if rename failed
                    QMessageBox.warning(self, "Rename Failed", 
                                      f"The name '{new_text}' is already in use or invalid.")
                    # Restore the original text
                    obj = self.document.get_object(object_id)
                    if obj:
                        item.setText(0, obj.name)
        
        # Clean up the line edit
        line_edit.deleteLater()
        
    def on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle item text changes."""
        if column == 0:  # Only handle name changes
            object_id = item.data(0, Qt.ItemDataRole.UserRole)
            if object_id:
                new_text = item.text(0).strip()
                if new_text and self.document:
                    # Try to rename the object
                    if not self.document.rename_object(object_id, new_text):
                        # Show error message if rename failed
                        QMessageBox.warning(self, "Rename Failed", 
                                          f"The name '{new_text}' is already in use or invalid.")
                        # Restore the original text
                        obj = self.document.get_object(object_id)
                        if obj:
                            item.setText(0, obj.name) 