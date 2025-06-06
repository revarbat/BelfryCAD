"""
Layer Window Module for PyTkCAD

This module provides a layer management window for CAD operations, allowing users to:
- View and manage layers with visibility, lock status, and CAM settings
- Create, delete, and reorder layers
- Edit layer properties (name, color, CAM settings)
- Toggle layer visibility and lock status

Translated from layerwin.tcl to provide equivalent functionality using PySide6/Qt.

Author: Converted from TCL to Python
"""

import math
import os
from typing import Dict, Any, Optional, List, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QDialog, QMessageBox, QFrame, QColorDialog,
    QApplication
)
from PySide6.QtCore import Qt, Signal, QTimer, QMimeData, QRect
from PySide6.QtGui import (
    QPixmap, QIcon, QColor, QPalette, QDrag, QPainter,
    QMouseEvent, QDragEnterEvent, QDropEvent
)


class LayerWindowInfo:
    """Global layer window information storage (singleton pattern)"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.windows = {}
            cls._instance.icons = {}
            cls._instance.click_positions = {}
            cls._instance.drag_states = {}
            cls._instance.drag_positions = {}
            cls._instance.drag_timers = {}
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
layerwin_info = LayerWindowInfo()


class LayerCamDialog(QDialog):
    """Dialog for editing layer CAM settings"""

    def __init__(self, layer_id: str, cut_bit: int, cut_depth: float,
                 available_tools: List[tuple], parent=None):
        super().__init__(parent)
        self.layer_id = layer_id
        self.cut_bit = cut_bit
        self.cut_depth = cut_depth
        self.result_bit = cut_bit
        self.result_depth = cut_depth

        self.setWindowTitle("CAM Settings")
        self.setModal(True)
        self._setup_ui(available_tools)

    def _setup_ui(self, available_tools: List[tuple]):
        """Setup the dialog UI"""
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
        """Accept the changes and close dialog"""
        self.result_bit = self.bit_combo.currentData()
        self.result_depth = self.depth_spin.value()
        self.accept()

    def get_results(self) -> tuple:
        """Get the dialog results"""
        return (self.result_bit, self.result_depth)


class LayerItem(QFrame):
    """Widget representing a single layer in the layer list"""

    # Signals
    layer_selected = Signal(str)  # layer_id
    layer_renamed = Signal(str, str)  # layer_id, new_name
    visibility_toggled = Signal(str)  # layer_id
    lock_toggled = Signal(str)  # layer_id
    color_changed = Signal(str, str)  # layer_id, color
    cam_edit_requested = Signal(str)  # layer_id
    layer_reordered = Signal(str, int)  # layer_id, new_position

    def __init__(self, layer_id: str, layer_data: Dict[str, Any],
                 icons: Dict[str, QIcon], is_current: bool = False):
        super().__init__()
        self.layer_id = layer_id
        self.layer_data = layer_data
        self.icons = icons
        self.is_current = is_current
        self.is_editing_name = False
        self.drag_start_pos = None

        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setFixedHeight(25)
        self._setup_ui()
        self._update_appearance()

    def _setup_ui(self):
        """Setup the layer item UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        self.setLayout(layout)

        # Lock button
        self.lock_button = QPushButton()
        self.lock_button.setFixedSize(16, 16)
        self.lock_button.setFlat(True)
        self.lock_button.clicked.connect(lambda: self.lock_toggled.emit(self.layer_id))
        layout.addWidget(self.lock_button)

        # Visibility button
        self.visibility_button = QPushButton()
        self.visibility_button.setFixedSize(16, 16)
        self.visibility_button.setFlat(True)
        self.visibility_button.clicked.connect(lambda: self.visibility_toggled.emit(self.layer_id))
        layout.addWidget(self.visibility_button)

        # Layer name label
        self.name_label = QLabel(self.layer_data['name'])
        self.name_label.setMinimumWidth(100)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.name_label, 1)  # Stretch factor 1

        # Layer name edit (initially hidden)
        self.name_edit = QLineEdit()
        self.name_edit.hide()
        self.name_edit.returnPressed.connect(self._commit_name_change)
        self.name_edit.editingFinished.connect(self._cancel_name_edit)
        layout.addWidget(self.name_edit, 1)

        # Color button
        self.color_button = QPushButton()
        self.color_button.setFixedSize(16, 16)
        self.color_button.clicked.connect(self._edit_color)
        layout.addWidget(self.color_button)

        # CAM button
        self.cam_button = QPushButton()
        self.cam_button.setFixedSize(16, 16)
        self.cam_button.setFlat(True)
        self.cam_button.clicked.connect(lambda: self.cam_edit_requested.emit(self.layer_id))
        layout.addWidget(self.cam_button)

        # Object count label
        self.count_label = QLabel(str(self.layer_data['object_count']))
        self.count_label.setFixedWidth(30)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.count_label)

        # Mouse events for layer selection and drag
        self.name_label.mousePressEvent = self._name_mouse_press
        self.name_label.mouseDoubleClickEvent = self._name_double_click
        self.name_label.mouseMoveEvent = self._name_mouse_move
        self.name_label.mouseReleaseEvent = self._name_mouse_release

    def _update_appearance(self):
        """Update the visual appearance based on layer data"""
        # Update lock icon
        if self.layer_data['locked']:
            self.lock_button.setIcon(self.icons.get('lock', QIcon()))
        else:
            self.lock_button.setIcon(self.icons.get('unlock', QIcon()))

        # Update visibility icon
        if self.layer_data['visible']:
            self.visibility_button.setIcon(self.icons.get('visible', QIcon()))
        else:
            self.visibility_button.setIcon(self.icons.get('invisible', QIcon()))

        # Update CAM icon
        if self.layer_data['cut_bit'] > 0:
            self.cam_button.setIcon(self.icons.get('cam', QIcon()))
        else:
            self.cam_button.setIcon(self.icons.get('nocam', QIcon()))

        # Update color button
        color = QColor(self.layer_data['color'])
        self.color_button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")

        # Update name label appearance for current layer
        if self.is_current:
            palette = self.name_label.palette()
            palette.setColor(QPalette.ColorRole.WindowText,
                           palette.color(QPalette.ColorRole.HighlightedText))
            palette.setColor(QPalette.ColorRole.Window,
                           palette.color(QPalette.ColorRole.Highlight))
            self.name_label.setPalette(palette)
            self.name_label.setAutoFillBackground(True)
        else:
            self.name_label.setPalette(QApplication.palette())
            self.name_label.setAutoFillBackground(False)

        # Update object count
        self.count_label.setText(str(self.layer_data['object_count']))

    def update_layer_data(self, layer_data: Dict[str, Any], is_current: bool = False):
        """Update the layer data and refresh appearance"""
        self.layer_data = layer_data
        self.is_current = is_current
        self.name_label.setText(layer_data['name'])
        self._update_appearance()

    def _edit_color(self):
        """Open color selection dialog"""
        current_color = QColor(self.layer_data['color'])
        color = QColorDialog.getColor(current_color, self, "Choose a new color")

        if color.isValid():
            self.color_changed.emit(self.layer_id, color.name())

    def _name_mouse_press(self, event: QMouseEvent):
        """Handle mouse press on name label"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.pos()
            self.layer_selected.emit(self.layer_id)

    def _name_double_click(self, event: QMouseEvent):
        """Handle double click on name label to start editing"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._start_name_edit()

    def _name_mouse_move(self, event: QMouseEvent):
        """Handle mouse move for drag and drop"""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return

        if not self.drag_start_pos:
            return

        if ((event.pos() - self.drag_start_pos).manhattanLength() <
            QApplication.startDragDistance()):
            return

        # Start drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"layer:{self.layer_id}")
        drag.setMimeData(mime_data)

        # Create drag pixmap
        pixmap = QPixmap(self.size())
        self.render(pixmap)
        drag.setPixmap(pixmap)

        # Execute drag
        drag.exec(Qt.DropAction.MoveAction)

    def _name_mouse_release(self, event: QMouseEvent):
        """Handle mouse release"""
        self.drag_start_pos = None

    def _start_name_edit(self):
        """Start editing the layer name"""
        if self.is_editing_name:
            return

        self.is_editing_name = True
        self.name_label.hide()
        self.name_edit.setText(self.layer_data['name'])
        self.name_edit.show()
        self.name_edit.setFocus()
        self.name_edit.selectAll()

    def _commit_name_change(self):
        """Commit the name change"""
        if self.is_editing_name:
            new_name = self.name_edit.text().strip()
            if new_name and new_name != self.layer_data['name']:
                self.layer_renamed.emit(self.layer_id, new_name)
            self._cancel_name_edit()

    def _cancel_name_edit(self):
        """Cancel name editing"""
        if self.is_editing_name:
            self.is_editing_name = False
            self.name_edit.hide()
            self.name_label.show()


