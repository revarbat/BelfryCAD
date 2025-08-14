"""
Palette System for BelfryCAD

This module manages the dockable palette system, providing a flexible way to
organize and display various UI components in dockable panels.
"""

from typing import Dict, Optional, List, Any, TYPE_CHECKING
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget,
    QDockWidget, QApplication, QLabel, QMainWindow
)
from PySide6.QtCore import Qt, Signal, QPoint, QSize, QObject
from PySide6.QtGui import QAction

# Import the translated palette components
from .panes.info_pane import InfoPane
from .panes.config_pane import ConfigPane

if TYPE_CHECKING:
    from .document_window import DocumentWindow


class PaletteDockArea(Enum):
    """Defines which areas palettes can be docked to."""
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"
    FLOATING = "floating"


class PaletteType(Enum):
    """Supported palette types."""
    INFO_PANE = "info_pane"
    CONFIG_PANE = "config_pane"
    SNAPS_PANE = "snaps_pane"


class DockablePalette(QDockWidget):
    """
    A dockable palette that can be moved around the main window.
    """

    # Signals
    palette_moved = Signal(str, str)  # palette_id, new_dock_area
    palette_undocked = Signal(str)    # palette_id (became floating)
    palette_redocked = Signal(str, str)  # palette_id, dock_area
    palette_visibility_changed = Signal(str, bool)  # palette_id, visible

    def __init__(
            self,
            palette_id: str,
            title: str,
            content_widget: QWidget,
            parent=None
    ):
        super().__init__(title, parent)
        self.palette_id = palette_id
        self.content_widget = content_widget
        self._is_floating_by_user = False

        self._setup_ui()

    def _setup_ui(self):
        """Setup the dockable palette UI."""
        # Configure dock widget properties
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea |
            Qt.DockWidgetArea.BottomDockWidgetArea
        )

        # Enable floating
        self.setFloating(False)

        # Set features
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )

        # Set content widget
        self.setWidget(self.content_widget)

        # Connect signals
        self.dockLocationChanged.connect(self._on_dock_location_changed)
        self.topLevelChanged.connect(self._on_floating_changed)
        self.visibilityChanged.connect(self._on_visibility_changed)

        # Set minimum size for better UX
        self.setMinimumSize(220, 150)

    def _on_visibility_changed(self, visible: bool):
        """Handle visibility changes."""
        self.palette_visibility_changed.emit(self.palette_id, visible)

    def _on_dock_location_changed(self, area: Qt.DockWidgetArea):
        """Handle when the palette is moved to a new dock area."""
        # Determine which area we're docked to
        if self.parent():
            document_window = self.parent()
            if isinstance(document_window, QMainWindow):
                area = document_window.dockWidgetArea(self)
                area_map = {
                    Qt.DockWidgetArea.LeftDockWidgetArea:
                        PaletteDockArea.LEFT.value,
                    Qt.DockWidgetArea.RightDockWidgetArea:
                        PaletteDockArea.RIGHT.value,
                    Qt.DockWidgetArea.TopDockWidgetArea:
                        PaletteDockArea.TOP.value,
                    Qt.DockWidgetArea.BottomDockWidgetArea:
                        PaletteDockArea.BOTTOM.value,
                }
                dock_area = area_map.get(area, PaletteDockArea.LEFT.value)
                self.palette_redocked.emit(self.palette_id, dock_area)

    def _on_floating_changed(self, floating: bool):
        """Handle floating state changes."""
        if floating and not self._is_floating_by_user:
            self._is_floating_by_user = True
            self.palette_undocked.emit(self.palette_id)
        elif not floating and self._is_floating_by_user:
            self._is_floating_by_user = False
            # Determine which area we're docked to
            if self.parent():
                document_window = self.parent()
                if isinstance(document_window, QMainWindow):
                    area = document_window.dockWidgetArea(self)
                    area_map = {
                        Qt.DockWidgetArea.LeftDockWidgetArea:
                            PaletteDockArea.LEFT.value,
                        Qt.DockWidgetArea.RightDockWidgetArea:
                            PaletteDockArea.RIGHT.value,
                        Qt.DockWidgetArea.TopDockWidgetArea:
                            PaletteDockArea.TOP.value,
                        Qt.DockWidgetArea.BottomDockWidgetArea:
                            PaletteDockArea.BOTTOM.value,
                    }
                    dock_area = area_map.get(area, PaletteDockArea.LEFT.value)
                    self.palette_redocked.emit(self.palette_id, dock_area)


