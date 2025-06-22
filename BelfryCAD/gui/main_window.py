# filepath: /Users/gminette/dev/git-repos/pyBelfryCad/src/gui/main_window.py
"""Main window for the BelfryCad application."""
import math
import os
import logging

from PySide6.QtCore import (
    Qt, QSize, QTimer
)
from PySide6.QtGui import (
    QShortcut, QKeySequence, QIcon
)
from PySide6.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox, QDialog
)

from ..core.undo_redo import UndoRedoManager
from ..core.cad_objects import CADObject
from ..tools.base import ToolCategory, ToolManager
from ..tools import available_tools

from .mainmenu import MainMenuBar
from .grid_info import GridInfo, GridUnits
from .grid_graphics_items import GridBackground, RulersForeground
from .palette_system import create_default_palettes
from .panes.category_button import CategoryToolButton
from .cad_scene import CadScene
from .cad_view import CadView
from .icon_manager import get_icon
from .cad_item import CadItem
from .print_manager import CadPrintManager
from .feed_wizard import FeedWizardDialog
from .tool_table_dialog import ToolTableDialog
from .preferences_dialog import PreferencesDialog
from .gear_wizard_dialog import GearWizardDialog
from .gcode_backtracer_dialog import GCodeBacktracerDialog
from .zoom_edit_widget import ZoomEditWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, config, preferences, document):
        super().__init__()
        self.config = config
        self.preferences = preferences
        self.document = document

        # Initialize undo/redo system
        self.undo_manager = UndoRedoManager(max_undo_levels=50)
        self.undo_manager.add_callback(self._on_undo_state_changed)

        # Connect layer manager to undo system
        if hasattr(self.document, 'layers'):
            self.document.layers.set_undo_manager(self.undo_manager)

        # Initialize print system
        self.print_manager = None  # Will be initialized after scene creation

        # Track graphics items by object ID for updates/deletion
        self.graphics_items = {}  # object_id -> list of graphics items

        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(self.config.APP_NAME)

        # Set window size - check preferences first, then default to 1024x768
        saved_geometry = self.preferences.get("window_geometry", None)
        if saved_geometry:
            try:
                # Parse saved geometry in format "WIDTHxHEIGHT+X+Y"
                parts = saved_geometry.replace('+', 'x').split('x')
                if len(parts) >= 2:
                    width = int(parts[0])
                    height = int(parts[1])
                    self.resize(width, height)

                    # Also restore position if available
                    if len(parts) >= 4:
                        x = int(parts[2])
                        y = int(parts[3])
                        self.move(x, y)
                else:
                    # Fallback to default size
                    self.resize(1024, 768)
            except (ValueError, IndexError):
                # If parsing fails, use default size
                self.resize(1024, 768)
        else:
            # Set default window size to 1024x768
            self.resize(1024, 768)

        self._create_menu()
        self._create_toolbar()
        self._create_canvas()
        self._setup_palettes()  # Add palette system setup
        self._setup_tools()
        self._setup_category_shortcuts()
        self._update_shortcut_tooltips()
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts for the main window."""
        zoom_in_shortcut = QShortcut(QKeySequence("Ctrl+="), self)
        zoom_in_shortcut.activated.connect(self._zoom_in)
        zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        zoom_out_shortcut.activated.connect(self._zoom_out)
        reset_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)
        reset_shortcut.activated.connect(self._reset_zoom)
        zoom_fit_shortcut = QShortcut(QKeySequence("Ctrl+0"), self)
        zoom_fit_shortcut.activated.connect(self._zoom_to_fit)
        deselect_shortcut = QShortcut(QKeySequence("Escape"), self)
        deselect_shortcut.activated.connect(self._clear_selection)
        select_all_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        select_all_shortcut.activated.connect(self._select_all)

    def _setup_category_shortcuts(self):
        """Set up keyboard shortcuts for tool category activation"""
        # Define key mappings for tool categories
        self.category_key_mappings = {
            'Space': ToolCategory.SELECTOR,  # Spacebar for Selector
            'N': ToolCategory.NODES,         # N for Nodes
            'T': ToolCategory.TRANSFORMS,    # T for Transform
            'D': ToolCategory.DUPLICATORS,   # D for Duplicators
            'L': ToolCategory.LINES,         # L for Lines
            'A': ToolCategory.ARCS,          # A for Arcs
            'E': ToolCategory.ELLIPSES,      # E for Ellipses
            'P': ToolCategory.POLYGONS,      # P for Polygons
            'M': ToolCategory.MISC,          # M for Miscellaneous
            'C': ToolCategory.CAM,           # C for Cam
            'I': ToolCategory.DIMENSIONS,    # I for dImensions
        }

        # Create shortcuts for each category
        self.category_shortcuts = {}
        for key, category in self.category_key_mappings.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(
                lambda cat=category: self._activate_category_shortcut(cat)
            )
            self.category_shortcuts[category] = shortcut

    def _update_shortcut_tooltips(self):
        """Update category button tooltips to show keyboard shortcuts"""
        if not hasattr(self, 'category_key_mappings'):
            return

        for key, category in self.category_key_mappings.items():
            if (hasattr(self, 'category_buttons') and
                    category in self.category_buttons):
                button = self.category_buttons[category]
                current_tooltip = button.toolTip()
                # Only add shortcut hint if not already present
                if f"({key})" not in current_tooltip:
                    new_tooltip = f"{current_tooltip} ({key})"
                    button.setToolTip(new_tooltip)

    def _activate_category_shortcut(self, category):
        """Handle keyboard shortcut activation for a tool category"""
        if (not hasattr(self, 'category_buttons') or
                category not in self.category_buttons):
            return

        category_button = self.category_buttons[category]

        # Check if this category has only one tool
        if len(category_button.tools) == 1:
            # Single tool: activate it directly
            if category_button.current_tool:
                self.activate_tool(category_button.current_tool.token)
        else:
            # Multiple tools: show the palette
            category_button._show_palette()

    def _create_menu(self):
        """Create the comprehensive main menu system."""
        # Initialize the main menu bar
        self.main_menu = MainMenuBar(self, self.preferences)

        # Connect menu signals to handlers
        self._connect_menu_signals()

    def _connect_menu_signals(self):
        """Connect menu signals to their corresponding handlers."""
        # File menu connections
        self.main_menu.new_triggered.connect(self.new_file)
        self.main_menu.open_triggered.connect(self.open_file)
        self.main_menu.save_triggered.connect(self.save_file)
        self.main_menu.save_as_triggered.connect(self.save_as_file)
        self.main_menu.close_triggered.connect(self.close_file)
        self.main_menu.import_triggered.connect(self.import_file)
        self.main_menu.export_triggered.connect(self.export_file)
        self.main_menu.page_setup_triggered.connect(self.page_setup)
        self.main_menu.print_triggered.connect(self.print_file)

        # Edit menu connections
        self.main_menu.undo_triggered.connect(self.undo)
        self.main_menu.redo_triggered.connect(self.redo)
        self.main_menu.cut_triggered.connect(self.cut)
        self.main_menu.copy_triggered.connect(self.copy)
        self.main_menu.paste_triggered.connect(self.paste)
        self.main_menu.clear_triggered.connect(self.clear)
        self.main_menu.select_all_triggered.connect(self._select_all)
        self.main_menu.select_similar_triggered.connect(self._select_similar)
        self.main_menu.deselect_all_triggered.connect(self._clear_selection)
        self.main_menu.group_triggered.connect(self.group_selection)
        self.main_menu.ungroup_triggered.connect(self.ungroup_selection)

        # Arrange submenu connections
        self.main_menu.raise_to_top_triggered.connect(self.raise_to_top)
        self.main_menu.raise_triggered.connect(self.raise_selection)
        self.main_menu.lower_triggered.connect(self.lower_selection)
        self.main_menu.lower_to_bottom_triggered.connect(self.lower_to_bottom)

        # Transform connections
        self.main_menu.rotate_90_ccw_triggered.connect(
            lambda: self.rotate_selection(-90)
        )
        self.main_menu.rotate_90_cw_triggered.connect(
            lambda: self.rotate_selection(90)
        )
        self.main_menu.rotate_180_triggered.connect(
            lambda: self.rotate_selection(180)
        )

        # Conversion connections
        self.main_menu.convert_to_lines_triggered.connect(self.convert_to_lines)
        self.main_menu.convert_to_curves_triggered.connect(self.convert_to_curves)
        self.main_menu.simplify_curves_triggered.connect(self.simplify_curves)
        self.main_menu.smooth_curves_triggered.connect(self.smooth_curves)
        self.main_menu.join_curves_triggered.connect(self.join_curves)
        self.main_menu.vectorize_bitmap_triggered.connect(self.vectorize_bitmap)

        # Boolean operations connections
        self.main_menu.union_polygons_triggered.connect(self.union_polygons)
        self.main_menu.difference_polygons_triggered.connect(self.difference_polygons)
        self.main_menu.intersection_polygons_triggered.connect(self.intersection_polygons)

        # View menu connections
        self.main_menu.actual_size_triggered.connect(self._reset_zoom)
        self.main_menu.zoom_to_fit_triggered.connect(self._zoom_to_fit)
        self.main_menu.zoom_in_triggered.connect(self._zoom_in)
        self.main_menu.zoom_out_triggered.connect(self._zoom_out)
        self.main_menu.show_origin_toggled.connect(self.toggle_show_origin)
        self.main_menu.show_grid_toggled.connect(self.toggle_show_grid)

        # Palette visibility connections
        self.main_menu.show_info_panel_toggled.connect(self.toggle_info_panel)
        self.main_menu.show_properties_toggled.connect(self.toggle_properties)
        self.main_menu.show_layers_toggled.connect(self.toggle_layers)
        self.main_menu.show_snap_settings_toggled.connect(self.toggle_snap_settings)

        # CAM menu connections
        self.main_menu.configure_mill_triggered.connect(self.configure_mill)
        self.main_menu.tool_table_triggered.connect(self.tool_table)
        self.main_menu.speeds_feeds_wizard_triggered.connect(self.speeds_feeds_wizard)
        self.main_menu.generate_gcode_triggered.connect(self.generate_gcode)
        self.main_menu.backtrace_gcode_triggered.connect(self.backtrace_gcode)
        self.main_menu.gear_wizard_triggered.connect(self.gear_wizard)

        # Window menu connections
        self.main_menu.minimize_triggered.connect(self.showMinimized)
        self.main_menu.cycle_windows_triggered.connect(self.cycle_windows)

        # Preferences menu connection
        self.main_menu.preferences_triggered.connect(self.show_preferences)

    def _create_toolbar(self):
        """Create a toolbar with drawing tools"""
        self.toolbar = self.addToolBar("Tools")
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.toolbar)
        # Set the icon size to 48x48 for 150% size visibility
        self.toolbar.setIconSize(QSize(48, 48))
        # Set spacing between toolbar buttons to 2 pixels using stylesheet
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        # Make toolbar more compact
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        # Apply custom stylesheet with 2px spacing
        self.toolbar.setStyleSheet("""
            QToolBar {
                margin: 2px;
                border: none;
            }
            QToolButton {
                margin: 2px;
                padding: 0px;
                border: none;
            }
        """)
        # We'll populate this with category buttons in _setup_tools()

        # Store category buttons for reference
        self.category_buttons = {}

    def get_scene(self):
        return self.cad_scene

    def get_view(self):
        return self.cad_view

    def _create_canvas(self):
        # Create the CAD scene component
        self.grid_info = GridInfo(GridUnits.INCHES_DECIMAL)
        self.cad_scene = CadScene(self)
        self.cad_view = CadView(self.cad_scene)
        self.print_manager = CadPrintManager(
            self, self.cad_scene, self.document)
        self.cad_view.mouseMoveEvent = self._mouse_move_event

        # Add grid background
        self.grid = GridBackground(self.grid_info)
        self.cad_scene.addItem(self.grid)

        # Add rulers
        self.rulers = RulersForeground(self.grid_info)
        self.cad_scene.addItem(self.rulers)

        # Set the CAD scene as the central widget
        self.setCentralWidget(self.cad_view)

    def _setup_palettes(self):
        """Setup the palette system with dockable windows."""
        # Create the palette manager and default palettes
        self.palette_manager = create_default_palettes(self)

        # Connect palette visibility changes to menu sync
        self.palette_manager.palette_visibility_changed.connect(
            self._on_palette_visibility_changed
        )

        # Connect palette content to canvas and other components
        self._connect_palette_content()

        # Restore palette layout from preferences if available
        saved_layout = self.preferences.get("palette_layout", None)
        if saved_layout:
            self.palette_manager.restore_palette_layout(saved_layout)

    def _connect_palette_content(self):
        """Connect palette content widgets to the main window functionality."""
        # Connect info pane to canvas for position updates and selection
        info_pane = self.palette_manager.get_palette_content("info_pane")
        #if info_pane and hasattr(self, 'canvas'):
            # Connect canvas mouse move events to info pane updates
            #self._connect_info_pane(info_pane)

        # Connect config pane to document and selection
        config_pane = self.palette_manager.get_palette_content("config_pane")
        if config_pane and hasattr(self, 'document'):
            # Connect the config pane to selection changes
            self._connect_config_pane(config_pane)

        # Connect layer pane to document layer management
        layer_pane = self.palette_manager.get_palette_content(
            "layer_pane")
        if (layer_pane and hasattr(self, 'document') and
                hasattr(self.document, 'layers')):
            self._connect_layer_pane(layer_pane)

    def _connect_layer_pane(self, layer_pane):
        """Connect the layer pane to the document's layer manager."""
        # Connect layer pane signals to document layer manager
        layer_pane.layer_created.connect(self._on_layer_created)
        layer_pane.layer_deleted.connect(self._on_layer_deleted)
        layer_pane.layer_selected.connect(self._on_layer_selected)
        layer_pane.layer_renamed.connect(self._on_layer_renamed)
        layer_pane.layer_visibility_changed.connect(
            self._on_layer_visibility_changed)
        layer_pane.layer_lock_changed.connect(self._on_layer_lock_changed)
        layer_pane.layer_color_changed.connect(self._on_layer_color_changed)
        layer_pane.layer_cam_changed.connect(self._on_layer_cam_changed)
        layer_pane.layer_reordered.connect(self._on_layer_reordered)

        # Initialize layer pane with current layer data
        self._refresh_layer_pane()

    def _refresh_layer_pane(self):
        """Refresh the layer pane with current layer data."""
        layer_pane = self.palette_manager.get_palette_content(
            "layer_pane")
        if not layer_pane or not hasattr(self.document, 'layers'):
            return

        # Get all layer data from the layer manager
        layers = self.document.layers.get_all_layers()
        current_layer = self.document.layers.get_current_layer()

        # Update the layer pane
        layer_pane.refresh_layers(layers, current_layer)

    def _on_layer_created(self):
        """Handle layer creation request from layer window."""
        if hasattr(self.document, 'layers'):
            new_layer = self.document.layers.create_layer()
            self.document.layers.set_current_layer(new_layer)
            self._refresh_layer_pane()

    def _on_layer_deleted(self, layer):
        """Handle layer deletion request from layer pane."""
        if self.document.layers.delete_layer(layer):
            self._refresh_layer_pane()

    def _on_layer_selected(self, layer):
        """Handle layer selection from layer pane."""
        self.document.layers.set_current_layer(layer)
        self._refresh_layer_pane()

    def _on_layer_renamed(self, layer, new_name):
        """Handle layer rename from layer pane."""
        self.document.layers.set_layer_name(layer, new_name)
        self._refresh_layer_pane()

    def _on_layer_visibility_changed(self, layer, visible):
        """Handle layer visibility change from layer window."""
        self.document.layers.set_layer_visible(layer, visible)

    def _on_layer_lock_changed(self, layer, locked):
        """Handle layer lock change from layer window."""
        self.document.layers.set_layer_locked(layer, locked)

    def _on_layer_color_changed(self, layer, color):
        """Handle layer color change from layer window."""
        self.document.layers.set_layer_color(layer, color)

    def _on_layer_cam_changed(self, layer, cut_bit, cut_depth):
        """Handle layer CAM settings change from layer window."""
        self.document.layers.set_layer_cut_bit(layer, cut_bit)
        self.document.layers.set_layer_cut_depth(layer, cut_depth)

    def _on_layer_reordered(self, layer, new_position):
        """Handle layer reorder from layer pane."""
        self.document.layers.reorder_layer(layer, new_position)
        self._refresh_layer_pane()

    def _connect_config_pane(self, config_pane):
        """Connect config pane to the selection system for property editing."""
        # Connect config pane field changes to property updates
        config_pane.field_changed.connect(self._on_property_changed)

        # Set up periodic check for selection changes
        if not hasattr(self, '_selection_timer'):
            self._selection_timer = QTimer()
            self._selection_timer.timeout.connect(
                self._check_selection_changes
            )
            self._selection_timer.start(100)  # Check every 100ms

        # Track current selection state
        self._current_selection = set()

    def _check_selection_changes(self):
        """Check if selection changed and update config pane if needed."""
        if not hasattr(self, 'tool_manager'):
            return

        # Get current tool and check if it's the selector tool
        current_tool = self.tool_manager.get_active_tool()
        if current_tool and hasattr(current_tool, 'selected_objects'):
            # Get current selection using getattr for type safety
            selected_objects = getattr(current_tool, 'selected_objects', [])
            current_selection = set(
                obj.object_id for obj in selected_objects
            )
            # Check if selection changed
            if current_selection != self._current_selection:
                self._current_selection = current_selection
                self._update_config_pane_for_selection(selected_objects)

    def _update_config_pane_for_selection(self, selected_objects):
        """Update config pane based on current selection."""
        config_pane = self.palette_manager.get_palette_content("config_pane")
        if not config_pane:
            return

        if not selected_objects:
            # No selection - clear config pane or show default fields
            self._populate_config_pane_for_objects([])
        elif len(selected_objects) == 1:
            # Single object selected - show its properties
            self._populate_config_pane_for_objects(selected_objects)
        else:
            # Multiple objects selected - show common properties
            self._populate_config_pane_for_objects(selected_objects)

    def _populate_config_pane_for_objects(self, objects):
        """Populate config pane with properties for given objects."""
        config_pane = self.palette_manager.get_palette_content("config_pane")
        if not config_pane:
            return

        # Store reference to selected objects for property updates
        # We'll use dynamic attributes to work around type checker limitations
        setattr(config_pane, 'selected_objects', objects)

        # Update the config pane fields based on selection
        # Check if the config pane has the populate method
        if hasattr(config_pane, 'populate'):
            populate_method = getattr(config_pane, 'populate', None)
            if callable(populate_method):
                populate_method()

    def _on_property_changed(self, field_name, datum, value):
        """Handle property changes from config pane."""
        config_pane = self.palette_manager.get_palette_content("config_pane")
        if not config_pane or not hasattr(config_pane, 'selected_objects'):
            return

        # Apply property change to all selected objects
        for obj in getattr(config_pane, 'selected_objects', []):
            try:
                # Update object attribute
                if hasattr(obj, 'attributes'):
                    obj.attributes[field_name] = value
                elif hasattr(obj, field_name):
                    setattr(obj, field_name, value)

                # Mark object as modified
                obj.selected = True  # Ensure it stays selected

            except Exception as e:
                print(f"Error updating property {field_name} on object "
                      f"{obj.object_id}: {e}")

    def _setup_tools(self):
        """Set up the tool system and register tools"""
        # Initialize tool manager
        self.tool_manager = ToolManager(
            self, self.document, self.preferences)

        # Register all available tools and group by category
        self.tools = {}
        tools_by_category = {}

        for tool_class in available_tools:
            tool = self.tool_manager.register_tool(tool_class)
            self.tools[tool.definition.token] = tool
            # Connect tool signals to redraw
            #tool.object_created.connect(self.on_object_created)

            # Group tools by category
            category = tool.definition.category
            if category not in tools_by_category:
                tools_by_category[category] = []
            tools_by_category[category].append(tool)

            # Add tool to tools menu
            # Create tool menu action
            # menu_action = QAction(tool.definition.name, self)
            # icon = self._load_tool_icon(tool.definition.icon)
            # if icon:
            #     menu_action.setIcon(icon)
            # menu_action.triggered.connect(
            #     lambda checked, t=tool.definition.token:
            #         self.activate_tool(t)
            # )
            # self.tools_menu.addAction(menu_action)

        # Create category buttons for toolbar
        for category, category_tools in tools_by_category.items():
            if not category_tools:
                continue

            # Extract tool definitions from tool instances
            tool_definitions = [tool.definition for tool in category_tools]

            # Create category button
            category_button = CategoryToolButton(
                category,
                tool_definitions,
                get_icon,
                parent=self.toolbar
            )

            # Connect category button to tool activation
            category_button.tool_selected.connect(self.activate_tool)

            # Add to toolbar
            self.toolbar.addWidget(category_button)
            self.category_buttons[category] = category_button

        # Activate the selector tool by default
        if "OBJSEL" in self.tools:
            self.activate_tool("OBJSEL")

    def get_dpi(self):
        """Get the DPI from the main window."""
        screen = self.screen()
        if screen:
            return screen.logicalDotsPerInch()
        return 96.0  # Default DPI if screen info not available

    def activate_tool(self, tool_token):
        """Activate a tool by its token"""
        self.tool_manager.activate_tool(tool_token)

        # Clear active state from all category buttons first
        for category_button in self.category_buttons.values():
            category_button.set_active(False)

        # Update the appropriate category button to show the active tool
        if tool_token in self.tools:
            active_tool = self.tools[tool_token]
            category = active_tool.definition.category
            if category in self.category_buttons:
                category_button = self.category_buttons[category]
                category_button.set_current_tool(tool_token)
                category_button.set_active(True)

    def update_title(self):
        title = self.config.APP_NAME
        if self.document.filename:
            title += f" - {self.document.filename}"
        if self.document.is_modified():
            title += " *"
        self.setWindowTitle(title)

    def new_file(self):
        if self.document.is_modified():
            if not self._confirm_discard_changes():
                return
        self.document.new()
        self.update_title()
        self.cad_scene.clear()

    def open_file(self):
        if self.document.is_modified():
            if not self._confirm_discard_changes():
                return
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Document",
            "",
            "BelfryCad files (*.tkcad);;SVG files (*.svg);;"
            "DXF files (*.dxf);;All files (*.*)"
        )
        if filename:
            try:
                self.document.load(filename)
                self.update_title()
                self.cad_scene.clear()
            except Exception as e:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Open Error")
                msg.setText(f"Failed to open file:\n{e}")
                msg.exec()

    def save_file(self):
        if not self.document.filename:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save Document",
                "",
                "BelfryCad files (*.tkcad);;SVG files (*.svg);;"
                "DXF files (*.dxf);;All files (*.*)"
            )
            if not filename:
                return
            self.document.filename = filename
        try:
            self.document.save()
            self.update_title()
        except Exception as e:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Save Error")
            msg.setText(f"Failed to save file:\n{e}")
            msg.exec()

    def save_as_file(self):
        """Handle Save As menu action."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Document As",
            "",
            "BelfryCad files (*.tkcad);;SVG files (*.svg);;"
            "DXF files (*.dxf);;All files (*.*)"
        )
        if filename:
            try:
                self.document.filename = filename
                self.document.save()
                self.main_menu.add_recent_file(filename)
                self.update_title()
            except Exception as e:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Save Error")
                msg.setText(f"Failed to save file:\n{e}")
                msg.exec()

    def close_file(self):
        """Handle Close menu action."""
        if self.document.is_modified():
            if not self._confirm_discard_changes():
                return
        self.document.new()  # Reset to new document
        self.cad_scene.clear()
        self.update_title()

    def import_file(self):
        """Handle Import menu action."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import File",
            "",
            "SVG files (*.svg);;DXF files (*.dxf);;All files (*.*)"
        )
        if filename:
            try:
                # TODO: Implement import functionality
                QMessageBox.information(
                    self, "Import",
                    f"Import functionality not yet implemented for {filename}"
                )
            except Exception as e:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Import Error")
                msg.setText(f"Failed to import file:\n{e}")
                msg.exec()

    def export_file(self):
        """Handle Export menu action."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export File",
            "",
            "PDF files (*.pdf);;SVG files (*.svg);;DXF files (*.dxf);;"
            "All files (*.*)"
        )
        if filename:
            try:
                # Check file extension to determine export type
                if filename.lower().endswith('.pdf'):
                    # Use print manager for PDF export
                    if hasattr(self, 'print_manager'):
                        return self.print_manager.export_to_pdf(filename)
                    else:
                        QMessageBox.information(
                            self, "Export",
                            "PDF export not available"
                        )
                else:
                    # TODO: Implement other export formats
                    QMessageBox.information(
                        self, "Export",
                        f"Export format not yet implemented for {filename}"
                    )
            except Exception as e:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Export Error")
                msg.setText(f"Failed to export file:\n{e}")
                msg.exec()

    def page_setup(self):
        """Handle Page Setup menu action."""
        if hasattr(self, 'print_manager'):
            self.print_manager.show_page_setup_dialog()
        else:
            # Fallback message
            QMessageBox.information(
                self, "Page Setup",
                "Page setup functionality not available"
            )

    def print_file(self):
        """Handle Print menu action."""
        if hasattr(self, 'print_manager'):
            self.print_manager.show_print_dialog()
        else:
            # Fallback message
            QMessageBox.information(
                self, "Print",
                "Print functionality not available"
            )

    def export_pdf(self):
        """Export the current drawing to PDF."""
        if hasattr(self, 'print_manager'):
            return self.print_manager.export_to_pdf()
        else:
            # Fallback message
            QMessageBox.information(
                self, "Export PDF",
                "PDF export functionality not available"
            )
            return False

    # Edit menu handlers
    def undo(self):
        """Handle Undo menu action."""
        if hasattr(self, 'undo_manager') and self.undo_manager.undo():
            self.draw_objects()  # Redraw to reflect changes
            self.update_title()  # Update window title

    def redo(self):
        """Handle Redo menu action."""
        if hasattr(self, 'undo_manager') and self.undo_manager.redo():
            self.draw_objects()  # Redraw to reflect changes
            self.update_title()  # Update window title

    def cut(self):
        """Handle Cut menu action."""
        # Copy selected objects to clipboard, then delete them
        if self.copy():
            self._delete_selected_objects()

    def copy(self):
        """Handle Copy menu action."""
        selected_objects = self._get_selected_objects()
        if not selected_objects:
            return False

        # Store selected objects in clipboard format
        self._clipboard_data = []
        for obj in selected_objects:
            # Create a deep copy of the object data
            obj_data = {
                'type': obj.object_type,
                'coords': [{'x': coord.x, 'y': coord.y} for coord in obj.coords],
                'attributes': dict(obj.attributes),
                'layer': getattr(obj, 'layer', None)
            }
            self._clipboard_data.append(obj_data)

        return len(self._clipboard_data) > 0

    def paste(self):
        """Handle Paste menu action."""
        if not hasattr(self, '_clipboard_data') or not self._clipboard_data:
            return

        # Get current mouse position or use origin as paste location
        paste_offset_x = 10.0  # Default offset to avoid overlapping
        paste_offset_y = 10.0

        # Clear current selection
        self._clear_selection()

        # Create new objects from clipboard data
        new_objects = []
        for obj_data in self._clipboard_data:
            # Create new object with offset coordinates
            new_coords = []
            for coord in obj_data['coords']:
                new_coords.append(Point(
                    coord['x'] + paste_offset_x,
                    coord['y'] + paste_offset_y
                ))

            # Create new object
            new_obj = CADObject(
                mainwin=self,
                object_id=self.document.objects.get_next_id(),
                object_type=obj_data['type'],
                coords=new_coords,
                attributes=obj_data['attributes'].copy()
            )

            # Set layer if specified
            if obj_data['layer'] is not None:
                new_obj.layer = obj_data['layer']

            # Add to document
            if hasattr(self.document, 'objects'):
                self.document.objects.add_object(new_obj)
                new_objects.append(new_obj)

        # Select the newly pasted objects
        if new_objects:
            self._select_objects(new_objects)
            self.draw_objects()  # Redraw to show new objects

        return len(new_objects) > 0

    def clear(self):
        """Handle Clear menu action."""
        # TODO: Implement clear functionality
        QMessageBox.information(
            self, "Clear",
            "Clear functionality not yet implemented"
        )

    def group_selection(self):
        """Handle Group menu action."""
        # TODO: Implement group functionality
        QMessageBox.information(
            self, "Group",
            "Group functionality not yet implemented"
        )

    def ungroup_selection(self):
        """Handle Ungroup menu action."""
        # TODO: Implement ungroup functionality
        QMessageBox.information(
            self, "Ungroup",
            "Ungroup functionality not yet implemented"
        )

    # Arrange submenu handlers
    def raise_to_top(self):
        """Handle Raise to Top menu action."""
        # TODO: Implement raise to top functionality
        QMessageBox.information(
            self, "Raise to Top",
            "Raise to Top functionality not yet implemented"
        )

    def raise_selection(self):
        """Handle Raise menu action."""
        # TODO: Implement raise functionality
        QMessageBox.information(
            self, "Raise",
            "Raise functionality not yet implemented"
        )

    def lower_selection(self):
        """Handle Lower menu action."""
        # TODO: Implement lower functionality
        QMessageBox.information(
            self, "Lower",
            "Lower functionality not yet implemented"
        )

    def lower_to_bottom(self):
        """Handle Lower to Bottom menu action."""
        # TODO: Implement lower to bottom functionality
        QMessageBox.information(
            self, "Lower to Bottom",
            "Lower to Bottom functionality not yet implemented"
        )

    # Transform handlers
    def rotate_selection(self, angle):
        """Handle rotation menu actions."""
        # TODO: Implement rotation functionality
        QMessageBox.information(
            self, "Rotate",
            f"Rotate {angle}° functionality not yet implemented"
        )

    # Conversion handlers
    def convert_to_lines(self):
        """Handle Convert to Lines menu action."""
        # TODO: Implement convert to lines functionality
        QMessageBox.information(
            self, "Convert to Lines",
            "Convert to Lines functionality not yet implemented"
        )

    def convert_to_curves(self):
        """Handle Convert to Curves menu action."""
        # TODO: Implement convert to curves functionality
        QMessageBox.information(
            self, "Convert to Curves",
            "Convert to Curves functionality not yet implemented"
        )

    def simplify_curves(self):
        """Handle Simplify Curves menu action."""
        # TODO: Implement simplify curves functionality
        QMessageBox.information(
            self, "Simplify Curves",
            "Simplify Curves functionality not yet implemented"
        )

    def smooth_curves(self):
        """Handle Smooth Curves menu action."""
        # TODO: Implement smooth curves functionality
        QMessageBox.information(
            self, "Smooth Curves",
            "Smooth Curves functionality not yet implemented"
        )

    def join_curves(self):
        """Handle Join Curves menu action."""
        # TODO: Implement join curves functionality
        QMessageBox.information(
            self, "Join Curves",
            "Join Curves functionality not yet implemented"
        )

    def vectorize_bitmap(self):
        """Handle Vectorize Bitmap menu action."""
        # TODO: Implement vectorize bitmap functionality
        QMessageBox.information(
            self, "Vectorize Bitmap",
            "Vectorize Bitmap functionality not yet implemented"
        )

    # Boolean operations handlers
    def union_polygons(self):
        """Handle Union of Polygons menu action."""
        # TODO: Implement union functionality
        QMessageBox.information(
            self, "Union of Polygons",
            "Union of Polygons functionality not yet implemented"
        )

    def difference_polygons(self):
        """Handle Difference of Polygons menu action."""
        # TODO: Implement difference functionality
        QMessageBox.information(
            self, "Difference of Polygons",
            "Difference of Polygons functionality not yet implemented"
        )

    def intersection_polygons(self):
        """Handle Intersection of Polygons menu action."""
        # TODO: Implement intersection functionality
        QMessageBox.information(
            self, "Intersection of Polygons",
            "Intersection of Polygons functionality not yet implemented"
        )

    def toggle_show_origin(self, show):
        """Handle Show Origin toggle."""
        self.preferences.set("show_origin", show)
        # TODO: Actually toggle origin display

    def toggle_show_grid(self, show):
        """Handle Show Grid toggle."""
        self.preferences.set("show_grid", show)
        # TODO: Actually toggle grid display

    # CAM menu handlers
    def configure_mill(self):
        """Handle Configure Mill menu action."""
        # TODO: Implement mill configuration
        QMessageBox.information(
            self, "Configure Mill",
            "Mill configuration functionality not yet implemented"
        )

    def speeds_feeds_wizard(self):
        """Handle Speeds & Feeds Wizard menu action."""
        dialog = FeedWizardDialog(parent=self)
        dialog.exec()

    def generate_gcode(self):
        """Handle Generate G-Code menu action."""
        # TODO: Implement G-code generation
        QMessageBox.information(
            self, "Generate G-Code",
            "G-Code generation functionality not yet implemented"
        )

    def backtrace_gcode(self):
        """Handle Backtrace G-Code menu action."""
        dialog = GCodeBacktracerDialog(parent=self)
        dialog.exec()

    def gear_wizard(self):
        """Handle Gear Wizard menu action."""
        logger.info("Opening Gear Wizard dialog")
        try:
            dialog = GearWizardDialog(parent=self)
            logger.info("Gear Wizard dialog created")
            result = dialog.exec()
            logger.info(f"Gear Wizard dialog closed with result: {result}")
        except Exception as e:
            logger.error(f"Error opening Gear Wizard dialog: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open Gear Wizard: {str(e)}"
            )

    # Window menu handlers
    def cycle_windows(self):
        """Handle Cycle Windows menu action."""
        # TODO: Implement window cycling
        QMessageBox.information(
            self, "Cycle Windows",
            "Window cycling functionality not yet implemented"
        )

    def show_preferences(self):
        """Show the preferences dialog."""
        # Create and show preferences dialog
        dialog = PreferencesDialog(self)
        result = dialog.exec()

        if result == dialog.DialogCode.Accepted:
            # Preferences were saved, you might want to apply changes here
            # For example, update canvas settings, colors, etc.
            self._apply_preference_changes()

    def _apply_preference_changes(self):
        """Apply preference changes to the current session."""

    def _confirm_discard_changes(self):
        """Ask user to confirm discarding unsaved changes."""
        if not self.document.is_modified():
            return True

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "The document has been modified. Do you want to save your changes?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )

        if reply == QMessageBox.StandardButton.Save:
            self.save_file()
            return not self.document.is_modified()  # Return False if save failed
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:  # Cancel
            return False

    def _on_undo_state_changed(self):
        """Called when undo/redo state changes to update menu items."""
        if hasattr(self, 'main_menu'):
            # Update undo menu item
            can_undo = self.undo_manager.can_undo()
            undo_desc = self.undo_manager.get_undo_description()
            undo_text = f"Undo {undo_desc}" if undo_desc else "Undo"

            # Update redo menu item
            can_redo = self.undo_manager.can_redo()
            redo_desc = self.undo_manager.get_redo_description()
            redo_text = f"Redo {redo_desc}" if redo_desc else "Redo"

            # Update menu items (if the menu supports it)
            if hasattr(self.main_menu, 'update_undo_redo_state'):
                self.main_menu.update_undo_redo_state(
                    can_undo, undo_text, can_redo, redo_text)

    def execute_command(self, command):
        """Execute a command through the undo system."""
        if hasattr(self, 'undo_manager'):
            result = self.undo_manager.execute_command(command)
            if result:
                self.update_title()   # Update window title
            return result
        else:
            # Fallback: execute directly if no undo manager
            return command.execute()

    def closeEvent(self, event):
        """Handle window close event."""
        # Save window geometry to preferences
        geometry = self.geometry()
        self.preferences.set("window_geometry",
                           f"{geometry.width()}x{geometry.height()}+"
                           f"{geometry.x()}+{geometry.y()}")
        
        # Save preferences
        self.preferences.save()
        
        # Call parent's closeEvent
        super().closeEvent(event)

    # Palette visibility handlers
    def toggle_info_panel(self, show):
        """Handle Info Panel visibility toggle."""
        self.preferences.set("show_info_panel", show)
        self.palette_manager.set_palette_visibility("info_pane", show)
        self._sync_palette_menu_states()

    def toggle_properties(self, show):
        """Handle Properties panel visibility toggle."""
        self.preferences.set("show_properties", show)
        self.palette_manager.set_palette_visibility("config_pane", show)
        self._sync_palette_menu_states()

    def toggle_layers(self, show):
        """Handle Layers panel visibility toggle."""
        self.preferences.set("show_layers", show)
        self.palette_manager.set_palette_visibility("layer_pane", show)
        self._sync_palette_menu_states()

    def toggle_snap_settings(self, show):
        """Handle Snaps panel visibility toggle."""
        self.preferences.set("show_snap_settings", show)
        self.palette_manager.set_palette_visibility("snaps_pane", show)
        self._sync_palette_menu_states()

    def _sync_palette_menu_states(self):
        """Sync the palette menu checkbox states with actual visibility."""
        self.main_menu.sync_palette_menu_states(self.palette_manager)

    def _on_palette_visibility_changed(self, palette_id: str, visible: bool):
        """Handle palette visibility changes from the palette system."""
        # Update the preference for the palette
        if palette_id == "info_pane":
            self.preferences.set("show_info_panel", visible)
        elif palette_id == "config_pane":
            self.preferences.set("show_properties", visible)
        elif palette_id == "layer_pane":
            self.preferences.set("show_layers", visible)
        elif palette_id == "snaps_pane":
            self.preferences.set("show_snap_settings", visible)

        # Sync the menu checkboxes with the new state
        self._sync_palette_menu_states()




    def tool_table(self):
        """Handle Tool Table menu action."""
        logger.info("Opening tool table dialog")
        dialog = ToolTableDialog.load_from_preferences(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            logger.info("Tool table dialog accepted")
            # Preferences are saved in the dialog's accept() method
        else:
            logger.info("Tool table dialog cancelled")

    def _mouse_move_event(self, event):
        """Handle mouse move events to update position label."""
        # Get mouse position in scene coordinates
        pos = self.cad_view.mapToScene(event.position().toPoint())
        label = self.grid_info.unit_label
        if label == "Inch":
            label = '"'
        elif label == "Foot":
            label = ""
        elif label == "Yard":
            label = ""
        cursor_x = self.grid_info.format_label(pos.x(), no_subs=True)
        cursor_y = self.grid_info.format_label(pos.y(), no_subs=True)
        cursor_x = cursor_x.replace("\n", " ")
        cursor_y = cursor_y.replace("\n", " ")
        self.position_label_x.setText(f"X: {cursor_x}{label}")
        self.position_label_y.setText(f"Y: {cursor_y}{label}")
        # Call original mouse move event
        QGraphicsView.mouseMoveEvent(self.cad_view, event)

    def _zoom_in(self):
        """Zoom in."""
        zoom = GridInfo.zoom_adjust(self.cad_view, increase=True)
        self.zoom_edit_widget.set_zoom_value(zoom)

    def _zoom_out(self):
        """Zoom out."""
        zoom = GridInfo.zoom_adjust(self.cad_view, increase=False)
        self.zoom_edit_widget.set_zoom_value(zoom)

    def _reset_zoom(self):
        """Reset zoom to fit view."""
        zoom = GridInfo.set_zoom(self.cad_view, 100)
        self.cad_view.centerOn(0, 0)
        self.zoom_edit_widget.set_zoom_value(zoom)

    def _zoom_to_fit(self):
        """Zoom and center to fit all scene items (excluding grid and rulers)."""
        # Get all items except GridBackground and RulersForeground
        scene_items = [
            item for item in self.cad_scene.items()
            if not isinstance(item, (GridBackground, RulersForeground))
        ]
        
        if not scene_items:
            # No items to fit, just reset to 100% zoom at origin
            self._reset_zoom()
            return
        
        # Calculate bounding rect of all items
        bounding_rect = scene_items[0].sceneBoundingRect()
        for item in scene_items[1:]:
            bounding_rect = bounding_rect.united(item.sceneBoundingRect())
        
        # Add some padding around the items (5% of the bounding rect size)
        padding = max(bounding_rect.width(), bounding_rect.height()) * 0.05
        bounding_rect.adjust(-padding, -padding, padding, padding)
        bounding_rect.adjust(0, 0, 0, bounding_rect.height()*0.05)
        
        # Fit the view to the bounding rect
        self.cad_view.fitInView(bounding_rect, Qt.AspectRatioMode.KeepAspectRatio)
        
        # Update the zoom widget with the new zoom level
        zoom = GridInfo.get_zoom(self.cad_view)
        self.zoom_edit_widget.set_zoom_value(zoom)

    def _clear_selection(self):
        """Deselect all selected items."""
        self.cad_scene.clearSelection()

    def _select_all(self):
        """Select all selectable items (excluding grid and rulers)."""
        for item in self.cad_scene.items():
            if isinstance(item, CadItem):
                item.setSelected(True)

    def _select_similar(self):
        """Select similar items."""
        pass