class LayerWindow(QWidget):
    """
    Layer management window for CAD operations.

    Provides a comprehensive interface for managing layers including:
    - Layer visibility and lock status
    - Layer creation, deletion, and reordering
    - Layer property editing (name, color, CAM settings)
    """

    # Signals
    layer_selected = Signal(str)  # layer_id
    layer_created = Signal()
    layer_deleted = Signal(str)  # layer_id
    layer_renamed = Signal(str, str)  # layer_id, new_name
    layer_visibility_changed = Signal(str, bool)  # layer_id, visible
    layer_lock_changed = Signal(str, bool)  # layer_id, locked
    layer_color_changed = Signal(str, str)  # layer_id, color
    layer_cam_changed = Signal(str, int, float)  # layer_id, cut_bit, cut_depth
    layer_reordered = Signal(str, int)  # layer_id, new_position

    def __init__(self, canvas=None, window_id: str = "main", parent: Optional[QWidget] = None):
        """
        Initialize the layer window.

        Args:
            canvas: Canvas object reference
            window_id: Unique identifier for this window
            parent: Parent widget, if any
        """
        super().__init__(parent)
        self.canvas = canvas
        self.window_id = window_id
        self.base_id = f"layerwin_{window_id}"
        self.layer_items = {}  # layer_id -> LayerItem
        self.current_layer_id = None

        # Register with global info
        layerwin_info.register_window(self.base_id, self)

        self._setup_ui()
        self._setup_icons()
        self._setup_drag_drop()

    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Scroll area for layers
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFixedWidth(220)

        # Container widget for layer items
        self.layer_container = QWidget()
        self.layer_layout = QVBoxLayout()
        self.layer_layout.setContentsMargins(0, 0, 0, 0)
        self.layer_layout.setSpacing(1)
        self.layer_container.setLayout(self.layer_layout)
        self.scroll_area.setWidget(self.layer_container)

        layout.addWidget(self.scroll_area)

        # Button panel
        button_panel = QFrame()
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_panel.setLayout(button_layout)

        # New layer button
        self.new_button = QPushButton()
        self.new_button.setFixedSize(24, 24)
        self.new_button.setToolTip("Create New Layer")
        self.new_button.clicked.connect(self._create_new_layer)
        button_layout.addWidget(self.new_button)

        # Delete layer button
        self.delete_button = QPushButton()
        self.delete_button.setFixedSize(24, 24)
        self.delete_button.setToolTip("Delete Current Layer")
        self.delete_button.clicked.connect(self._delete_current_layer)
        button_layout.addWidget(self.delete_button)

        button_layout.addStretch()
        layout.addWidget(button_panel)

    def _setup_icons(self):
        """Setup icons for the layer window"""
        # Try to load icons from the images directory
        icons = {}
        try:
            # These would be loaded from the actual image files
            # For now, we'll use simple colored pixmaps as placeholders
            icons['visible'] = self._create_icon_pixmap(Qt.GlobalColor.green, "👁")
            icons['invisible'] = self._create_icon_pixmap(Qt.GlobalColor.lightGray, "")
            icons['lock'] = self._create_icon_pixmap(Qt.GlobalColor.red, "🔒")
            icons['unlock'] = self._create_icon_pixmap(Qt.GlobalColor.green, "🔓")
            icons['cam'] = self._create_icon_pixmap(Qt.GlobalColor.blue, "⚙")
            icons['nocam'] = self._create_icon_pixmap(Qt.GlobalColor.lightGray, "")
            icons['new'] = self._create_icon_pixmap(Qt.GlobalColor.green, "+")
            icons['delete'] = self._create_icon_pixmap(Qt.GlobalColor.red, "×")

        except Exception as e:
            print(f"Warning: Could not load layer icons: {e}")
            # Create empty icons as fallback
            for key in ['visible', 'invisible', 'lock', 'unlock', 'cam', 'nocam', 'new', 'delete']:
                icons[key] = QIcon()

        layerwin_info.set_icons(self.base_id, icons)

        # Set button icons
        self.new_button.setIcon(icons['new'])
        self.delete_button.setIcon(icons['delete'])

    def _create_icon_pixmap(self, color: Qt.GlobalColor, text: str = "") -> QIcon:
        """Create a simple icon pixmap with color and optional text"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(color)

        if text:
            painter = QPainter(pixmap)
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
            painter.end()

        return QIcon(pixmap)

    def _setup_drag_drop(self):
        """Setup drag and drop functionality"""
        self.setAcceptDrops(True)
        self.layer_container.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasText() and event.mimeData().text().startswith("layer:"):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop events for layer reordering"""
        if not event.mimeData().hasText():
            return

        text = event.mimeData().text()
        if not text.startswith("layer:"):
            return

        layer_id = text[6:]  # Remove "layer:" prefix

        # Find drop position
        drop_pos = event.pos()
        target_position = self._get_drop_position(drop_pos)

        if target_position >= 0:
            self.layer_reordered.emit(layer_id, target_position)

        event.acceptProposedAction()

    def _get_drop_position(self, pos) -> int:
        """Get the target position for a drop operation"""
        # Find which layer item the drop is over
        for i in range(self.layer_layout.count()):
            item = self.layer_layout.itemAt(i)
            if item and item.widget():
                widget_rect = item.widget().geometry()
                if widget_rect.contains(pos):
                    # Determine if drop is in upper or lower half
                    if pos.y() < widget_rect.center().y():
                        return i
                    else:
                        return i + 1

        # Drop at end
        return self.layer_layout.count()

    def refresh_layers(self, layers_data: List[Dict[str, Any]], current_layer_id: str = None,
                      edit_layer_id: str = None):
        """
        Refresh the layer display with new data.

        Args:
            layers_data: List of layer data dictionaries
            current_layer_id: ID of the currently selected layer
            edit_layer_id: ID of layer to start editing (optional)
        """
        self.current_layer_id = current_layer_id

        # Clear existing layer items
        for layer_id, item in self.layer_items.items():
            item.setParent(None)
            item.deleteLater()
        self.layer_items.clear()

        # Clear layout
        while self.layer_layout.count():
            child = self.layer_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

        # Get icons
        icons = layerwin_info.get_icons(self.base_id)

        # Create new layer items
        for layer_data in layers_data:
            layer_id = layer_data['id']
            is_current = (layer_id == current_layer_id)

            layer_item = LayerItem(layer_id, layer_data, icons, is_current)

            # Connect signals
            layer_item.layer_selected.connect(self.layer_selected.emit)
            layer_item.layer_renamed.connect(self.layer_renamed.emit)
            layer_item.visibility_toggled.connect(self._toggle_visibility)
            layer_item.lock_toggled.connect(self._toggle_lock)
            layer_item.color_changed.connect(self.layer_color_changed.emit)
            layer_item.cam_edit_requested.connect(self._edit_cam_settings)

            self.layer_items[layer_id] = layer_item
            self.layer_layout.addWidget(layer_item)

        # Add stretch at the end
        self.layer_layout.addStretch()

        # Start editing if requested
        if edit_layer_id and edit_layer_id in self.layer_items:
            QTimer.singleShot(10, lambda: self.layer_items[edit_layer_id]._start_name_edit())

    def _toggle_visibility(self, layer_id: str):
        """Toggle layer visibility"""
        if layer_id in self.layer_items:
            layer_item = self.layer_items[layer_id]
            current_visible = layer_item.layer_data['visible']
            new_visible = not current_visible

            # Update the layer data
            layer_item.layer_data['visible'] = new_visible
            layer_item._update_appearance()

            # Emit signal
            self.layer_visibility_changed.emit(layer_id, new_visible)

    def _toggle_lock(self, layer_id: str):
        """Toggle layer lock status"""
        if layer_id in self.layer_items:
            layer_item = self.layer_items[layer_id]
            current_locked = layer_item.layer_data['locked']
            new_locked = not current_locked

            # Update the layer data
            layer_item.layer_data['locked'] = new_locked
            layer_item._update_appearance()

            # Emit signal
            self.layer_lock_changed.emit(layer_id, new_locked)

    def _edit_cam_settings(self, layer_id: str):
        """Open CAM settings dialog for a layer"""
        if layer_id not in self.layer_items:
            return

        layer_item = self.layer_items[layer_id]
        layer_data = layer_item.layer_data

        # Get available tools (this would come from the CAD system)
        available_tools = self._get_available_tools()

        # Open CAM dialog
        dialog = LayerCamDialog(
            layer_id,
            layer_data['cut_bit'],
            layer_data['cut_depth'],
            available_tools,
            self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            cut_bit, cut_depth = dialog.get_results()

            # Update layer data
            layer_item.layer_data['cut_bit'] = cut_bit
            layer_item.layer_data['cut_depth'] = cut_depth
            layer_item._update_appearance()

            # Emit signal
            self.layer_cam_changed.emit(layer_id, cut_bit, cut_depth)

    def _get_available_tools(self) -> List[tuple]:
        """Get list of available cutting tools"""
        # This would integrate with the CAD system's tool management
        # For now, return some sample tools
        return [
            (1, "1/8\" End Mill"),
            (2, "1/4\" End Mill"),
            (3, "1/16\" End Mill"),
            (4, "60° V-Bit"),
            (5, "90° V-Bit")
        ]

    def _create_new_layer(self):
        """Create a new layer"""
        self.layer_created.emit()

    def _delete_current_layer(self):
        """Delete the current layer"""
        if not self.current_layer_id:
            QApplication.beep()
            return

        if len(self.layer_items) <= 1:
            QApplication.beep()
            return

        # Get layer info
        if self.current_layer_id in self.layer_items:
            layer_item = self.layer_items[self.current_layer_id]
            layer_name = layer_item.layer_data['name']
            object_count = layer_item.layer_data['object_count']

            # Confirm deletion if layer has objects
            if object_count > 0:
                reply = QMessageBox.question(
                    self,
                    "Delete Layer",
                    f"Are you sure you want to delete the layer '{layer_name}' "
                    f"and all of the {object_count} objects in it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply != QMessageBox.StandardButton.Yes:
                    return

            self.layer_deleted.emit(self.current_layer_id)

    def update_layer_data(self, layer_id: str, layer_data: Dict[str, Any]):
        """Update data for a specific layer"""
        if layer_id in self.layer_items:
            is_current = (layer_id == self.current_layer_id)
            self.layer_items[layer_id].update_layer_data(layer_data, is_current)

    def set_current_layer(self, layer_id: str):
        """Set the current layer"""
        old_current = self.current_layer_id
        self.current_layer_id = layer_id

        # Update old current layer appearance
        if old_current and old_current in self.layer_items:
            layer_data = self.layer_items[old_current].layer_data
            self.layer_items[old_current].update_layer_data(layer_data, False)

        # Update new current layer appearance
        if layer_id and layer_id in self.layer_items:
            layer_data = self.layer_items[layer_id].layer_data
            self.layer_items[layer_id].update_layer_data(layer_data, True)


def create_layer_window(canvas=None, window_id: str = "main",
                       parent: Optional[QWidget] = None) -> LayerWindow:
    """
    Create and return a new layer window.

    Args:
        canvas: Canvas object reference
        window_id: Unique identifier for the window
        parent: Parent widget for the new window

    Returns:
        A new LayerWindow instance
    """
    return LayerWindow(canvas, window_id, parent)


if __name__ == "__main__":
    """Test the layer window independently."""
    import sys

    app = QApplication(sys.argv)

    # Create test layer data
    test_layers = [
        {
            'id': 'layer1',
            'name': 'Layer 1',
            'visible': True,
            'locked': False,
            'color': '#FF0000',
            'cut_bit': 1,
            'cut_depth': -0.1,
            'object_count': 5
        },
        {
            'id': 'layer2',
            'name': 'Layer 2',
            'visible': True,
            'locked': True,
            'color': '#00FF00',
            'cut_bit': 0,
            'cut_depth': 0.0,
            'object_count': 3
        },
        {
            'id': 'layer3',
            'name': 'Hidden Layer',
            'visible': False,
            'locked': False,
            'color': '#0000FF',
            'cut_bit': 2,
            'cut_depth': -0.2,
            'object_count': 0
        }
    ]

    # Create and show the layer window
    layer_window = create_layer_window()
    layer_window.setWindowTitle("Layer Window Test")
    layer_window.show()

    # Populate with test data
    layer_window.refresh_layers(test_layers, 'layer1')

    # Connect signals for testing
    layer_window.layer_selected.connect(
        lambda layer_id: print(f"Layer selected: {layer_id}")
    )
    layer_window.layer_renamed.connect(
        lambda layer_id, name: print(f"Layer {layer_id} renamed to: {name}")
    )
    layer_window.layer_visibility_changed.connect(
        lambda layer_id, visible: print(f"Layer {layer_id} visibility: {visible}")
    )
    layer_window.layer_lock_changed.connect(
        lambda layer_id, locked: print(f"Layer {layer_id} locked: {locked}")
    )
    layer_window.layer_color_changed.connect(
        lambda layer_id, color: print(f"Layer {layer_id} color: {color}")
    )
    layer_window.layer_cam_changed.connect(
        lambda layer_id, bit, depth: print(f"Layer {layer_id} CAM: bit={bit}, depth={depth}")
    )
    layer_window.layer_created.connect(
        lambda: print("New layer requested")
    )
    layer_window.layer_deleted.connect(
        lambda layer_id: print(f"Delete layer requested: {layer_id}")
    )
    layer_window.layer_reordered.connect(
        lambda layer_id, pos: print(f"Layer {layer_id} moved to position {pos}")
    )

    print("Layer window test started. Try interacting with the layers!")
    sys.exit(app.exec())
