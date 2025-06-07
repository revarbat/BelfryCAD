# filepath: /Users/gminette/dev/git-repos/pyTkCAD/src/gui/main_window.py
"""Main window for the PyTkCAD application."""
import math
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFileDialog, QMessageBox, QGridLayout,
    QGraphicsScene, QGraphicsView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QPen, QColor

try:
    from PIL import Image
    import io
except ImportError:
    Image = None
    io = None

from BelfryCAD.tools import available_tools, ToolManager
from BelfryCAD.gui.category_button import CategoryToolButton
from BelfryCAD.gui.rulers import RulerManager
from BelfryCAD.gui.mainmenu import MainMenuBar
from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from .palette_system import create_default_palettes


class CADGraphicsView(QGraphicsView):
    """Custom graphics view for CAD drawing operations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Handle dragging ourselves
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        # Enable scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Enable mouse wheel scrolling
        self.setInteractive(True)

        # Enable mouse tracking to receive mouse move events
        # even when no buttons are pressed
        self.setMouseTracking(True)

        self.tool_manager = None  # Will be set by the main window
        self.drawing_manager = None  # Will be set by the main window

    def set_tool_manager(self, tool_manager):
        """Set the tool manager for handling events"""
        self.tool_manager = tool_manager

    def set_drawing_manager(self, drawing_manager):
        """Set the drawing manager for coordinate transformations"""
        self.drawing_manager = drawing_manager

    def wheelEvent(self, event):
        """Handle mouse wheel events for scrolling"""
        from PySide6.QtCore import Qt

        # Get wheel delta values
        delta = event.angleDelta()

        # Scroll speed multiplier
        scroll_speed = 30

        # Handle horizontal scrolling (Shift+wheel or horizontal wheel)
        if (
            event.modifiers() & Qt.KeyboardModifier.ShiftModifier or
            delta.x() != 0
        ):
            # Horizontal scrolling
            scroll_amount = delta.y() if delta.x() == 0 else delta.x()
            # Normalize wheel delta
            scroll_amount = int(scroll_amount / 120 * scroll_speed)

            # Use the view's built-in scrolling methods
            h_bar = self.horizontalScrollBar()
            new_value = h_bar.value() - scroll_amount
            h_bar.setValue(new_value)

        else:
            # Vertical scrolling (normal wheel movement)
            # Normalize wheel delta
            scroll_amount = int(delta.y() / 120 * scroll_speed)

            # Use the view's built-in scrolling methods
            v_bar = self.verticalScrollBar()
            new_value = v_bar.value() - scroll_amount
            v_bar.setValue(new_value)

        # Accept the event to prevent it from being passed to parent
        event.accept()

    def mousePressEvent(self, event):
        """Handle mouse press events and forward to active tool"""
        if self.tool_manager and self.tool_manager.get_active_tool():
            # Convert to scene coordinates
            scene_pos = self.mapToScene(event.pos())

            # Convert Qt scene coordinates to CAD coordinates using
            # drawing manager
            if self.drawing_manager:
                # Use descale_coords to convert from Qt (Y-down) to CAD (Y-up)
                # coordinates
                cad_coords = self.drawing_manager.descale_coords(
                    [scene_pos.x(), scene_pos.y()])
                cad_x, cad_y = cad_coords[0], cad_coords[1]
            else:
                # Fallback to scene coordinates if no drawing manager
                cad_x, cad_y = scene_pos.x(), scene_pos.y()

            # Create a simple event object with CAD coordinates and x/y attrs
            class SceneEvent:
                def __init__(self, scene_pos, cad_x, cad_y):
                    self._scene_pos = scene_pos
                    self.x = cad_x  # Use CAD coordinates
                    self.y = cad_y  # Use CAD coordinates

                def scenePos(self):
                    return self._scene_pos

            scene_event = SceneEvent(scene_pos, cad_x, cad_y)
            self.tool_manager.get_active_tool().handle_mouse_down(scene_event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events and forward to active tool"""
        if self.tool_manager and self.tool_manager.get_active_tool():
            scene_pos = self.mapToScene(event.pos())

            # Convert Qt scene coordinates to CAD coordinates using
            # drawing manager
            if self.drawing_manager:
                # Use descale_coords to convert from Qt (Y-down) to CAD (Y-up)
                # coordinates
                cad_coords = self.drawing_manager.descale_coords(
                    [scene_pos.x(), scene_pos.y()])
                cad_x, cad_y = cad_coords[0], cad_coords[1]
            else:
                # Fallback to scene coordinates if no drawing manager
                cad_x, cad_y = scene_pos.x(), scene_pos.y()

            class SceneEvent:
                def __init__(self, scene_pos, cad_x, cad_y):
                    self._scene_pos = scene_pos
                    self.x = cad_x  # Use CAD coordinates
                    self.y = cad_y  # Use CAD coordinates

                def scenePos(self):
                    return self._scene_pos

            scene_event = SceneEvent(scene_pos, cad_x, cad_y)
            self.tool_manager.get_active_tool().handle_mouse_move(scene_event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events and forward to active tool"""
        if self.tool_manager and self.tool_manager.get_active_tool():
            scene_pos = self.mapToScene(event.pos())

            # Convert Qt scene coordinates to CAD coordinates using
            # drawing manager
            if self.drawing_manager:
                # Use descale_coords to convert from Qt (Y-down) to CAD (Y-up)
                # coordinates
                cad_coords = self.drawing_manager.descale_coords(
                    [scene_pos.x(), scene_pos.y()])
                cad_x, cad_y = cad_coords[0], cad_coords[1]
            else:
                # Fallback to scene coordinates if no drawing manager
                cad_x, cad_y = scene_pos.x(), scene_pos.y()

            class SceneEvent:
                def __init__(self, scene_pos, cad_x, cad_y):
                    self._scene_pos = scene_pos
                    self.x = cad_x  # Use CAD coordinates
                    self.y = cad_y  # Use CAD coordinates

                def scenePos(self):
                    return self._scene_pos

            scene_event = SceneEvent(scene_pos, cad_x, cad_y)
            # Check if tool has handle_mouse_up method (selector tool has it)
            active_tool = self.tool_manager.get_active_tool()
            if hasattr(active_tool, 'handle_mouse_up'):
                active_tool.handle_mouse_up(scene_event)
            elif hasattr(active_tool, 'handle_drag'):
                active_tool.handle_drag(scene_event)
        else:
            super().mouseReleaseEvent(event)


class MainWindow(QMainWindow):
    def __init__(self, config, preferences, document):
        super().__init__()
        self.config = config
        self.preferences = preferences
        self.document = document

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

    def _setup_category_shortcuts(self):
        """Set up keyboard shortcuts for tool category activation"""
        from PySide6.QtGui import QShortcut, QKeySequence
        from BelfryCAD.tools.base import ToolCategory

        # Define key mappings for tool categories
        self.category_key_mappings = {
            'Space': ToolCategory.SELECTOR,  # Spacebar for Selector
            'N': ToolCategory.NODES,         # N for Nodes
            'L': ToolCategory.LINES,         # L for Lines
            'A': ToolCategory.ARCS,          # A for Arcs
            'E': ToolCategory.ELLIPSES,      # E for Ellipses
            'P': ToolCategory.POLYGONS,      # P for Polygons
            'T': ToolCategory.TEXT,          # T for Text
            'I': ToolCategory.IMAGES,        # I for Images
            'D': ToolCategory.DIMENSIONS,    # D for Dimensions
            'F': ToolCategory.TRANSFORMS,    # F for transForm
            'Y': ToolCategory.LAYOUT,        # LaYout
            'U': ToolCategory.DUPLICATORS,   # dUplicators
            'O': ToolCategory.POINTS,        # pOints
            'H': ToolCategory.SCREWHOLES,    # H for screw Holes
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
        self.main_menu.select_all_triggered.connect(self.select_all)
        self.main_menu.select_similar_triggered.connect(self.select_similar)
        self.main_menu.deselect_all_triggered.connect(self.deselect_all)
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
        self.main_menu.convert_to_lines_triggered.connect(
            self.convert_to_lines)
        self.main_menu.convert_to_curves_triggered.connect(
            self.convert_to_curves)
        self.main_menu.simplify_curves_triggered.connect(
            self.simplify_curves)
        self.main_menu.smooth_curves_triggered.connect(
            self.smooth_curves)
        self.main_menu.join_curves_triggered.connect(
            self.join_curves)
        self.main_menu.vectorize_bitmap_triggered.connect(
            self.vectorize_bitmap)

        # Boolean operations connections
        self.main_menu.union_polygons_triggered.connect(
            self.union_polygons)
        self.main_menu.difference_polygons_triggered.connect(
            self.difference_polygons)
        self.main_menu.intersection_polygons_triggered.connect(
            self.intersection_polygons)

        # View menu connections
        self.main_menu.redraw_triggered.connect(self.redraw)
        self.main_menu.actual_size_triggered.connect(self.actual_size)
        self.main_menu.zoom_to_fit_triggered.connect(self.zoom_to_fit)
        self.main_menu.zoom_in_triggered.connect(self.zoom_in)
        self.main_menu.zoom_out_triggered.connect(self.zoom_out)
        self.main_menu.show_origin_toggled.connect(self.toggle_show_origin)
        self.main_menu.show_grid_toggled.connect(self.toggle_show_grid)

        # Palette visibility connections
        self.main_menu.show_info_panel_toggled.connect(self.toggle_info_panel)
        self.main_menu.show_properties_toggled.connect(self.toggle_properties)
        self.main_menu.show_snap_settings_toggled.connect(
            self.toggle_snap_settings)
        self.main_menu.show_layers_toggled.connect(self.toggle_layers)

        # CAM menu connections
        self.main_menu.configure_mill_triggered.connect(
            self.configure_mill)
        self.main_menu.speeds_feeds_wizard_triggered.connect(
            self.speeds_feeds_wizard)
        self.main_menu.generate_gcode_triggered.connect(
            self.generate_gcode)
        self.main_menu.backtrace_gcode_triggered.connect(
            self.backtrace_gcode)
        self.main_menu.make_worm_triggered.connect(self.make_worm)
        self.main_menu.make_worm_gear_triggered.connect(
            self.make_worm_gear)
        self.main_menu.make_gear_triggered.connect(self.make_gear)

        # Window menu connections
        self.main_menu.minimize_triggered.connect(self.showMinimized)
        self.main_menu.cycle_windows_triggered.connect(
            self.cycle_windows)

    def _create_toolbar(self):
        """Create a toolbar with drawing tools"""
        from PySide6.QtCore import Qt, QSize
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
                spacing: 2px 0 2px 0;
                border: none;
            }
            QToolButton {
                margin: 0px;
                padding: 0px;
                border: none;
            }
        """)
        # We'll populate this with category buttons in _setup_tools()

        # Store category buttons for reference
        self.category_buttons = {}

    def _create_canvas(self):
        # Create central widget and grid layout for rulers and canvas
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)

        # Remove all spacing around the grid
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create graphics view and scene
        self.scene = QGraphicsScene()
        # Set a large scene rectangle to enable scrolling
        # This creates a virtual canvas much larger than the visible area
        self.scene.setSceneRect(-5000, -5000, 10000, 10000)

        self.canvas = CADGraphicsView()
        self.canvas.setScene(self.scene)

        # Initialize DrawingManager for object drawing
        drawing_context = DrawingContext(
            scene=self.scene,
            dpi=72.0,
            scale_factor=1.0,
            show_grid=True,
            show_origin=True
        )
        self.drawing_manager = DrawingManager(drawing_context)

        # Connect DrawingManager to Document's LayerManager
        if hasattr(self.document, 'layers'):
            self.drawing_manager.set_layer_manager(self.document.layers)

        # Create ruler manager and get ruler widgets
        self.ruler_manager = RulerManager(self.canvas, central_widget)
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        vertical_ruler = self.ruler_manager.get_vertical_ruler()

        # Create a spacer widget for the top-left corner
        corner_widget = QWidget()
        corner_widget.setFixedSize(32, 32)  # Match ruler width
        corner_widget.setStyleSheet(
            "background-color: white; border: 1px solid black;"
        )

        # Set up grid layout:
        # [corner] [horizontal_ruler]
        # [vertical_ruler] [canvas]
        layout.addWidget(corner_widget, 0, 0)
        layout.addWidget(horizontal_ruler, 0, 1)
        layout.addWidget(vertical_ruler, 1, 0)
        layout.addWidget(self.canvas, 1, 1)

        # Set column and row stretch so canvas takes remaining space
        layout.setColumnStretch(1, 1)  # Canvas column stretches
        layout.setRowStretch(1, 1)     # Canvas row stretches

        # Add axis lines at X=0 and Y=0
        self._add_axis_lines()

        # Add grid lines that align with ruler major tickmarks
        self._add_grid_lines()

        # Remove any default margins/padding from the graphics view
        self.canvas.setContentsMargins(0, 0, 0, 0)
        self.canvas.setStyleSheet("""
            QGraphicsView {
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """)

        # Connect canvas scroll and mouse events to rulers
        self._connect_ruler_events()

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
        # Connect info pane to canvas for position updates
        info_pane = self.palette_manager.get_palette_content("info_pane")
        if info_pane and hasattr(self, 'canvas'):
            # TODO: Connect canvas mouse move events to info pane updates
            pass

        # Connect config pane to document and selection
        config_pane = self.palette_manager.get_palette_content("config_pane")
        if config_pane and hasattr(self, 'document'):
            # Connect the config pane to selection changes
            self._connect_config_pane(config_pane)

        # Connect layer window to document layer management
        layer_window = self.palette_manager.get_palette_content(
            "layer_window")
        if (layer_window and hasattr(self, 'document') and
                hasattr(self.document, 'layers')):
            self._connect_layer_window(layer_window)

    def _connect_layer_window(self, layer_window):
        """Connect the layer window to the document's layer manager."""
        # Connect layer window signals to document layer manager
        layer_window.layer_created.connect(self._on_layer_created)
        layer_window.layer_deleted.connect(self._on_layer_deleted)
        layer_window.layer_selected.connect(self._on_layer_selected)
        layer_window.layer_renamed.connect(self._on_layer_renamed)
        layer_window.layer_visibility_changed.connect(
            self._on_layer_visibility_changed)
        layer_window.layer_lock_changed.connect(self._on_layer_lock_changed)
        layer_window.layer_color_changed.connect(self._on_layer_color_changed)
        layer_window.layer_cam_changed.connect(self._on_layer_cam_changed)
        layer_window.layer_reordered.connect(self._on_layer_reordered)

        # Initialize layer window with current layer data
        self._refresh_layer_window()

    def _refresh_layer_window(self):
        """Refresh the layer window with current layer data."""
        layer_window = self.palette_manager.get_palette_content(
            "layer_window")
        if not layer_window or not hasattr(self.document, 'layers'):
            return

        # Get all layer data from the layer manager
        layers_data = self.document.layers.get_all_layers_data()
        current_layer_id = str(self.document.layers.get_current_layer())

        # Update the layer window
        if hasattr(layer_window, 'refresh_layers'):
            refresh_method = getattr(layer_window, 'refresh_layers', None)
            if callable(refresh_method):
                refresh_method(layers_data, current_layer_id)

    def _on_layer_created(self):
        """Handle layer creation request from layer window."""
        if hasattr(self.document, 'layers'):
            new_layer_id = self.document.layers.create_layer()
            self.document.layers.set_current_layer(new_layer_id)
            self._refresh_layer_window()
            self.draw_objects()  # Redraw to update layer visibility

    def _on_layer_deleted(self, layer_id_str):
        """Handle layer deletion request from layer window."""
        if hasattr(self.document, 'layers'):
            layer_id = int(layer_id_str)
            if self.document.layers.delete_layer(layer_id):
                self._refresh_layer_window()
                self.draw_objects()  # Redraw to update layer visibility

    def _on_layer_selected(self, layer_id_str):
        """Handle layer selection from layer window."""
        if hasattr(self.document, 'layers'):
            layer_id = int(layer_id_str)
            self.document.layers.set_current_layer(layer_id)
            self._refresh_layer_window()

    def _on_layer_renamed(self, layer_id_str, new_name):
        """Handle layer rename from layer window."""
        if hasattr(self.document, 'layers'):
            layer_id = int(layer_id_str)
            self.document.layers.set_layer_name(layer_id, new_name)
            self._refresh_layer_window()

    def _on_layer_visibility_changed(self, layer_id_str, visible):
        """Handle layer visibility change from layer window."""
        if hasattr(self.document, 'layers'):
            layer_id = int(layer_id_str)
            self.document.layers.set_layer_visible(layer_id, visible)
            self.draw_objects()  # Redraw to update layer visibility

    def _on_layer_lock_changed(self, layer_id_str, locked):
        """Handle layer lock change from layer window."""
        if hasattr(self.document, 'layers'):
            layer_id = int(layer_id_str)
            self.document.layers.set_layer_locked(layer_id, locked)

    def _on_layer_color_changed(self, layer_id_str, color):
        """Handle layer color change from layer window."""
        if hasattr(self.document, 'layers'):
            layer_id = int(layer_id_str)
            self.document.layers.set_layer_color(layer_id, color)
            self.draw_objects()  # Redraw with new color

    def _on_layer_cam_changed(self, layer_id_str, cut_bit, cut_depth):
        """Handle layer CAM settings change from layer window."""
        if hasattr(self.document, 'layers'):
            layer_id = int(layer_id_str)
            self.document.layers.set_layer_cut_bit(layer_id, cut_bit)
            self.document.layers.set_layer_cut_depth(layer_id, cut_depth)

    def _on_layer_reordered(self, layer_id_str, new_position):
        """Handle layer reorder from layer window."""
        if hasattr(self.document, 'layers'):
            layer_id = int(layer_id_str)
            self.document.layers.reorder_layer(layer_id, new_position)
            self._refresh_layer_window()

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

        # Redraw objects to show changes
        self.draw_objects()

    def _setup_tools(self):
        """Set up the tool system and register tools"""
        # Initialize tool manager
        self.tool_manager = ToolManager(
            self.scene, self.document, self.preferences)

        # Connect tool manager to graphics view
        self.canvas.set_tool_manager(self.tool_manager)

        # Connect drawing manager to graphics view for coordinate
        # transformations
        self.canvas.set_drawing_manager(self.drawing_manager)

        # Register all available tools and group by category
        self.tools = {}
        tools_by_category = {}

        for tool_class in available_tools:
            tool = self.tool_manager.register_tool(tool_class)
            self.tools[tool.definition.token] = tool
            # Connect tool signals to redraw
            tool.object_created.connect(self.on_object_created)

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
                self._load_tool_icon,
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
        # Clear the scene but keep axis lines
        self.scene.clear()
        self._add_axis_lines()
        self.draw_objects()

    def open_file(self):
        if self.document.is_modified():
            if not self._confirm_discard_changes():
                return
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Document",
            "",
            "TkCAD files (*.tkcad);;SVG files (*.svg);;"
            "DXF files (*.dxf);;All files (*.*)"
        )
        if filename:
            try:
                self.document.load(filename)
                self.update_title()
                self.scene.clear()
                self.draw_objects()
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
                "TkCAD files (*.tkcad);;SVG files (*.svg);;"
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
            "TkCAD files (*.tkcad);;SVG files (*.svg);;"
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
        self.scene.clear()
        self._add_axis_lines()
        self._add_grid_lines()
        self.draw_objects()
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
            "SVG files (*.svg);;DXF files (*.dxf);;"
            "PDF files (*.pdf);;All files (*.*)"
        )
        if filename:
            try:
                # TODO: Implement export functionality
                QMessageBox.information(
                    self, "Export",
                    f"Export functionality not yet implemented for {filename}"
                )
            except Exception as e:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Export Error")
                msg.setText(f"Failed to export file:\n{e}")
                msg.exec()

    def page_setup(self):
        """Handle Page Setup menu action."""
        QMessageBox.information(
            self, "Page Setup",
            "Page setup functionality not yet implemented"
        )

    def print_file(self):
        """Handle Print menu action."""
        QMessageBox.information(
            self, "Print",
            "Print functionality not yet implemented"
        )

    # Edit menu handlers
    def undo(self):
        """Handle Undo menu action."""
        # TODO: Implement undo functionality
        QMessageBox.information(
            self, "Undo",
            "Undo functionality not yet implemented"
        )

    def redo(self):
        """Handle Redo menu action."""
        # TODO: Implement redo functionality
        QMessageBox.information(
            self, "Redo",
            "Redo functionality not yet implemented"
        )

    def cut(self):
        """Handle Cut menu action."""
        # TODO: Implement cut functionality
        QMessageBox.information(
            self, "Cut",
            "Cut functionality not yet implemented"
        )

    def copy(self):
        """Handle Copy menu action."""
        # TODO: Implement copy functionality
        QMessageBox.information(
            self, "Copy",
            "Copy functionality not yet implemented"
        )

    def paste(self):
        """Handle Paste menu action."""
        # TODO: Implement paste functionality
        QMessageBox.information(
            self, "Paste",
            "Paste functionality not yet implemented"
        )

    def clear(self):
        """Handle Clear menu action."""
        # TODO: Implement clear functionality
        QMessageBox.information(
            self, "Clear",
            "Clear functionality not yet implemented"
        )

    def select_all(self):
        """Handle Select All menu action."""
        # TODO: Implement select all functionality
        QMessageBox.information(
            self, "Select All",
            "Select All functionality not yet implemented"
        )

    def select_similar(self):
        """Handle Select Similar menu action."""
        # TODO: Implement select similar functionality
        QMessageBox.information(
            self, "Select Similar",
            "Select Similar functionality not yet implemented"
        )

    def deselect_all(self):
        """Handle Deselect All menu action."""
        # TODO: Implement deselect all functionality
        QMessageBox.information(
            self, "Deselect All",
            "Deselect All functionality not yet implemented"
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

    # View menu handlers
    def redraw(self):
        """Handle Redraw menu action."""
        self.draw_objects()
        self._update_rulers_and_grid()

    def actual_size(self):
        """Handle Actual Size menu action."""
        # TODO: Implement actual size functionality
        QMessageBox.information(
            self, "Actual Size",
            "Actual Size functionality not yet implemented"
        )

    def zoom_to_fit(self):
        """Handle Zoom to Fit menu action."""
        # TODO: Implement zoom to fit functionality
        QMessageBox.information(
            self, "Zoom to Fit",
            "Zoom to Fit functionality not yet implemented"
        )

    def zoom_in(self):
        """Handle Zoom In menu action."""
        # TODO: Implement zoom in functionality
        QMessageBox.information(
            self, "Zoom In",
            "Zoom In functionality not yet implemented"
        )

    def zoom_out(self):
        """Handle Zoom Out menu action."""
        # TODO: Implement zoom out functionality
        QMessageBox.information(
            self, "Zoom Out",
            "Zoom Out functionality not yet implemented"
        )

    def toggle_show_origin(self, show):
        """Handle Show Origin toggle."""
        self.preferences.set("show_origin", show)
        # TODO: Actually toggle origin display
        self.redraw()

    def toggle_show_grid(self, show):
        """Handle Show Grid toggle."""
        self.preferences.set("show_grid", show)
        # TODO: Actually toggle grid display
        self.redraw()

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
        # TODO: Implement speeds & feeds wizard
        QMessageBox.information(
            self, "Speeds & Feeds Wizard",
            "Speeds & Feeds Wizard functionality not yet implemented"
        )

    def generate_gcode(self):
        """Handle Generate G-Code menu action."""
        # TODO: Implement G-code generation
        QMessageBox.information(
            self, "Generate G-Code",
            "G-Code generation functionality not yet implemented"
        )

    def backtrace_gcode(self):
        """Handle Backtrace G-Code menu action."""
        # TODO: Implement G-code backtracing
        QMessageBox.information(
            self, "Backtrace G-Code",
            "G-Code backtracing functionality not yet implemented"
        )

    def make_worm(self):
        """Handle Make a Worm menu action."""
        # TODO: Implement worm creation wizard
        QMessageBox.information(
            self, "Make a Worm",
            "Worm creation functionality not yet implemented"
        )

    def make_worm_gear(self):
        """Handle Make a WormGear menu action."""
        # TODO: Implement worm gear creation wizard
        QMessageBox.information(
            self, "Make a WormGear",
            "WormGear creation functionality not yet implemented"
        )

    def make_gear(self):
        """Handle Make a Gear menu action."""
        # TODO: Implement gear creation wizard
        QMessageBox.information(
            self, "Make a Gear",
            "Gear creation functionality not yet implemented"
        )

    # Window menu handlers
    def cycle_windows(self):
        """Handle Cycle Windows menu action."""
        # TODO: Implement window cycling
        QMessageBox.information(
            self, "Cycle Windows",
            "Window cycling functionality not yet implemented"
        )

    # Helper methods for canvas setup and drawing
    def _add_axis_lines(self):
        """Add X=0 and Y=0 axis lines to the scene."""
        from PySide6.QtGui import QPen, QColor
        from PySide6.QtCore import Qt

        # Get scene rectangle for full extent lines
        scene_rect = self.scene.sceneRect()

        # Create axis line pen (thin, dark gray)
        axis_pen = QPen(QColor(64, 64, 64), 1)
        axis_pen.setStyle(Qt.PenStyle.DashLine)

        # Add X-axis (horizontal line at Y=0)
        x_line = self.scene.addLine(
            scene_rect.left(), 0, scene_rect.right(), 0, axis_pen
        )
        x_line.setZValue(-100)  # Behind other objects

        # Add Y-axis (vertical line at X=0)
        y_line = self.scene.addLine(
            0, scene_rect.top(), 0, scene_rect.bottom(), axis_pen
        )
        y_line.setZValue(-100)  # Behind other objects

    def _add_grid_lines(self):
        """Add dotted grid lines that align with ruler major tickmarks"""
        # Skip if grid is not enabled
        if not self.preferences.get("show_grid", True):
            return

        # Get grid information from the ruler system
        horizontal_ruler = self.ruler_manager.get_horizontal_ruler()
        grid_info = horizontal_ruler.get_grid_info()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = grid_info

        # Calculate scale conversion (same as rulers)
        dpi = horizontal_ruler.get_dpi()  # 96.0
        scalefactor = horizontal_ruler.get_scale_factor()  # 1.0
        scalemult = dpi * scalefactor / conversion  # 96.0

        # Create a light gray dotted pen for grid lines
        grid_pen = QPen(QColor(200, 200, 200))  # Light gray
        grid_pen.setWidth(1)
        grid_pen.setStyle(Qt.PenStyle.DotLine)  # Dotted line style

        # Get the visible scene rectangle
        scene_rect = self.scene.sceneRect()

        # Convert scene coordinates to ruler coordinates for calculation
        x_start_ruler = scene_rect.left() / scalemult
        x_end_ruler = scene_rect.right() / scalemult
        y_start_ruler = scene_rect.top() / scalemult
        y_end_ruler = scene_rect.bottom() / scalemult

        # Draw vertical grid lines
        # Use EXACT same logic as horizontal ruler's _draw_horizontal_ruler
        x = math.floor(x_start_ruler / minorspacing + 1e-6) * minorspacing

        while x <= x_end_ruler:
            # Test if this position would be a major tick with label
            if abs(math.floor(x / labelspacing + 1e-6) -
                   x / labelspacing) < 1e-3:
                # Convert ruler coordinate back to scene coordinate
                x_scene = x * scalemult
                grid_line = self.scene.addLine(
                    x_scene, scene_rect.top(),
                    x_scene, scene_rect.bottom(),
                    grid_pen
                )
                # Put grid lines behind axis lines
                grid_line.setZValue(-1001)
            x += minorspacing  # Iterate by minorspacing (ruler logic)

        # Draw horizontal grid lines
        # Use EXACT same logic as vertical ruler's _draw_vertical_ruler
        y = math.floor(y_start_ruler / minorspacing + 1e-6) * minorspacing

        while y <= y_end_ruler:
            # Test if this position would be a major tick with label
            if abs(math.floor(y / labelspacing + 1e-6) -
                   y / labelspacing) < 1e-3:
                # Convert ruler coordinate back to scene coordinate
                y_scene = y * scalemult
                grid_line = self.scene.addLine(
                    scene_rect.left(), y_scene,
                    scene_rect.right(), y_scene,
                    grid_pen
                )
                # Put grid lines behind axis lines
                grid_line.setZValue(-1001)
            y += minorspacing  # Iterate by minorspacing (ruler logic)

    def _connect_ruler_events(self):
        """Connect canvas scroll and mouse events to rulers for updates."""
        # Connect scroll events to update rulers when viewport changes
        self.canvas.horizontalScrollBar().valueChanged.connect(
            self._update_rulers_and_grid
        )
        self.canvas.verticalScrollBar().valueChanged.connect(
            self._update_rulers_and_grid
        )

        # Override the canvas mouse move event to update ruler positions
        original_mouse_move = self.canvas.mouseMoveEvent

        def enhanced_mouse_move(event):
            # Call the original mouse move handler first
            original_mouse_move(event)

            # Update ruler mouse position indicators
            scene_pos = self.canvas.mapToScene(event.pos())
            self.ruler_manager.update_mouse_position(
                scene_pos.x(), scene_pos.y()
            )

        # Replace the mouse move event handler
        self.canvas.mouseMoveEvent = enhanced_mouse_move

        # Also connect scene changes to ruler updates
        self.scene.sceneRectChanged.connect(self._update_rulers_and_grid)

    def _update_rulers_and_grid(self):
        """Update both rulers and grid when the view changes."""
        if hasattr(self, 'ruler_manager') and self.ruler_manager:
            self.ruler_manager.update_rulers()
        # Redraw grid lines to match new view
        self._redraw_grid()

    def _redraw_grid(self):
        """Remove existing grid lines and redraw them."""
        # Check if scene is still valid
        if not self.scene or not hasattr(self.scene, 'items'):
            return

        try:
            # Remove existing grid lines (z-value -1001)
            items_to_remove = []
            for item in self.scene.items():
                if hasattr(item, 'zValue') and item.zValue() == -1001:
                    items_to_remove.append(item)

            for item in items_to_remove:
                try:
                    self.scene.removeItem(item)
                except RuntimeError:
                    # Item may have already been removed
                    pass

            # Add new grid lines
            self._add_grid_lines()
        except Exception as e:
            print(f"Error redrawing grid: {e}")

    def draw_objects(self):
        """Draw all objects from the document to the scene."""
        # Clear existing drawing objects (but keep grid and axes)
        items_to_remove = []
        for item in self.scene.items():
            # Keep axis lines and grid lines (they have negative Z values)
            if item.zValue() >= 0:
                items_to_remove.append(item)

        for item in items_to_remove:
            try:
                self.scene.removeItem(item)
            except RuntimeError:
                # Item may have already been removed
                pass

        # Draw objects from document
        if (
            hasattr(self.document, 'objects') and
            hasattr(self.document.objects, 'objects')
        ):
            # CADObjectManager stores objects in a dictionary
            for obj_id, obj in self.document.objects.objects.items():
                self._draw_object(obj)

    def _draw_object(self, obj):
        """Draw a single object to the scene."""
        obj_id = id(obj)

        # Remove any existing graphics items for this object
        if obj_id in self.graphics_items:
            for item in self.graphics_items[obj_id]:
                try:
                    if item.scene() == self.scene:
                        self.scene.removeItem(item)
                except RuntimeError:
                    # Item may have already been removed
                    pass
            del self.graphics_items[obj_id]

        graphics_items = []

        # Use the DrawingManager to draw objects with proper TCL
        # translation
        if hasattr(self, 'drawing_manager'):
            graphics_items = self.drawing_manager.object_draw(obj)
            # Store graphics items for this object if any were returned
            if graphics_items:
                self.graphics_items[obj_id] = graphics_items
        else:
            # Fallback to simple drawing if DrawingManager is not available
            graphics_items = self._draw_object_simple(obj)
            if graphics_items:
                self.graphics_items[obj_id] = graphics_items

        return graphics_items

    def on_object_created(self, obj):
        """Handle when a new object is created by a tool."""
        # Draw the new object
        self._draw_object(obj)

        # Mark document as modified
        if hasattr(self.document, 'set_modified'):
            self.document.set_modified(True)

        # Update window title
        self.update_title()

    def _confirm_discard_changes(self):
        """Show dialog to confirm discarding unsaved changes."""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self, "Unsaved Changes",
            "The document has been modified. "
            "Do you want to save your changes?",
            (QMessageBox.StandardButton.Save |
             QMessageBox.StandardButton.Discard |
             QMessageBox.StandardButton.Cancel),
            QMessageBox.StandardButton.Save
        )

        if reply == QMessageBox.StandardButton.Save:
            self.save_file()
            return True
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:  # Cancel
            return False

    def _load_tool_icon(self, icon_name):
        """Load an icon for a tool, preferring SVG over PNG"""
        if not icon_name:
            return None

        # Construct the path to the images directory
        import os
        from PySide6.QtGui import QIcon, QPixmap
        from PySide6.QtCore import Qt

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        images_dir = os.path.join(base_dir, 'images')

        # Try SVG first (from main images directory), then fall back to PNG
        svg_path = os.path.join(images_dir, f"{icon_name}.svg")
        png_path = os.path.join(images_dir, f"{icon_name}.png")

        # Prefer SVG if available
        if os.path.exists(svg_path):
            try:
                # Load SVG icon
                icon = QIcon(svg_path)
                if not icon.isNull():
                    return icon
            except Exception as e:
                print(f"Failed to load SVG icon {svg_path}: {e}")

        # Fall back to PNG if SVG not available or failed to load
        if os.path.exists(png_path):
            try:
                # Load PNG and scale to 150% size (48x48 from original 32x32)
                pixmap = QPixmap(png_path)
                if not pixmap.isNull():
                    # Scale PNG icons to 150% for better visibility
                    scaled_pixmap = pixmap.scaled(
                        48, 48,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    return QIcon(scaled_pixmap)
            except Exception as e:
                print(f"Failed to load PNG icon {png_path}: {e}")

        return None

    def closeEvent(self, event):
        """Handle window close event."""
        if self.document.is_modified():
            if not self._confirm_discard_changes():
                event.ignore()
                return

        # Save window geometry to preferences
        geometry = self.geometry()
        geometry_str = (f"{geometry.width()}x{geometry.height()}+"
                        f"{geometry.x()}+{geometry.y()}")
        self.preferences.set("window_geometry", geometry_str)

        event.accept()

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
        self.palette_manager.set_palette_visibility("layer_window", show)
        self._sync_palette_menu_states()

    def toggle_snap_settings(self, show):
        """Handle Snap Settings panel visibility toggle."""
        self.preferences.set("show_snap_settings", show)
        self.palette_manager.set_palette_visibility("snap_window", show)
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
        elif palette_id == "layer_window":
            self.preferences.set("show_layers", visible)
        elif palette_id == "snap_window":
            self.preferences.set("show_snap_settings", visible)

        # Sync the menu checkboxes with the new state
        self._sync_palette_menu_states()

    def _draw_object_simple(self, obj):
        """Fallback method for drawing objects without DrawingManager."""
        from PySide6.QtGui import QPen, QBrush, QColor
        from PySide6.QtCore import Qt
        from BelfryCAD.core.cad_objects import ObjectType

        # Skip invisible objects
        if not getattr(obj, 'visible', True):
            return []

        # Get color from attributes, default to black
        color_name = obj.attributes.get('color', 'black')
        if color_name == 'black':
            color = QColor(0, 0, 0)
        elif color_name == 'blue':
            color = QColor(0, 0, 255)
        elif color_name == 'red':
            color = QColor(255, 0, 0)
        elif color_name == 'green':
            color = QColor(0, 255, 0)
        else:
            color = QColor(0, 0, 0)

        # Get line width from attributes
        line_width = obj.attributes.get('linewidth', 2)
        pen = QPen(color, line_width)
        brush = QBrush(Qt.BrushStyle.NoBrush)

        graphics_items = []

        # Draw based on object type
        if obj.object_type == ObjectType.LINE:
            if len(obj.coords) >= 2:
                start = obj.coords[0]
                end = obj.coords[1]
                line = self.scene.addLine(start.x, start.y, end.x, end.y, pen)
                line.setZValue(1)
                graphics_items.append(line)

        elif obj.object_type == ObjectType.CIRCLE:
            if len(obj.coords) >= 1 and 'radius' in obj.attributes:
                center = obj.coords[0]
                radius = obj.attributes['radius']
                ellipse = self.scene.addEllipse(
                    center.x - radius, center.y - radius,
                    radius * 2, radius * 2, pen, brush
                )
                ellipse.setZValue(1)
                graphics_items.append(ellipse)

        elif obj.object_type == ObjectType.POINT:
            if len(obj.coords) >= 1:
                point = obj.coords[0]
                size = 3
                h_line = self.scene.addLine(
                    point.x - size, point.y, point.x + size, point.y, pen
                )
                h_line.setZValue(1)
                graphics_items.append(h_line)
                v_line = self.scene.addLine(
                    point.x, point.y - size, point.x, point.y + size, pen
                )
                v_line.setZValue(1)
                graphics_items.append(v_line)

        return graphics_items
