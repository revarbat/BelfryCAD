"""
Layer Pane Module for BelfryCad

This module provides a layer management pane for CAD operations, allowing
users to:
- View and manage layers with visibility, lock status, and CAM settings
- Create, delete, and reorder layers
- Edit layer properties (name, color, CAM settings)
- Toggle layer visibility and lock status

Translated from layerwin.tcl to provide equivalent functionality using
PySide6/Qt.

Author: Converted from TCL to Python
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING, Type, Sequence

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QLineEdit, QDoubleSpinBox,
    QComboBox, QDialog, QMessageBox, QFrame, QColorDialog,
    QApplication, QListWidget, QListWidgetItem, QToolBar, QSizePolicy, QGridLayout, QMainWindow,
    QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QTimer, QMimeData, QPoint, QSize
from PySide6.QtGui import (
    QPixmap, QIcon, QColor, QPalette, QDrag, QPainter,
    QDragEnterEvent, QDropEvent, QAction
)

from ..icon_manager import get_icon

if TYPE_CHECKING:
    from BelfryCAD.core.layers import Layer


class LayerPaneInfo:
    """Global layer pane information storage (singleton pattern)"""
    _instance = None

    def __init__(self):
        self.windows = {}
        self.icons = {}
        self.click_positions = {}
        self.drag_states = {}
        self.drag_positions = {}
        self.drag_timers = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register_window(self, base_id: str, window):
        """Register a window with its base ID"""
        self.windows[base_id] = window

    def get_window(self, base_id: str):
        """Get window by base ID"""
        return self.windows.get(base_id)

    def set_icons(self, base_id: str, icons: Dict[str, QIcon]):
        """Set icons for a window"""
        self.icons[base_id] = icons

    def get_icons(self, base_id: str) -> Dict[str, QIcon]:
        """Get icons for a window"""
        return self.icons.get(base_id, {})


# Global instance
layerpane_info = LayerPaneInfo()


class LayerCamDialog(QDialog):
    """Dialog for editing layer CAM settings."""

    def __init__(self, layer: 'Layer', cut_bit: int, cut_depth: float,
                 available_tools: List[tuple], parent=None):
        super().__init__(parent)
        self.layer = layer
        self.cut_bit = cut_bit
        self.cut_depth = cut_depth
        self.result_bit = cut_bit
        self.result_depth = cut_depth

        self.setWindowTitle("CAM Settings")
        self.setModal(True)
        self._setup_ui(available_tools)

    def _setup_ui(self, available_tools: List[tuple]):
        """Setup the dialog UI."""
        layout = QGridLayout()
        self.setLayout(layout)

        # Cut bit selection
        layout.addWidget(QLabel("Cut Bit:"), 0, 0)
        self.bit_combo = QComboBox()
        self.bit_combo.addItem("No Cut", 0)

        # Add available tools
        selected_index = 0
        for i, (bit_num, bit_name) in enumerate(available_tools):
            if bit_num != 99:  # Skip special tool number
                self.bit_combo.addItem(f"{bit_num}: {bit_name}", bit_num)
                if bit_num == self.cut_bit:
                    selected_index = i + 1

        self.bit_combo.setCurrentIndex(selected_index)
        layout.addWidget(self.bit_combo, 0, 1)

        # Cut depth
        layout.addWidget(QLabel("Cut Depth:"), 1, 0)
        self.depth_spin = QDoubleSpinBox()
        self.depth_spin.setRange(-1e6, 1e6)
        self.depth_spin.setDecimals(4)
        self.depth_spin.setSingleStep(0.05)
        self.depth_spin.setValue(self.cut_depth)
        layout.addWidget(self.depth_spin, 1, 1)

        # Buttons
        button_layout = QHBoxLayout()

        self.ok_button = QPushButton("Set")
        self.ok_button.setDefault(True)
        self.ok_button.clicked.connect(self.accept_changes)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout, 2, 0, 1, 2)

        # Keyboard shortcuts
        self.ok_button.setShortcut(Qt.Key.Key_Return)
        self.cancel_button.setShortcut(Qt.Key.Key_Escape)

        self.bit_combo.setFocus()

    def accept_changes(self):
        """Accept the changes and close dialog."""
        self.result_bit = self.bit_combo.currentData()
        self.result_depth = self.depth_spin.value()
        self.accept()

    def get_results(self) -> tuple:
        """Get the dialog results."""
        return (self.result_bit, self.result_depth)


class LayerItem(QFrame):
    """Widget representing a single layer in the layer list."""

    _next_id = 0

    # Signals
    selected = Signal(object)  # layer
    renamed = Signal(object, str)  # layer, new_name
    visibility_changed = Signal(object, bool)  # layer, visible
    lock_changed = Signal(object, bool)  # layer, locked
    color_changed = Signal(object, QColor)  # layer, color
    cam_settings_changed = Signal(object, int, float)  # layer, cut_bit, cut_depth
    reordered = Signal(object, int)  # layer, new_position

    def __init__(self, layer: 'Layer', parent=None):
        super().__init__(parent)
        self.id = LayerItem._next_id
        LayerItem._next_id += 1
        
        self.layer = layer
        self.is_current = False
        self.is_dragging = False
        self.drag_start_pos = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup the layer item UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(3)
        self.setLayout(layout)

        # Make the widget selectable
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("""
            background: transparent;
            border: 1px solid transparent;
            border-radius: 2px;
        """)

        # Visibility toggle
        self.visible_btn = QPushButton()
        self.visible_btn.setFixedSize(16, 16)
        self.visible_btn.setCheckable(True)
        self.visible_btn.setChecked(self.layer.visible)
        self.visible_btn.clicked.connect(self._toggle_visibility)
        self.visible_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 2px;
                margin: 2px;
            }
        """)
        layout.addWidget(self.visible_btn)

        # Lock toggle
        self.lock_btn = QPushButton()
        self.lock_btn.setFixedSize(16, 16)
        self.lock_btn.setCheckable(True)
        self.lock_btn.setChecked(self.layer.locked)
        self.lock_btn.clicked.connect(self._toggle_lock)
        self.lock_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 2px;
                margin: 2px;
            }
        """)
        layout.addWidget(self.lock_btn)

        # Layer name
        self.name_label = QLabel(self.layer.name)
        self.name_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                padding: 4px;
            }
        """)
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.name_edit = QLineEdit(self.layer.name)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #999;
                padding: 2px;
            }
        """)
        self.name_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.name_edit.hide()
        self.name_edit.editingFinished.connect(self._finish_editing_name)
        self.name_edit.returnPressed.connect(self._finish_editing_name)
        layout.addWidget(self.name_label, 1)  # Add stretch factor of 1
        layout.addWidget(self.name_edit, 1)   # Add stretch factor of 1

        # Color button
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(16, 16)
        self.color_btn.clicked.connect(self._change_color)
        layout.addWidget(self.color_btn)

        # CAM settings button
        self.cam_btn = QPushButton()
        self.cam_btn.setFixedSize(16, 16)
        self.cam_btn.clicked.connect(self._edit_cam_settings)
        self.cam_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 2px;
                margin: 2px;
            }
        """)
        layout.addWidget(self.cam_btn)

        # Object count
        self.count_label = QLabel(str(len(self.layer.objects)))
        self.count_label.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                padding: 2px;
            }
        """)
        layout.addWidget(self.count_label)

        # Set initial appearance
        self._update_appearance()

    def _update_appearance(self):
        """Update the layer item appearance based on its state."""
        # Update visibility button
        if self.layer.visible:
            self.visible_btn.setIcon(get_icon("layer-visible"))
        else:
            self.visible_btn.setIcon(get_icon("layer-invisible"))

        # Update lock button
        if self.layer.locked:
            self.lock_btn.setIcon(get_icon("layer-locked"))
        else:
            self.lock_btn.setIcon(get_icon("layer-unlocked"))

        # Update color button
        color = QColor(self.layer.color)
        self.color_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                border: 1px solid #999999;
                border-radius: 3px;
            }}
        """)

        # Update CAM settings button
        if self.layer.cut_bit > 0:
            self.cam_btn.setIcon(get_icon("layer-cam"))
        else:
            self.cam_btn.setIcon(get_icon("layer-nocam"))

        # Update selected state
        if self.is_current:
            self.setStyleSheet("""
                background: #bbbbbb;
                border: 1px solid #999999;
                border-radius: 2px;
            """)
        else:
            self.setStyleSheet("""
                background: transparent;
                border: 1px solid transparent;
                border-radius: 2px;
            """)

    def _toggle_visibility(self):
        """Toggle layer visibility."""
        self.layer.visible = self.visible_btn.isChecked()
        self._update_appearance()
        self.visibility_changed.emit(self.layer, self.layer.visible)

    def _toggle_lock(self):
        """Toggle layer lock state."""
        self.layer.locked = self.lock_btn.isChecked()
        self._update_appearance()
        self.lock_changed.emit(self.layer, self.layer.locked)

    def _change_color(self):
        """Change layer color."""
        color = QColorDialog.getColor(
            QColor(self.layer.color),
            self,
            "Select Layer Color"
        )
        if color.isValid():
            self.layer.color = color.name()
            self._update_appearance()
            self.color_changed.emit(self.layer, color)

    def _edit_cam_settings(self):
        """Edit layer CAM settings."""
        get_tools = getattr(self.parent(), '_get_available_tools', None)
        available_tools = get_tools() if get_tools else []
        dialog = LayerCamDialog(
            self.layer,
            self.layer.cut_bit,
            self.layer.cut_depth,
            available_tools,
            self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cut_bit, cut_depth = dialog.get_results()
            self.layer.cut_bit = cut_bit
            self.layer.cut_depth = cut_depth
            self._update_appearance()
            self.cam_settings_changed.emit(self.layer, cut_bit, cut_depth)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = event.pos()
            self.setSelected(True)
            self.selected.emit(self.layer)
            
            # Ensure the selected item is visible in the scroll area
            if self.parent() and self.parent().parent():
                scroll_area = self.parent().parent()
                if isinstance(scroll_area, QScrollArea):
                    # Get the item's position relative to the layer list
                    item_pos = self.mapTo(scroll_area.widget(), QPoint(0, 0))
                    # Add a small margin to ensure visibility
                    scroll_pos = max(0, item_pos.y() - 20)  # 20 pixel margin
                    # Set the scroll position
                    scroll_area.verticalScrollBar().setValue(scroll_pos)
                    
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.is_dragging and self.drag_start_pos:
            if (
                (event.pos() - self.drag_start_pos).manhattanLength() >
                QApplication.startDragDistance()
            ):
                # Start drag operation
                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setData("application/x-layer", str(self.id).encode())
                drag.setMimeData(mime_data)
                
                # Create a pixmap of the item for drag preview
                pixmap = QPixmap(self.size())
                self.render(pixmap)
                drag.setPixmap(pixmap)
                
                # Start the drag
                drag.exec(Qt.DropAction.MoveAction)
                self.is_dragging = False

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
        self.drag_start_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double click events to start editing the layer name."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_editing_name()
        super().mouseDoubleClickEvent(event)

    def _start_editing_name(self):
        """Start editing the layer name."""
        self.name_label.hide()
        self.name_edit.setText(self.layer.name)
        self.name_edit.show()
        self.name_edit.setFocus()
        self.name_edit.selectAll()

    def _finish_editing_name(self):
        """Finish editing the layer name."""
        new_name = self.name_edit.text().strip()
        if new_name and new_name != self.layer.name:
            self.layer.name = new_name
            self.name_label.setText(new_name)
            self.renamed.emit(self.layer, new_name)
        self.name_edit.hide()
        self.name_label.show()

    def _cancel_editing_name(self):
        """Cancel editing the layer name."""
        self.name_edit.hide()
        self.name_label.show()

    def update_data(self, layer: 'Layer'):
        """Update layer data."""
        self.layer = layer
        self.name_label.setText(layer.name)
        self.name_edit.setText(layer.name)
        self.count_label.setText(str(len(layer.objects)))
        self._update_appearance()

    def setSelected(self, selected: bool):
        """Set the selected state of the layer item."""
        self.is_current = selected
        self._update_appearance()

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Escape and self.name_edit.isVisible():
            self._cancel_editing_name()
        super().keyPressEvent(event)


class LayerPane(QWidget):
    """Pane for managing layers."""

    # Signals
    layer_created = Signal()
    layer_deleted = Signal(object)  # layer
    layer_selected = Signal(object)  # layer
    layer_renamed = Signal(object, str)  # layer, new_name
    layer_visibility_changed = Signal(object, bool)  # layer, visible
    layer_lock_changed = Signal(object, bool)  # layer, locked
    layer_color_changed = Signal(object, QColor)  # layer, color
    layer_cam_changed = Signal(object, int, float)  # layer, cut_bit, cut_depth
    layer_reordered = Signal(object, int)  # layer, new_position

    def __init__(self, canvas=None, window_id="main", parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.window_id = window_id
        self.base_id = f"layerwin_{window_id}"
        self.layer_items: Dict['Layer', 'LayerItem'] = {}  # layer -> LayerItem
        self.current_layer: Optional['Layer'] = None
        self.main_window = self.parent()
        self.drag_item = None

        # Register with global info
        layerpane_info.register_window(window_id, self)

        self._setup_ui()
        self._setup_icons()
        self._setup_drag_drop()

    @property
    def document(self):
        """Get the document from the main window."""
        if isinstance(self.parent(), QMainWindow):
            return getattr(self.parent(), "document", None)
        return None

    def _get_available_tools(self) -> List[tuple]:
        """Get list of available cutting tools."""
        # This would integrate with the CAD system's tool management
        # For now, return some sample tools
        return [
            (1, '1/8" End Mill'),
            (2, '1/4" End Mill'),
            (3, '1/16" End Mill'),
            (4, '60° V-Bit'),
            (5, '90° V-Bit')
        ]

    def start_drag(self, layer: 'Layer', pos: QPoint):
        """Start dragging a layer."""
        if layer in self.layer_items:
            self.drag_item = self.layer_items[layer]

    def _on_layer_selected(self, layer: 'Layer'):
        """Handle layer selection."""
        self.set_current_layer(layer)
        self.layer_selected.emit(layer)

    def refresh_layers(
            self, layers: Sequence['Layer'],
            current_layer: Optional['Layer'] = None
    ):
        """
        Refresh the layer display with new data.

        Args:
            layers: Sequence of Layer objects
            current_layer: Currently selected layer
        """
        self.current_layer = current_layer

        # Track which layers we've processed
        processed_layers = set()
        new_layer_item = None

        # Update or create layer items
        for layer in layers:
            if layer in self.layer_items:
                # Reuse existing layer item
                layer_item = self.layer_items[layer]
                layer_item.update_data(layer)
                if layer == current_layer:
                    layer_item.setSelected(True)
                else:
                    layer_item.setSelected(False)
            else:
                # Create new layer item
                layer_item = LayerItem(layer)
                # Connect signals
                layer_item.selected.connect(self._on_layer_selected)
                layer_item.renamed.connect(self.layer_renamed.emit)
                layer_item.visibility_changed.connect(self.layer_visibility_changed.emit)
                layer_item.lock_changed.connect(self.layer_lock_changed.emit)
                layer_item.color_changed.connect(self.layer_color_changed.emit)
                layer_item.cam_settings_changed.connect(self.layer_cam_changed.emit)
                self.layer_items[layer] = layer_item
                new_layer_item = layer_item
                # Add new item to layout
                self.layer_layout.addWidget(layer_item)

            processed_layers.add(layer)

        # Remove layer items that are no longer in the layers list
        layers_to_remove = set(self.layer_items.keys()) - processed_layers
        for layer in layers_to_remove:
            layer_item = self.layer_items.pop(layer)
            # Remove from layout
            self.layer_layout.removeWidget(layer_item)
            layer_item.setParent(None)
            layer_item.deleteLater()

        # Ensure stretch is at the end
        if self.layer_layout.count() > 0:
            last_item = self.layer_layout.itemAt(self.layer_layout.count() - 1)
            if not isinstance(last_item, QSpacerItem):
                self.layer_layout.addStretch()

        # If we created a new layer item, select it and make it visible
        if new_layer_item:
            new_layer_item.setSelected(True)
            self.current_layer = new_layer_item.layer
            self.layer_selected.emit(new_layer_item.layer)
            
            # Use a timer to scroll to the new item after layout is complete
            def scroll_to_new_item():
                if self.scroll_area and new_layer_item:
                    # Force layout update
                    self.layer_list.updateGeometry()
                    self.scroll_area.viewport().update()
                    
                    # Get the item's position relative to the layer list
                    item_pos = new_layer_item.mapTo(self.scroll_area.widget(), QPoint(0, 0))
                    # Add a small margin to ensure visibility
                    scroll_pos = max(0, item_pos.y() - 20)  # 20 pixel margin
                    # Set the scroll position
                    self.scroll_area.verticalScrollBar().setValue(scroll_pos)
            
            # Use a longer delay to ensure layout is complete
            QTimer.singleShot(100, scroll_to_new_item)

    def _delete_current_layer(self):
        """Delete the current layer."""
        if not self.current_layer:
            QApplication.beep()
            return

        # Get layer info
        if self.current_layer in self.layer_items:
            layer_item = self.layer_items[self.current_layer]
            layer_name = layer_item.layer.name
            object_count = len(layer_item.layer.objects)

            # Confirm deletion if layer has objects
            if object_count > 0:
                reply = QMessageBox.question(
                    self,
                    "Delete Layer",
                    f"Layer '{layer_name}' contains {object_count} objects.\n"
                    "Are you sure you want to delete it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            self.layer_deleted.emit(self.current_layer)

    def set_current_layer(self, layer: 'Layer'):
        """Set the current layer."""
        old_current = self.current_layer
        self.current_layer = layer

        # Update old current layer appearance
        if old_current and old_current in self.layer_items:
            self.layer_items[old_current].setSelected(False)

        # Update new current layer appearance
        if layer and layer in self.layer_items:
            self.layer_items[layer].setSelected(True)

    def _on_layers_reordered(self, parent, start, end, destination, row):
        """Handle layer reordering."""
        if start != row:  # Only emit if the layer actually moved
            layer_item = self.layer_layout.itemAt(start).widget()
            if isinstance(layer_item, LayerItem):
                self.layer_reordered.emit(layer_item.layer, row)

    def _create_new_layer(self):
        """Create a new layer."""
        self.layer_created.emit()

    def _setup_ui(self):
        """Set up the user interface."""
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Create scroll area for layer list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.main_layout.addWidget(self.scroll_area)

        # Create layer list container
        self.layer_list = QWidget()
        self.layer_layout = QVBoxLayout(self.layer_list)
        self.layer_layout.setContentsMargins(0, 0, 0, 0)
        self.layer_layout.setSpacing(0)
        self.scroll_area.setWidget(self.layer_list)

        # Create toolbar at the bottom
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(16, 16))
        self.toolbar.setMovable(False)
        self.main_layout.addWidget(self.toolbar)

    def _setup_icons(self):
        """Set up toolbar icons."""
        # Add new layer button
        new_layer_action = QAction(self)
        new_layer_action.setIcon(get_icon("layer-new"))
        new_layer_action.setToolTip("New Layer")
        new_layer_action.triggered.connect(self._create_new_layer)
        self.toolbar.addAction(new_layer_action)

        # Add delete layer button
        delete_layer_action = QAction(self)
        delete_layer_action.setIcon(get_icon("layer-delete"))
        delete_layer_action.setToolTip("Delete Layer")
        delete_layer_action.triggered.connect(self._delete_current_layer)
        self.toolbar.addAction(delete_layer_action)

    def _setup_drag_drop(self):
        """Set up drag and drop functionality."""
        self.layer_list.setAcceptDrops(True)
        self.layer_list.dragEnterEvent = self._drag_enter_event
        self.layer_list.dragMoveEvent = self._drag_move_event
        self.layer_list.dropEvent = self._drop_event

    def _drag_enter_event(self, event):
        """Handle drag enter event."""
        if event.mimeData().hasFormat("application/x-layer"):
            event.acceptProposedAction()

    def _drag_move_event(self, event):
        """Handle drag move event."""
        if event.mimeData().hasFormat("application/x-layer"):
            # Get the position in the layer list
            pos = event.position().toPoint()
            target_item = self.layer_list.childAt(pos)
            
            # Find the target position in the layout
            if target_item:
                target_index = self.layer_layout.indexOf(target_item)
                if target_index >= 0:
                    # Move the dragged item in the layout
                    if self.drag_item:
                        self.layer_layout.removeWidget(self.drag_item)
                        self.layer_layout.insertWidget(target_index, self.drag_item)
            event.acceptProposedAction()

    def _drop_event(self, event):
        """Handle drop event."""
        if event.mimeData().hasFormat("application/x-layer"):
            # Get the position in the layer list
            pos = event.position().toPoint()
            target_item = self.layer_list.childAt(pos)
            
            if target_item and self.drag_item:
                # Get the target position in the layout
                target_index = self.layer_layout.indexOf(target_item)
                if target_index >= 0:
                    # Move the dragged item in the layout
                    self.layer_layout.removeWidget(self.drag_item)
                    self.layer_layout.insertWidget(target_index, self.drag_item)
                    
                    # Emit reorder signal
                    self.layer_reordered.emit(self.drag_item.layer, target_index)
            
            self.drag_item = None
            event.acceptProposedAction()