class PaletteTabWidget(QTabWidget):
    """
    A tab widget that holds multiple palettes in a shared dock area.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabPosition(QTabWidget.TabPosition.South)
        self.setTabsClosable(False)  # Don't allow closing tabs
        self.setMovable(True)       # Allow tab reordering

        # Style the tabs to be more compact
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                top: -1px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #c0c0c0;
                padding: 4px 8px;
                margin-right: 1px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: none;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)


class PaletteManager(QObject):
    """
    Manages all palettes within the main window.
    """

    # Signal emitted when a palette visibility changes
    palette_visibility_changed = Signal(str, bool)  # palette_id, visible

    def __init__(self, document_window):
        """Initialize the palette manager.
        
        Args:
            document_window: The document window to attach palettes to
        """
        super().__init__()
        self.document_window = document_window
        self.palettes: Dict[str, DockablePalette] = {}
        self.palette_configs: Dict[str, Dict[str, Any]] = {}
        self.dock_tab_widgets: Dict[PaletteDockArea, PaletteTabWidget] = {}

        # Load default palette configuration
        self._init_default_configs()

    def _init_default_configs(self):
        """Initialize default palette configurations."""
        self.palette_configs = {
            PaletteType.INFO_PANE.value: {
                'title': 'Info Panel',
                'default_area': PaletteDockArea.TOP,
                'visible': True,
                'width': 600,
                'height': 100,
            },
            PaletteType.CONFIG_PANE.value: {
                'title': 'Properties',
                'default_area': PaletteDockArea.RIGHT,
                'visible': True,
                'width': 250,
                'height': 400,
            },
            PaletteType.SNAPS_PANE.value: {
                'title': 'Snaps',
                'default_area': PaletteDockArea.RIGHT,
                'visible': True,
                'width': 200,
                'height': 100,
            },
        }

    def create_palette(
            self,
            palette_type: PaletteType,
            content_widget: Optional[QWidget] = None
    ) -> str:
        """
        Create a new palette of the specified type.

        Args:
            palette_type: Type of palette to create
            content_widget: Optional custom content widget

        Returns:
            String ID of the created palette
        """
        palette_id = palette_type.value
        config = self.palette_configs.get(palette_id, {})

        # Create content widget if not provided
        if content_widget is None:
            content_widget = self._create_content_widget(palette_type)

        # Create the dockable palette
        title = config.get(
            'title', palette_type.value.replace('_', ' ').title())
        palette = DockablePalette(
            palette_id, title, content_widget, self.document_window)

        # Connect signals
        palette.palette_moved.connect(self._on_palette_moved)
        palette.palette_undocked.connect(self._on_palette_undocked)
        palette.palette_redocked.connect(self._on_palette_redocked)
        palette.palette_visibility_changed.connect(
            self._on_palette_visibility_changed)

        # Set initial size
        width = config.get('width', 250)
        height = config.get('height', 200)
        palette.resize(width, height)

        # Store palette
        self.palettes[palette_id] = palette

        # Add to main window
        default_area = config.get('default_area', PaletteDockArea.RIGHT)
        self._dock_palette(palette, default_area)

        # Set initial visibility
        visible = config.get('visible', True)
        palette.setVisible(visible)

        return palette_id

    def _create_content_widget(self, palette_type: PaletteType) -> QWidget:
        """Create the appropriate content widget for the palette type."""
        if palette_type == PaletteType.INFO_PANE:
            return InfoPane()
        elif palette_type == PaletteType.CONFIG_PANE:
            # Get precision from main window preferences
            precision = 3  # Default fallback
            if hasattr(self.document_window, 'preferences_viewmodel'):
                precision = self.document_window.preferences_viewmodel.get("precision", 3)
            return ConfigPane(precision=precision)
        elif palette_type == PaletteType.SNAPS_PANE:
            # Snaps are now handled by toolbar, return placeholder
            widget = QWidget()
            widget.setMinimumSize(200, 150)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Snaps are now available in the toolbar"))
            widget.setLayout(layout)
            return widget
        else:
            # Fallback to empty widget
            widget = QWidget()
            widget.setMinimumSize(200, 150)
            layout = QVBoxLayout()
            layout.addWidget(QLabel(f"Placeholder for {palette_type.value}"))
            widget.setLayout(layout)
            return widget

    def _dock_palette(
            self, palette: DockablePalette, dock_area: PaletteDockArea):
        """Dock a palette to the specified area."""
        area_map = {
            PaletteDockArea.LEFT: Qt.DockWidgetArea.LeftDockWidgetArea,
            PaletteDockArea.RIGHT: Qt.DockWidgetArea.RightDockWidgetArea,
            PaletteDockArea.TOP: Qt.DockWidgetArea.TopDockWidgetArea,
            PaletteDockArea.BOTTOM: Qt.DockWidgetArea.BottomDockWidgetArea,
        }

        if dock_area == PaletteDockArea.FLOATING:
            palette.setFloating(True)
        else:
            qt_area = area_map.get(
                dock_area, Qt.DockWidgetArea.RightDockWidgetArea)
            self.document_window.addDockWidget(qt_area, palette)

    def _on_palette_moved(self, palette_id: str, new_dock_area: str):
        """Handle palette movement."""
        print(f"Palette {palette_id} moved to {new_dock_area}")

    def _on_palette_undocked(self, palette_id: str):
        """Handle palette undocking (becoming floating)."""
        print(f"Palette {palette_id} undocked (floating)")

    def _on_palette_redocked(self, palette_id: str, dock_area: str):
        """Handle palette redocking."""
        print(f"Palette {palette_id} redocked to {dock_area}")

    def _on_palette_visibility_changed(self, palette_id: str, visible: bool):
        """Handle palette visibility changes."""
        # Forward the signal to any listeners (like the main window menu)
        self.palette_visibility_changed.emit(palette_id, visible)

    def get_palette(self, palette_id: str) -> Optional[DockablePalette]:
        """Get a palette by ID."""
        return self.palettes.get(palette_id)

    def get_palette_content(self, palette_id: str) -> Optional[QWidget]:
        """Get the content widget of a palette."""
        palette = self.get_palette(palette_id)
        if palette:
            return palette.content_widget
        return None

    def show_palette(self, palette_id: str):
        """Show a palette."""
        palette = self.get_palette(palette_id)
        if palette:
            palette.setVisible(True)
            palette.raise_()

    def hide_palette(self, palette_id: str):
        """Hide a palette."""
        palette = self.get_palette(palette_id)
        if palette:
            palette.setVisible(False)

    def toggle_palette(self, palette_id: str):
        """Toggle palette visibility."""
        palette = self.get_palette(palette_id)
        if palette:
            if palette.isVisible():
                self.hide_palette(palette_id)
            else:
                self.show_palette(palette_id)

    def is_palette_visible(self, palette_id: str) -> bool:
        """Check if a palette is visible."""
        palette = self.get_palette(palette_id)
        return palette.isVisible() if palette else False

    def save_palette_layout(self) -> Dict[str, Any]:
        """Save the current palette layout to preferences."""
        layout_data = {}

        for palette_id, palette in self.palettes.items():
            # Get current dock area
            if palette.isFloating():
                dock_area = PaletteDockArea.FLOATING.value
                pos = palette.pos()
                size = palette.size()
            else:
                qt_area = self.document_window.dockWidgetArea(palette)
                area_map = {
                    Qt.DockWidgetArea.LeftDockWidgetArea:
                        PaletteDockArea.LEFT.value,
                    Qt.DockWidgetArea.RightDockWidgetArea:
                        PaletteDockArea.RIGHT.value,
                    Qt.DockWidgetArea.TopDockWidgetArea:
                        PaletteDockArea.TOP.value,
                    Qt.DockWidgetArea.BottomDockWidgetArea:
                        PaletteDockArea.BOTTOM.value,
                }
                dock_area = area_map.get(qt_area, PaletteDockArea.RIGHT.value)
                pos = None
                size = palette.size()

            layout_data[palette_id] = {
                'dock_area': dock_area,
                'visible': palette.isVisible(),
                'size': [size.width(), size.height()],
                'pos': [pos.x(), pos.y()] if pos else None,
            }

        return layout_data

    def restore_palette_layout(self, layout_data: Dict[str, Any]):
        """Restore palette layout from preferences."""
        for palette_id, data in layout_data.items():
            palette = self.get_palette(palette_id)
            if not palette:
                continue

            # Restore dock area
            dock_area_str = data.get('dock_area', PaletteDockArea.RIGHT.value)
            dock_area = PaletteDockArea.FLOATING
            try:
                dock_area = PaletteDockArea(dock_area_str)
                self._dock_palette(palette, dock_area)
            except ValueError:
                # Invalid dock area, use default
                self._dock_palette(palette, PaletteDockArea.RIGHT)

            # Restore size
            size_data = data.get('size', [250, 200])
            palette.resize(QSize(size_data[0], size_data[1]))

            # Restore position if floating
            if dock_area == PaletteDockArea.FLOATING:
                pos_data = data.get('pos')
                if pos_data:
                    palette.move(QPoint(pos_data[0], pos_data[1]))

            # Restore visibility
            visible = data.get('visible', True)
            palette.setVisible(visible)

    def set_palette_visibility(self, palette_id: str, visible: bool):
        """Set palette visibility state."""
        if visible:
            self.show_palette(palette_id)
        else:
            self.hide_palette(palette_id)


def create_default_palettes(document_window) -> PaletteManager:
    """
    Create the default set of palettes for the main window.

    Args:
        document_window: The document window to attach palettes to

    Returns:
        PaletteManager instance with default palettes created
    """
    manager = PaletteManager(document_window)

    # Create default palettes
    manager.create_palette(PaletteType.INFO_PANE)
    manager.create_palette(PaletteType.CONFIG_PANE)

    # Snaps are now handled by toolbar, no longer need palette

    return manager


if __name__ == "__main__":
    """Test the palette system independently."""
    import sys
    from PySide6.QtWidgets import QTextEdit

    app = QApplication(sys.argv)

    # Create a test main window
    main_window = QMainWindow()
    main_window.setWindowTitle("Palette System Test")
    main_window.resize(1024, 768)

    # Add a central widget
    central_widget = QTextEdit()
    central_widget.setText(
        "Main content area\n\nTry docking and undocking the palettes!")
    main_window.setCentralWidget(central_widget)

    # Create palette manager and default palettes
    palette_manager = create_default_palettes(main_window)

    # Show the window
    main_window.show()

    print("Palette system test started!")
    print("- Try dragging palettes to different dock areas")
    print("- Try undocking palettes to make them floating")
    print("- Try redocking floating palettes")

    sys.exit(app.exec())
