# filepath: /Users/gminette/dev/git-repos/pyBelfryCad/src/gui/document_window.py
"""Document window for the BelfryCad application."""

import logging
from tracemalloc import start
from typing import Set

from PySide6.QtCore import (
    Qt, QSize, QTimer
)
from PySide6.QtGui import (
    QShortcut, QKeySequence, QPen, QColor
)
from PySide6.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox, QDialog, QLabel, QGraphicsView,
    QDockWidget
)
from PySide6.QtCore import QPointF


from ..models.undo_redo import UndoRedoManager
from ..models.cad_object import CadObject
from ..tools.base import ToolCategory, ToolManager

from .mainmenu import MainMenuBar
from .grid_info import GridInfo, GridUnits
from .graphics_items.grid_graphics_items import (
    GridBackground, RulersForeground, SnapCursorItem
)
from .palette_system import create_default_palettes
from .widgets.category_button import CategoryToolButton
from .widgets.cad_scene import CadScene
from .widgets.cad_view import CadView
from .icon_manager import get_icon

from .print_manager import CadPrintManager
from .dialogs.feed_wizard import FeedWizardDialog
from .dialogs.tool_table_dialog import ToolTableDialog
from .views.preferences_dialog import PreferencesDialog
from .dialogs.gear_wizard_dialog import GearWizardDialog
from .dialogs.gcode_backtracer_dialog import GCodeBacktracerDialog
from .widgets.zoom_edit_widget import ZoomEditWidget
from .snaps_system import SnapsSystem
from .panes.config_pane import ConfigPane
from .widgets.columnar_toolbar import ColumnarToolbarWidget
from BelfryCAD.utils.cad_expression import CadExpression
from .panes.parameters_pane import ParametersPane
from .panes.object_tree_pane import ObjectTreePane
from BelfryCAD.utils.xml_serializer import (
    load_belfrycad_document, load_belfrycad_xml_document,
    save_belfrycad_document, save_belfrycad_xml_document
)

logger = logging.getLogger(__name__)


class DocumentWindow(QMainWindow):
    def __init__(self, config, preferences_viewmodel, document):
        super().__init__()
        self.cad_expression = CadExpression()
        self.config = config
        self.preferences_viewmodel = preferences_viewmodel
        self.document = document

        # Initialize undo/redo system
        self.undo_manager = UndoRedoManager(max_undo_levels=50)
        self.undo_manager.add_callback(self._on_undo_state_changed)

        # Initialize print system
        self.print_manager = None  # Will be initialized after scene creation

        # Track graphics items by object ID for updates/deletion
        self.graphics_items = {}  # object_id -> list of graphics items
        
        # Flag to prevent circular updates when programmatically updating tree selection
        self._updating_tree_programmatically = False
        
        # Flag to prevent circular updates when programmatically updating scene selection
        self._updating_scene_programmatically = False
        
        # Track previous tree selection for detecting deselections
        self._previous_tree_selection = set()
        
        # Initialize snaps system (will be set up after scene creation)
        self._snaps_system = None

        self._setup_ui()

    @property
    def snaps_system(self):
        return self._snaps_system
    
    @snaps_system.setter
    def snaps_system(self, value):
        self._snaps_system = value

    def _setup_ui(self):
        self.setWindowTitle(self.config.APP_NAME)

        # Set window size - check preferences first, then default to 1024x768
        saved_geometry = self.preferences_viewmodel.get("window_geometry", None)
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
        self._create_snaps_toolbar()  # Add snaps toolbar
        self._create_status_bar()  # Add status bar
        self._setup_palettes()  # Add palette system setup
        self._setup_tools()
        self._setup_category_shortcuts()
        self._update_shortcut_tooltips()
        self._draw_shapes()
        
        # Connect preference change signals
        self._connect_preference_signals()

    def _connect_preference_signals(self):
        """Connect preference change signals to their handlers."""
        # Connect grid visibility preference changes
        self.preferences_viewmodel.preference_changed.connect(self._on_preference_changed)
        # Connect preferences loaded signal
        self.preferences_viewmodel.preferences_loaded.connect(self._refresh_visibility_from_preferences)

    def _on_preference_changed(self, key: str, value):
        """Handle preference changes."""
        if key == "grid_visible" and hasattr(self, 'grid'):
            self.grid.setVisible(value)
        elif key == "show_rulers" and hasattr(self, 'rulers'):
            self.rulers.setVisible(value)
        elif key == "precision" and hasattr(self, 'grid_info'):
            # Update GridInfo precision and refresh grid display
            self.grid_info.decimal_places = value
            if hasattr(self, 'cad_scene'):
                self.cad_scene.set_precision(value)
                self.cad_scene.update_all_control_datums_precision(value)
            if hasattr(self, 'grid'):
                self.grid.update()  # Refresh grid display
            if hasattr(self, 'rulers'):
                self.rulers.update()  # Refresh rulers display
            
            # Update ConfigPanes precision
            if hasattr(self, 'palette_manager'):
                config_pane = self.palette_manager.get_palette_content("config_pane")
                if config_pane and isinstance(config_pane, ConfigPane):
                    config_pane.update_precision(value)

    def _refresh_visibility_from_preferences(self):
        """Refresh grid and rulers visibility from preferences after they are loaded."""
        if hasattr(self, 'grid'):
            show_grid = self.preferences_viewmodel.get("grid_visible", True)
            self.grid.setVisible(show_grid)
        
        if hasattr(self, 'rulers'):
            show_rulers = self.preferences_viewmodel.get("show_rulers", True)
            self.rulers.setVisible(show_rulers)

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
        self.main_menu = MainMenuBar(self, self.preferences_viewmodel)

        # Connect menu signals to handlers
        self._connect_menu_signals()

    def _connect_menu_signals(self):
        """Connect menu signals to their corresponding handlers."""
        # File menu connections
        self.main_menu.new_triggered.connect(self.new_file)
        self.main_menu.open_triggered.connect(self.open_file)
        self.main_menu.file_selected.connect(self.open_recent_file)
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
        self.main_menu.show_grid_toggled.connect(self.toggle_show_grid)
        self.main_menu.show_rulers_toggled.connect(self.toggle_show_rulers)

        # Palette visibility connections
        self.main_menu.show_properties_toggled.connect(self.toggle_properties)
        self.main_menu.show_snap_settings_toggled.connect(self.toggle_snap_settings)
        self.main_menu.show_tools_toggled.connect(self.toggle_tools)

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
        
        # Make the toolbar movable and allow it to be docked in different areas
        self.toolbar.setMovable(True)
        self.toolbar.setAllowedAreas(
            Qt.ToolBarArea.TopToolBarArea |
            Qt.ToolBarArea.BottomToolBarArea |
            Qt.ToolBarArea.LeftToolBarArea |
            Qt.ToolBarArea.RightToolBarArea
        )
        
        # Set the icon size to 48x48 for 150% size visibility
        self.toolbar.setIconSize(QSize(48, 48))
        # Set spacing between toolbar buttons to 2 pixels using stylesheet
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        # Make toolbar more compact
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        # Apply custom stylesheet with 2px spacing and 1px border
        self.toolbar.setStyleSheet("""
            QToolBar {
                margin: 0px;
                border: 1px solid #cccccc;
            }
            QToolButton {
                margin: 0px;
                padding: 0px;
                border: none;
            }
        """)
        
        # Create two-column widget for tools
        self.tools_widget = ColumnarToolbarWidget()
        self.toolbar.addWidget(self.tools_widget)
        
        # Store category buttons for reference
        self.category_buttons = {}
        
        # Connect toolbar area changes to update column layout
        self.toolbar.orientationChanged.connect(self._on_tools_toolbar_moved)
        # Also connect to visibility changes to catch dock area changes
        self.toolbar.visibilityChanged.connect(self._on_tools_toolbar_moved)
        
        # Restore toolbar visibility from preferences
        visible = self.preferences_viewmodel.get("show_tools", True)
        self.toolbar.setVisible(visible)

    def _create_snaps_toolbar(self):
        """Create a toolbar for snap settings"""
        from .panes.snaps_pane import create_snaps_toolbar
        
        self.snaps_toolbar = create_snaps_toolbar(self.cad_scene, None)
        
        # Make the toolbar movable and allow it to be docked in different areas
        self.snaps_toolbar.setMovable(True)
        self.snaps_toolbar.setAllowedAreas(
            Qt.ToolBarArea.TopToolBarArea |
            Qt.ToolBarArea.BottomToolBarArea |
            Qt.ToolBarArea.LeftToolBarArea |
            Qt.ToolBarArea.RightToolBarArea
        )
        
        # Add to left toolbar area by default, below the tools toolbar
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, self.snaps_toolbar)
        
        # Connect snap signals to the snaps system
        self.snaps_toolbar.snap_changed.connect(self._on_snap_changed)
        self.snaps_toolbar.all_snaps_changed.connect(self._on_all_snaps_changed)
        
        # Restore toolbar position from preferences
        self._restore_snaps_toolbar_position()
        
        # Connect toolbar area changes to save position
        self.snaps_toolbar.orientationChanged.connect(self._on_snaps_toolbar_moved)
        # Also connect to visibility changes to catch dock area changes
        self.snaps_toolbar.visibilityChanged.connect(self._on_snaps_toolbar_moved)

    def _on_snap_changed(self, snap_type: str, enabled: bool):
        """Handle individual snap type changes"""
        # The snaps system will automatically pick up changes from snaps_pane_info
        pass

    def _on_all_snaps_changed(self, enabled: bool):
        """Handle all snaps toggle changes"""
        # The snaps system will automatically pick up changes from snaps_pane_info
        pass

    def _restore_snaps_toolbar_position(self):
        """Restore snaps toolbar position from preferences."""
        toolbar_area = self.preferences_viewmodel.get("snaps_toolbar_area", "left")
        
        # Remove from current area
        self.removeToolBar(self.snaps_toolbar)
        
        # Add to preferred area
        area_map = {
            "top": Qt.ToolBarArea.TopToolBarArea,
            "bottom": Qt.ToolBarArea.BottomToolBarArea,
            "left": Qt.ToolBarArea.LeftToolBarArea,
            "right": Qt.ToolBarArea.RightToolBarArea,
        }
        
        qt_area = area_map.get(toolbar_area, Qt.ToolBarArea.LeftToolBarArea)
        self.addToolBar(qt_area, self.snaps_toolbar)
        
        # Restore visibility
        visible = self.preferences_viewmodel.get("snaps_toolbar_visible", True)
        self.snaps_toolbar.setVisible(visible)
        
        # Menu state will be synced after palette manager is created

    def _save_snaps_toolbar_position(self):
        """Save snaps toolbar position to preferences."""
        # Determine current area
        area = self.toolBarArea(self.snaps_toolbar)
        area_map = {
            Qt.ToolBarArea.TopToolBarArea: "top",
            Qt.ToolBarArea.BottomToolBarArea: "bottom",
            Qt.ToolBarArea.LeftToolBarArea: "left",
            Qt.ToolBarArea.RightToolBarArea: "right",
        }
        
        toolbar_area = area_map.get(area, "top")
        self.preferences_viewmodel.set("snaps_toolbar_area", toolbar_area)
        self.preferences_viewmodel.set("snaps_toolbar_visible", self.snaps_toolbar.isVisible())

    def _on_snaps_toolbar_moved(self, orientation):
        """Handle snaps toolbar movement."""
        # Use a timer to ensure the move is complete before checking dock area
        QTimer.singleShot(50, self._update_snaps_toolbar_columns)
        # Save the new position after a short delay to ensure the move is complete
        QTimer.singleShot(100, self._save_snaps_toolbar_position)

    def _update_snaps_toolbar_columns(self):
        """Update the snaps toolbar columns based on current dock area."""
        if hasattr(self, 'snaps_toolbar') and self.snaps_toolbar:
            area = self.toolBarArea(self.snaps_toolbar)
            if area in [Qt.ToolBarArea.LeftToolBarArea, Qt.ToolBarArea.RightToolBarArea]:
                # Left/right docks: use 2 columns for vertical layout
                self.snaps_toolbar.snaps_widget.set_max_columns(2)
            else:
                # Top/bottom docks: use many columns (999) for horizontal layout
                self.snaps_toolbar.snaps_widget.set_max_columns(999)

    def _on_tools_toolbar_moved(self, orientation):
        """Handle tools toolbar movement."""
        # Use a timer to ensure the move is complete before checking dock area
        QTimer.singleShot(50, self._update_tools_toolbar_columns)

    def _update_tools_toolbar_columns(self):
        """Update the tools toolbar columns based on current dock area."""
        if hasattr(self, 'toolbar') and self.toolbar:
            area = self.toolBarArea(self.toolbar)
            if area in [Qt.ToolBarArea.LeftToolBarArea, Qt.ToolBarArea.RightToolBarArea]:
                # Left/right docks: use 2 columns for vertical layout
                self.tools_widget.set_max_columns(2)
            else:
                # Top/bottom docks: use many columns (999) for horizontal layout
                self.tools_widget.set_max_columns(999)

    def _create_status_bar(self):
        """Create the status bar with position labels."""
        # Create status bar
        status_bar = self.statusBar()

        # Create position labels
        xlabel = QLabel('  X:')
        self.position_label_x = QLabel('0.000"')
        ylabel = QLabel('Y:')
        self.position_label_y = QLabel('0.000"')

        # Set minimum width for labels to prevent jumping
        self.position_label_x.setMinimumWidth(100)
        self.position_label_y.setMinimumWidth(100)

        xlabel.setStyleSheet("color: #cc0000; font-weight: bold; font-size: 16pt;")
        self.position_label_x.setStyleSheet("font-size: 16pt;")
        ylabel.setStyleSheet("color: #00aa00; font-weight: bold; font-size: 16pt;")
        self.position_label_y.setStyleSheet("font-size: 16pt;")

        # Add labels to status bar
        status_bar.addWidget(xlabel)
        status_bar.addWidget(self.position_label_x)
        status_bar.addWidget(ylabel)
        status_bar.addWidget(self.position_label_y)

        # Add stretch to push labels to the left
        status_bar.addWidget(QLabel(), 1)

        self.zoom_edit_widget = ZoomEditWidget(self.cad_view)
        status_bar.addWidget(self.zoom_edit_widget, 1)

    def get_scene(self):
        return self.cad_scene

    def get_view(self):
        return self.cad_view

    def _create_canvas(self):
        # Create the CAD scene component
        # Get precision from preferences
        precision = self.preferences_viewmodel.get("precision", 3)
        self.grid_info = GridInfo(GridUnits.INCHES_DECIMAL, decimal_places=precision)
        self.cad_scene = CadScene(self, precision=precision)
        self.cad_view = CadView(self.cad_scene)
        self.print_manager = CadPrintManager(
            self, self.cad_scene, self.document)
        self.cad_view.mouseMoveEvent = self._mouse_move_event

        # Track viewmodels by object id
        self._object_viewmodels = {}

        # Connect CAD scene selection changes to object tree synchronization
        self.cad_scene.scene_selection_changed.connect(self._on_scene_selection_changed)

        # Add grid background
        self.grid = GridBackground(self.grid_info)
        self.cad_scene.addItem(self.grid)
        
        # Set initial grid visibility based on preferences
        show_grid = self.preferences_viewmodel.get("grid_visible", True)
        self.grid.setVisible(show_grid)

        # Add rulers
        self.rulers = RulersForeground(self.grid_info)
        self.cad_scene.addItem(self.rulers)
        
        # Set initial rulers visibility based on preferences
        show_rulers = self.preferences_viewmodel.get("show_rulers", True)
        self.rulers.setVisible(show_rulers)

        self.snap_cursor = SnapCursorItem()
        self.cad_scene.addItem(self.snap_cursor)

        # Set the CAD scene as the central widget
        self.setCentralWidget(self.cad_view)
        
        # Initialize the snaps system
        self.snaps_system = SnapsSystem(self.cad_scene, self.grid_info)
        
        # Set the snaps system reference in the scene for control point dragging
        self.cad_scene.set_snaps_system(self.snaps_system)

    def _rebuild_scene_overlays(self):
        """Re-add grid, rulers, and snap cursor after a scene clear."""
        if not hasattr(self, 'cad_scene'):
            return
        # Grid
        self.grid = GridBackground(self.grid_info)
        self.cad_scene.addItem(self.grid)
        self.grid.setVisible(self.preferences_viewmodel.get("grid_visible", True))
        # Rulers
        self.rulers = RulersForeground(self.grid_info)
        self.cad_scene.addItem(self.rulers)
        self.rulers.setVisible(self.preferences_viewmodel.get("show_rulers", True))
        # Snap cursor
        self.snap_cursor = SnapCursorItem()
        self.cad_scene.addItem(self.snap_cursor)

    def load_belcad_file(self, filepath: str) -> bool:
        """
        Load a BelfryCAD document (.belcad or .belcadx), then create CadViewModels and their views in the scene.
        """
        try:
            # Determine file format by extension
            filepath_lower = filepath.lower()
            if filepath_lower.endswith('.belcadx'):
                # Load uncompressed XML format
                loaded = load_belfrycad_xml_document(filepath)
            elif filepath_lower.endswith('.belcad'):
                # Load compressed zip format
                loaded = load_belfrycad_document(filepath)
            else:
                # Try compressed format as default
                loaded = load_belfrycad_document(filepath)
                
            if not loaded:
                raise RuntimeError("Failed to load BelfryCAD document")
                
            # Replace current document reference
            self.document = loaded
            # Attach document CadExpression (parameters) into main window if available
            if hasattr(self.document, 'cad_expression'):
                self.cad_expression = self.document.cad_expression
            # Optionally solve constraints after load
            try:
                if hasattr(self.document, 'solve_constraints'):
                    self.document.solve_constraints()
            except Exception:
                logger.debug("Constraint solving after load failed or is not available.")
            # Update panes that depend on document
            if hasattr(self, 'object_tree_pane'):
                self.object_tree_pane.set_document(self.document)
            if hasattr(self, 'parameters_pane') and hasattr(self, 'cad_expression'):
                # Bind parameters pane to the document's CadExpression and refresh
                try:
                    if hasattr(self.document, 'cad_expression') and self.document.cad_expression is not None:
                        self.parameters_pane.cad_expression = self.document.cad_expression
                except Exception:
                    pass
                # Refresh parameter list from the new expression set
                self.parameters_pane.refresh()
            # Apply grid units and precision from document preferences before rebuilding overlays
            self._apply_grid_units_from_document()
            # Clear and rebuild scene overlays
            if hasattr(self, 'cad_scene'):
                self.cad_scene.clear()
                self._rebuild_scene_overlays()
            # Build viewmodels and views
            self._build_viewmodels_for_document()
            # Zoom to fit the loaded document
            self._zoom_to_fit()
            # Update title
            self.update_title()
            return True
        except Exception as e:
            logger.exception("Error loading .belcad file: %s", e)
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Open Error")
            msg.setText(f"Failed to open file:\n{e}")
            msg.exec()
            return False

    def _build_viewmodels_for_document(self):
        """Create a CadViewModel for each object and add its views to the scene."""
        if not hasattr(self, 'cad_scene'):
            return
        
        # Import the factory here to avoid circular imports
        from .viewmodels.cad_object_factory import CadObjectFactory
        
        # Create factory for viewmodels
        factory = CadObjectFactory(self)
        
        # Reset mapping
        self._object_viewmodels = {}
        
        # Create viewmodels for all objects in the document
        for obj in self.document.get_all_objects():
            if obj.visible:  # Only create graphics for visible objects
                viewmodel = factory.create_viewmodel(obj)
                if viewmodel:
                    self._object_viewmodels[obj.object_id] = viewmodel
                    # Add the graphics items to the scene
                    viewmodel.update_view(self.cad_scene)

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
        saved_layout = self.preferences_viewmodel.get("palette_layout", None)
        if saved_layout:
            self.palette_manager.restore_palette_layout(saved_layout)
        
        # Sync menu states after all components are created
        self._sync_palette_menu_states()

        # Create Object Tree pane
        object_tree_pane = ObjectTreePane()
        object_tree_dock = QDockWidget("Object Tree", self)
        object_tree_dock.setWidget(object_tree_pane)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, object_tree_dock)
        self.object_tree_pane = object_tree_pane
        self.object_tree_dock = object_tree_dock
        
        # Connect Object Tree pane to document
        if hasattr(self, 'document'):
            object_tree_pane.set_document(self.document)
            
        # Connect Object Tree signals
        object_tree_pane.selection_changed.connect(self._on_object_tree_selection_changed)
        object_tree_pane.visibility_changed.connect(self._on_object_tree_visibility_changed)
        object_tree_pane.color_changed.connect(self._on_object_tree_color_changed)
        object_tree_pane.name_changed.connect(self._on_object_tree_name_changed)

        # Create the Pane and ParametersPane as tabs
        parameters_pane = ParametersPane(self.document.cad_expression)
        parameters_dock = QDockWidget("Parameters", self)
        parameters_dock.setWidget(parameters_pane)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, parameters_dock)
        self.parameters_pane = parameters_pane
        self.parameters_dock = parameters_dock
        parameters_pane.parameter_changed.connect(self._on_parameters_changed)

    def _on_parameters_changed(self):
        # Refresh any widgets that depend on parameters (e.g., CadExpressionEdit completers)
        self.parameters_pane.refresh()

    def _connect_palette_content(self):
        """Connect palette content widgets to the main window functionality."""
        # Connect config pane to document and selection
        config_pane = self.palette_manager.get_palette_content("config_pane")
        if config_pane and hasattr(self, 'document'):
            # Connect the config pane to selection changes
            self._connect_config_pane(config_pane)

    def _connect_config_pane(self, config_pane):
        """Connect config pane to the selection system for property editing."""
        # Connect config pane field changes to property updates
        config_pane.field_changed.connect(self._on_property_changed)

        # Track current selection state
        self._current_selection = set()

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
        from ..tools import available_tools  # Local import to avoid circular import
        # Initialize tool manager
        self.tool_manager = ToolManager(
            self, self.document, self.preferences_viewmodel)

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

            # Add to two-column widget
            self.tools_widget.add_button(category_button)
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
        self.document.clear()
        self.update_title()
        self.cad_scene.clear()
        # Refresh graphics after creating new document
        self._draw_shapes()

    def open_file(self):
        if self.document.is_modified():
            if not self._confirm_discard_changes():
                return
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open Document",
            "",
            "BelfryCAD files (*.belcad *.belcadx);;BelfryCAD Compressed (*.belcad);;BelfryCAD XML (*.belcadx);;All files (*.*)"
        )
        if filename:
            # Delegate to .belcad loader which also builds viewmodels and views
            if self.load_belcad_file(filename):
                # Add to recent files after successful load
                self.main_menu.add_recent_file(filename)
                # Refresh graphics after loading document
                self._draw_shapes()

    def open_recent_file(self, filename: str):
        """Open a file from the recent files list."""
        if self.document.is_modified():
            if not self._confirm_discard_changes():
                return
        # Load the file directly without showing file dialog
        if self.load_belcad_file(filename):
            # Add to recent files after successful load (moves to front)
            self.main_menu.add_recent_file(filename)
            # Refresh graphics after loading document
            self._draw_shapes()

    def save_file(self):
        if not self.document.filename:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save Document",
                "",
                "BelfryCAD Compressed (*.belcad);;BelfryCAD XML (*.belcadx);;BelfryCad files (*.tkcad);;SVG files (*.svg);;"
                "DXF files (*.dxf);;All files (*.*)"
            )
            if not filename:
                return
            self.document.filename = filename
        try:
            if self._save_document_file(self.document.filename):
                # Add to recent files after successful save
                self.main_menu.add_recent_file(self.document.filename)
                self.update_title()
            else:
                raise Exception("Save operation failed")
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
            "BelfryCAD Compressed (*.belcad);;BelfryCAD XML (*.belcadx);;BelfryCad files (*.tkcad);;SVG files (*.svg);;"
            "DXF files (*.dxf);;All files (*.*)"
        )
        if filename:
            try:
                self.document.filename = filename
                if self._save_document_file(filename):
                    self.main_menu.add_recent_file(filename)
                    self.update_title()
                else:
                    raise Exception("Save operation failed")
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
        self.document.clear()  # Reset to new document
        self.cad_scene.clear()
        self.update_title()
        # Refresh graphics after closing document
        self._draw_shapes()

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
                    if hasattr(self, 'print_manager') and \
                            self.print_manager is not None:
                        success = self.print_manager.export_to_pdf(filename)
                        if success:
                            # Add to recent files after successful export
                            self.main_menu.add_recent_file(filename)
                        return success
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
        if hasattr(self, 'print_manager') and self.print_manager is not None:
            self.print_manager.show_page_setup_dialog()
        else:
            # Fallback message
            QMessageBox.information(
                self, "Page Setup",
                "Page setup functionality not available"
            )

    def print_file(self):
        """Handle Print menu action."""
        if hasattr(self, 'print_manager') and self.print_manager is not None:
            self.print_manager.show_print_dialog()
        else:
            # Fallback message
            QMessageBox.information(
                self, "Print",
                "Print functionality not available"
            )

    def export_pdf(self):
        """Export the current drawing to PDF."""
        if hasattr(self, 'print_manager') and self.print_manager is not None:
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
            self.update_title()  # Update window title

    def redo(self):
        """Handle Redo menu action."""
        if hasattr(self, 'undo_manager') and self.undo_manager.redo():
            self.update_title()  # Update window title

    def cut(self):
        """Handle Cut menu action."""
        # Copy selected objects to clipboard, then delete them
        if self.copy():
            self._delete_selected_items()

    def copy(self):
        """Handle Copy menu action."""
        selected_objects = self._get_selected_items()
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
                new_coords.append(QPointF(
                    coord['x'] + paste_offset_x,
                    coord['y'] + paste_offset_y
                ))

            # Create new object
            new_obj = CadObject(
                self.document,
                color = "black",
                line_width = None
            )

            # Add to document
            self.document.add_object(new_obj)
            new_objects.append(new_obj)

        # Select the newly pasted objects
        if new_objects:
            self._select_items(new_objects)
            
        # Refresh the object tree
        self.refresh_object_tree()

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

    def toggle_show_grid(self, show):
        """Handle Show Grid toggle."""
        self.preferences_viewmodel.set("grid_visible", show)
        # Actually toggle grid display
        if hasattr(self, 'grid'):
            self.grid.setVisible(show)

    def toggle_show_rulers(self, show):
        """Handle Show Rulers toggle."""
        self.preferences_viewmodel.set("show_rulers", show)
        # Actually toggle rulers display
        if hasattr(self, 'rulers'):
            self.rulers.setVisible(show)

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
        dialog = PreferencesDialog(self.preferences_viewmodel, self)
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
            # TODO: Implement update_undo_redo_state method in MainMenuBar
            pass

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
        self.preferences_viewmodel.set("window_geometry",
                                     f"{geometry.width()}x{geometry.height()}+"
                                     f"{geometry.x()}+{geometry.y()}")

        # Save snaps toolbar position
        if hasattr(self, 'snaps_toolbar'):
            self._save_snaps_toolbar_position()

        # Save preferences
        self.preferences_viewmodel.save_preferences()

        # Call parent's closeEvent
        super().closeEvent(event)

    # Palette visibility handlers
    def toggle_properties(self, show):
        """Handle Properties panel visibility toggle."""
        self.preferences_viewmodel.set("show_properties", show)
        self.palette_manager.set_palette_visibility("config_pane", show)
        self._sync_palette_menu_states()

    def toggle_snap_settings(self, show):
        """Toggle the snaps toolbar visibility."""
        if hasattr(self, 'snaps_toolbar'):
            self.snaps_toolbar.setVisible(show)
            # Save the visibility state to preferences
            self.preferences_viewmodel.set("snaps_toolbar_visible", show)
            self.preferences_viewmodel.set("show_snap_settings", show)
            # Sync menu state
            self._sync_snaps_toolbar_menu_state()

    def toggle_tools(self, show):
        """Toggle the tools toolbar visibility."""
        if hasattr(self, 'toolbar'):
            self.toolbar.setVisible(show)
            # Save the visibility state to preferences
            self.preferences_viewmodel.set("show_tools", show)



    def _sync_palette_menu_states(self):
        """Sync the palette menu checkbox states with actual visibility."""
        # Sync palette states if palette manager exists
        if hasattr(self, 'palette_manager'):
            self.main_menu.sync_palette_menu_states(self.palette_manager)
        
        # Sync snaps toolbar menu state
        if hasattr(self, 'snaps_toolbar') and hasattr(self.main_menu, 'show_snap_settings_action'):
            visible = self.snaps_toolbar.isVisible()
            if self.main_menu.show_snap_settings_action:
                self.main_menu.show_snap_settings_action.setChecked(visible)

    def _sync_snaps_toolbar_menu_state(self):
        """Sync the snaps toolbar menu checkbox state with actual toolbar visibility."""
        if hasattr(self, 'snaps_toolbar') and hasattr(self.main_menu, 'show_snap_settings_action'):
            visible = self.snaps_toolbar.isVisible()
            if self.main_menu.show_snap_settings_action:
                self.main_menu.show_snap_settings_action.setChecked(visible)

    def _on_palette_visibility_changed(self, palette_id: str, visible: bool):
        """Handle palette visibility changes from the palette system."""
        # Update the preference for the palette
        if palette_id == "config_pane":
            self.preferences_viewmodel.set("show_properties", visible)

        # Sync the menu checkboxes with the new state
        self._sync_palette_menu_states()

    def _on_object_tree_selection_changed(self, selected_object_ids: Set[str]):
        """Handle multiple object selection changes from the Object Tree pane."""
        # Skip if we're already updating the tree programmatically
        if self._updating_tree_programmatically:
            return
            
        # Detect deselected groups and remove their children too
        deselected_groups = self._get_deselected_groups(self._previous_tree_selection, selected_object_ids)
        adjusted_selection = self._remove_children_of_deselected_groups(selected_object_ids, deselected_groups)
        
        # Apply group auto-selection logic for tree selections too
        selection_with_groups = self._expand_selection_for_groups(adjusted_selection)
        
        # Use unified selection update method
        self._update_selection_state(selection_with_groups, "tree")
        
        # Update tree to show the complete selection (groups + children)
        if selection_with_groups != selected_object_ids:
            # Reset the tree's updating flag first, then set our programmatic flag
            if hasattr(self, 'object_tree_pane'):
                self.object_tree_pane.updating_selection = False
            
            self._updating_tree_programmatically = True
            try:
                self.update_object_tree_selection(selection_with_groups)
                # Update our tracking after the tree update
                self._previous_tree_selection = selection_with_groups.copy()
            finally:
                self._updating_tree_programmatically = False
        else:
            # Update tracking even if no tree update needed
            self._previous_tree_selection = selected_object_ids.copy()

    def _on_object_tree_visibility_changed(self, object_id: str, visible: bool):
        """Handle visibility changes from the Object Tree pane."""
        # Update graphics items visibility
        if object_id in self.graphics_items:
            for item in self.graphics_items[object_id]:
                item.setVisible(visible)
                
        # Update the scene
        if hasattr(self, 'cad_scene'):
            self.cad_scene.update()
            
    def _on_object_tree_color_changed(self, object_id: str, color: QColor):
        """Handle color changes from the Object Tree pane."""
        # Find the object in the document
        obj = self.document.get_object(object_id)
        if obj:
            # Update the object's color attribute
            obj.color = color.name()
            # Mark the object as modified
            self.document.modified = True
            # Update the config pane to reflect the new color
            self._update_config_pane_for_selection([obj])
            # Refresh the object tree
            self.refresh_object_tree()

    def _on_object_tree_name_changed(self, object_id: str, name: str):
        """Handle name changes from the Object Tree pane."""
        # Find the object in the document
        obj = self.document.get_object(object_id)
        if obj:
            # Update the object's name
            obj.name = name
            # Mark the document as modified
            self.document.modified = True
            # Refresh the object tree to show the updated name
            self.refresh_object_tree()
            
    def update_object_tree_selection(self, selected_object_ids: Set[str]):
        """Update the object tree selection to match given object IDs."""
        if hasattr(self, 'object_tree_pane'):
            self.object_tree_pane.set_selection_from_scene(selected_object_ids)

    def _on_scene_selection_changed(self, selected_object_ids: Set[str]):
        """Handle selection changes from the CAD scene and sync with object tree."""
        # Skip if we're already updating from tree to prevent circular updates
        if self._updating_tree_programmatically:
            return
            
        # Apply hierarchical selection logic
        expanded_selection = self._expand_selection_for_groups(selected_object_ids)
        
        # Use unified selection update method
        self._update_selection_state(expanded_selection, "scene")
        
        # Update our tracking after the selection update
        self._previous_tree_selection = expanded_selection.copy()

    def _expand_selection_for_groups(self, selected_object_ids: Set[str]) -> Set[str]:
        """If all children of a group are selected, add the group to the selection too."""
        from BelfryCAD.models.cad_objects.group_cad_object import GroupCadObject
        
        expanded = selected_object_ids.copy()
        
        # Find all groups in the document using the objects dictionary directly
        all_groups = []
        for obj_id, obj in self.document.objects.items():
            if isinstance(obj, GroupCadObject):
                all_groups.append((obj_id, obj))
        
        # Check each group to see if all its children are selected
        for group_id, group in all_groups:
            children = set(group.get_all_descendants())
            
            # If group has children and all children are selected
            if children and children.issubset(selected_object_ids):
                expanded.add(group_id)  # Add the group (keep children too)
        
        return expanded

    def _expand_selection_for_children(self, selected_object_ids: Set[str]) -> Set[str]:
        """For each selected group, add all its children to the selection."""
        from BelfryCAD.models.cad_objects.group_cad_object import GroupCadObject
        
        expanded = set()
        
        for object_id in selected_object_ids:
            obj = self.document.get_object(object_id)
            if isinstance(obj, GroupCadObject):
                # Add all descendants of the group
                descendants = obj.get_all_descendants()
                expanded.update(descendants)
                # NOTE: Don't add the group itself - groups don't have graphics items
            else:
                # Add the object itself (not a group)
                expanded.add(object_id)
        
        return expanded

    def _get_deselected_groups(self, previous_selection: Set[str], current_selection: Set[str]) -> Set[str]:
        """Find groups that were deselected (in previous but not in current)."""
        from BelfryCAD.models.cad_objects.group_cad_object import GroupCadObject
        
        deselected_items = previous_selection - current_selection
        deselected_groups = set()
        
        for item_id in deselected_items:
            obj = self.document.get_object(item_id)
            if isinstance(obj, GroupCadObject):
                deselected_groups.add(item_id)
        
        return deselected_groups

    def _remove_children_of_deselected_groups(self, current_selection: Set[str], deselected_groups: Set[str]) -> Set[str]:
        """Remove children of deselected groups from the current selection."""
        from BelfryCAD.models.cad_objects.group_cad_object import GroupCadObject
        
        adjusted_selection = current_selection.copy()
        
        for group_id in deselected_groups:
            group = self.document.get_object(group_id)
            if isinstance(group, GroupCadObject):
                children = set(group.get_all_descendants())
                adjusted_selection -= children
        
        return adjusted_selection

    def refresh_object_tree(self):
        """Refresh the Object Tree pane."""
        if hasattr(self, 'object_tree_pane'):
            self.object_tree_pane.refresh_tree()

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
        if hasattr(self, 'snaps_system') and self.snaps_system is not None:
            pos = self.snaps_system.get_snap_point(pos)
        if pos is not None:
            cursor_x = self.grid_info.format_label(pos.x(), no_subs=False)
            cursor_y = self.grid_info.format_label(pos.y(), no_subs=False)
            cursor_x = cursor_x.replace("\n", " ")
            cursor_y = cursor_y.replace("\n", " ")
            self.position_label_x.setText(f"{cursor_x}{label}")
            self.position_label_y.setText(f"{cursor_y}{label}")
            self.snap_cursor.setPos(pos)
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
        try:
            
            # First call Qt's clearSelection to clear the internal state
            self.cad_scene.clearSelection()
            
            # Then manually deselect all items to ensure proper cleanup
            all_items = self.cad_scene.items()
            for item in all_items:
                try:
                    if hasattr(item, 'setSelected') and hasattr(item, 'isSelected'):
                        if item.isSelected():
                            item.setSelected(False)
                except (RuntimeError, AttributeError, TypeError):
                    # Item may be invalid, continue with others
                    continue
            
        except (RuntimeError, AttributeError, TypeError) as e:
            # If clearing fails, just log the error and continue
            print(f"Warning: Failed to clear selection: {e}")
            pass

    def _select_all(self):
        """Select all selectable items (excluding grid and rulers)."""
        for item in self.cad_scene.items():
            # Check if this item has a viewmodel reference in data slot 0
            viewmodel = item.data(0)
            if viewmodel and hasattr(viewmodel, '_cad_object'):
                item.setSelected(True)

    def _get_selected_items(self):
        """Get currently selected items from the scene."""
        selected_items = []
        for item in self.cad_scene.selectedItems():
            # Check if this item has a viewmodel reference in data slot 0
            viewmodel = item.data(0)
            if viewmodel and hasattr(viewmodel, '_cad_object'):
                selected_items.append(item)
        return selected_items

    def _delete_selected_items(self):
        """Delete currently selected items from the scene."""
        selected_items = self._get_selected_items()
        for item in selected_items:
            self.cad_scene.removeItem(item)
        return len(selected_items) > 0

    def _select_items(self, items):
        """Select the specified items in the scene."""
        # First clear current selection
        self.cad_scene.clearSelection()
        # Then select the new items
        for item in items:
            if hasattr(item, 'setSelected'):
                item.setSelected(True)

    def _select_similar(self):
        """Select similar items."""
        pass

    def _draw_shapes(self):
        """Draw shapes on the canvas."""
        # Import the factory here to avoid circular imports
        from .viewmodels.cad_object_factory import CadObjectFactory
        
        # Create factory for viewmodels
        factory = CadObjectFactory(self)
        
        # Clear existing viewmodels if any
        if not hasattr(self, '_object_viewmodels'):
            self._object_viewmodels = {}
        else:
            # Clean up existing viewmodels
            for viewmodel in self._object_viewmodels.values():
                if hasattr(viewmodel, '_clear_view_items'):
                    viewmodel._clear_view_items(self.cad_scene)
            self._object_viewmodels.clear()
        
        # Create viewmodels for all objects in the document
        for obj in self.document.get_all_objects():
            if obj.visible:  # Only create graphics for visible objects
                viewmodel = factory.create_viewmodel(obj)
                if viewmodel:
                    self._object_viewmodels[obj.object_id] = viewmodel
                    # Add the graphics items to the scene
                    viewmodel.update_view(self.cad_scene)

    def tool_table(self):
        """Handle Tool Table menu action."""
        logger.info("Opening tool table dialog")
        dialog = ToolTableDialog.load_from_preferences(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            logger.info("Tool table dialog accepted")
            # Preferences are saved in the dialog's accept() method
        else:
            logger.info("Tool table dialog cancelled")

    def _apply_grid_units_from_document(self):
        """Set GridInfo units and precision from document preferences (units, use_fractions, precision)."""
        if not hasattr(self, 'grid_info'):
            return
        prefs = getattr(self.document, 'preferences', {}) if hasattr(self.document, 'preferences') else {}
        units = prefs.get('units')
        use_fractions = prefs.get('use_fractions')
        precision = prefs.get('precision')
        # Map document units + use_fractions to GridUnits
        unit_map = {
            ('inches', False): GridUnits.INCHES_DECIMAL,
            ('inches', True): GridUnits.INCHES_FRACTION,
            ('inch', False): GridUnits.INCHES_DECIMAL,
            ('inch', True): GridUnits.INCHES_FRACTION,
            ('feet', False): GridUnits.FEET_DECIMAL,
            ('feet', True): GridUnits.FEET_FRACTION,
            ('foot', False): GridUnits.FEET_DECIMAL,
            ('foot', True): GridUnits.FEET_FRACTION,
            ('yards', False): GridUnits.YARDS_DECIMAL,
            ('yards', True): GridUnits.YARDS_FRACTION,
            ('yard', False): GridUnits.YARDS_DECIMAL,
            ('yard', True): GridUnits.YARDS_FRACTION,
            ('mm', False): GridUnits.MILLIMETERS,
            ('millimeters', False): GridUnits.MILLIMETERS,
            ('cm', False): GridUnits.CENTIMETERS,
            ('centimeters', False): GridUnits.CENTIMETERS,
            ('m', False): GridUnits.METERS,
            ('meters', False): GridUnits.METERS,
        }
        if isinstance(units, str):
            key = (units.lower(), bool(use_fractions))
            grid_units = unit_map.get(key)
            if grid_units:
                self.grid_info.units = grid_units
        if isinstance(precision, int):
            self.grid_info.decimal_places = precision

    def _save_document_file(self, filepath: str) -> bool:
        """
        Save the document using the appropriate format based on file extension.
        
        Args:
            filepath: Path to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get preferences for saving
            preferences = {}
            if hasattr(self, 'preferences_viewmodel'):
                preferences = {
                    'units': self.preferences_viewmodel.get('units', 'mm'),
                    'precision': self.preferences_viewmodel.get('precision', 2),
                    'use_fractions': self.preferences_viewmodel.get('use_fractions', False),
                    'grid_visible': self.preferences_viewmodel.get('grid_visible', True),
                    'show_rulers': self.preferences_viewmodel.get('show_rulers', True),
                    'canvas_bg_color': self.preferences_viewmodel.get('canvas_bg_color', '#f0f0f0'),
                    'grid_color': self.preferences_viewmodel.get('grid_color', '#d0d0d0'),
                    'selection_color': self.preferences_viewmodel.get('selection_color', '#ff8000')
                }
            
            # Determine file format by extension
            filepath_lower = filepath.lower()
            if filepath_lower.endswith('.belcadx'):
                # Save as uncompressed XML format
                success = save_belfrycad_xml_document(self.document, filepath, preferences)
            elif filepath_lower.endswith('.belcad'):
                # Save as compressed zip format
                success = save_belfrycad_document(self.document, filepath, preferences)
            else:
                # Try to guess format from extension or default to compressed
                if filepath_lower.endswith('.xml'):
                    success = save_belfrycad_xml_document(self.document, filepath, preferences)
                else:
                    # Default to compressed format for unknown extensions
                    success = save_belfrycad_document(self.document, filepath, preferences)
            
            if success:
                self.document.mark_saved()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error saving document: {e}")
            return False

    def _update_decorations_for_selection_change(
            self,
            previous_selection: Set[str],
            current_selection: Set[str]
    ):
        """Update decorations when selection changes by calling show/hide on viewmodels."""
        # Objects that were deselected - hide their decorations
        deselected_objects = previous_selection - current_selection
        for obj_id in deselected_objects:
            if obj_id in self._object_viewmodels:
                viewmodel = self._object_viewmodels[obj_id]
                viewmodel.hide_decorations(self.cad_scene)
        
        # Objects that were newly selected - show their decorations  
        newly_selected_objects = current_selection - previous_selection
        for obj_id in newly_selected_objects:
            if obj_id in self._object_viewmodels:
                viewmodel = self._object_viewmodels[obj_id]
                viewmodel.show_decorations(self.cad_scene)

    def _update_controls_for_selection_change(
            self,
            previous_selection: Set[str],
            current_selection: Set[str]
    ):
        """
        Update control points and datums based on selection state.
        
        Rules:
        - When a CAD object becomes the only object selected: show_controls()
        - When a CAD object is deselected or more than one object becomes selected: hide_controls()
        - After show_controls(): update_controls()
        """
        # Hide controls for all previously selected objects
        for obj_id in previous_selection:
            if obj_id in self._object_viewmodels:
                viewmodel = self._object_viewmodels[obj_id]
                viewmodel.hide_controls(self.cad_scene)
        
        # Show controls only if exactly one object is selected
        if len(current_selection) == 1:
            obj_id = next(iter(current_selection))
            if obj_id in self._object_viewmodels:
                viewmodel = self._object_viewmodels[obj_id]
                viewmodel.show_controls(self.cad_scene)
                # Update controls immediately after showing them
                viewmodel.update_controls(self.cad_scene)

    def _update_selection_state(self, new_selection: Set[str], source: str = "unknown"):
        """
        Unified method to update selection state across all components.
        
        Args:
            new_selection: Set of object IDs representing the new selection
            source: String indicating the source of the selection change
        """
        # Skip if selection hasn't actually changed
        if new_selection == self._current_selection:
            return
            
        # Store previous selection for decoration updates
        previous_selection = self._current_selection.copy()
        
        # Update current selection
        self._current_selection = new_selection.copy()
        
        # Update decorations based on selection changes
        self._update_decorations_for_selection_change(previous_selection, new_selection)
        
        # Update control points and datums based on selection state
        self._update_controls_for_selection_change(previous_selection, new_selection)
        
        # Update config pane with selected objects
        selected_objects = []
        for obj_id in new_selection:
            obj = self.document.get_object(obj_id)
            if obj:
                selected_objects.append(obj)
        self._update_config_pane_for_selection(selected_objects)
        
        # Update other components based on source to prevent circular updates
        if source != "tree":
            # Update tree selection
            self._updating_tree_programmatically = True
            try:
                self.update_object_tree_selection(new_selection)
            finally:
                self._updating_tree_programmatically = False
                
        if source != "scene":
            # Update scene selection - expand to include children of groups
            expanded_selection = self._expand_selection_for_children(new_selection)
            self._updating_scene_programmatically = True
            self.cad_scene.set_updating_from_tree(True)
            try:
                self._clear_selection()
                for obj_id in expanded_selection:
                    obj = self.document.get_object(obj_id)
                    if obj and obj_id in self._object_viewmodels:
                        viewmodel = self._object_viewmodels[obj_id]
                        for item in self.cad_scene.items():
                            item_viewmodel = item.data(0)
                            if item_viewmodel == viewmodel:
                                item.setSelected(True)
                                break
            finally:
                self._updating_scene_programmatically = False
                self.cad_scene.set_updating_from_tree(False)

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
