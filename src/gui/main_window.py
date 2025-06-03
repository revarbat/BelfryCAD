# filepath: /Users/gminette/dev/git-repos/pyTkCAD/src/gui/main_window.py
"""Main window for the PyTkCAD application."""
import os
import math
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QFileDialog,
    QMessageBox, QGraphicsView, QGraphicsScene
)
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QAction, QIcon, QPixmap
)

try:
    from PIL import Image
    import io
except ImportError:
    Image = None
    io = None

from src.tools import available_tools, ToolManager
from src.gui.category_button import CategoryToolButton
from src.gui.rulers import RulerManager
from src.gui.preferences_dialog_qt import PreferencesDialog


class CADGraphicsView(QGraphicsView):
    """Custom graphics view for CAD drawing operations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)  # Handle dragging ourselves

        # Enable scrollbars
        from PySide6.QtCore import Qt
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Enable mouse wheel scrolling
        self.setInteractive(True)

        # Enable mouse tracking to receive mouse move events
        # even when no buttons are pressed
        self.setMouseTracking(True)

        self.tool_manager = None  # Will be set by the main window

    def set_tool_manager(self, tool_manager):
        """Set the tool manager for handling events"""
        self.tool_manager = tool_manager

    def wheelEvent(self, event):
        """Handle mouse wheel events for scrolling"""
        from PySide6.QtCore import Qt

        # Get wheel delta values
        delta = event.angleDelta()

        # Scroll speed multiplier
        scroll_speed = 30

        # Handle horizontal scrolling (Shift+wheel or horizontal wheel)
        if event.modifiers() & Qt.ShiftModifier or delta.x() != 0:
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
            # Create a simple event object with scene coordinates and x/y attrs

            class SceneEvent:

                def __init__(self, scene_pos):
                    self._scene_pos = scene_pos
                    self.x = scene_pos.x()
                    self.y = scene_pos.y()

                def scenePos(self):
                    return self._scene_pos

            scene_event = SceneEvent(scene_pos)
            self.tool_manager.get_active_tool().handle_mouse_down(scene_event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move events and forward to active tool"""
        if self.tool_manager and self.tool_manager.get_active_tool():
            scene_pos = self.mapToScene(event.pos())

            class SceneEvent:

                def __init__(self, scene_pos):
                    self._scene_pos = scene_pos
                    self.x = scene_pos.x()
                    self.y = scene_pos.y()

                def scenePos(self):
                    return self._scene_pos

            scene_event = SceneEvent(scene_pos)
            self.tool_manager.get_active_tool().handle_mouse_move(scene_event)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events and forward to active tool"""
        if self.tool_manager and self.tool_manager.get_active_tool():
            scene_pos = self.mapToScene(event.pos())

            class SceneEvent:

                def __init__(self, scene_pos):
                    self._scene_pos = scene_pos
                    self.x = scene_pos.x()
                    self.y = scene_pos.y()

                def scenePos(self):
                    return self._scene_pos

            scene_event = SceneEvent(scene_pos)
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
        self._setup_tools()

    def _create_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)

        open_action = QAction("Open...", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        preferences_action = QAction("Preferences...", self)
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)

        # Tools menu
        self.tools_menu = menubar.addMenu("Tools")

    def _create_toolbar(self):
        """Create a toolbar with drawing tools"""
        from PySide6.QtCore import Qt, QSize
        self.toolbar = self.addToolBar("Tools")
        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)
        # Set the icon size to 48x48 for 150% size visibility
        self.toolbar.setIconSize(QSize(48, 48))
        # Set spacing between toolbar buttons to 2 pixels
        self.toolbar.layout().setSpacing(2)
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        # Make toolbar more compact
        self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        # Apply custom stylesheet with 2px spacing
        self.toolbar.setStyleSheet("""
            QToolBar {
                spacing: 2px;
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

    def _setup_tools(self):
        """Set up the tool system and register tools"""
        # Initialize tool manager
        self.tool_manager = ToolManager(
            self.scene, self.document, self.preferences)

        # Connect tool manager to graphics view
        self.canvas.set_tool_manager(self.tool_manager)

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
            menu_action = QAction(tool.definition.name, self)
            icon = self._load_tool_icon(tool.definition.icon)
            if icon:
                menu_action.setIcon(icon)
            menu_action.triggered.connect(
                lambda checked, t=tool.definition.token: self.activate_tool(t)
            )
            self.tools_menu.addAction(menu_action)

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
                msg.setIcon(QMessageBox.Critical)
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
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Save Error")
            msg.setText(f"Failed to save file:\n{e}")
            msg.exec()

    def show_preferences(self):
        """Show the preferences dialog."""
        dialog = PreferencesDialog(self)
        dialog.exec()

    def _confirm_discard_changes(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Unsaved Changes")
        msg.setText("You have unsaved changes. Discard them?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        result = msg.exec()
        return result == QMessageBox.Yes

    def draw_objects(self):
        # Clear the scene but keep axis lines and grid lines
        axis_items = []
        for item in self.scene.items():
            if hasattr(item, 'zValue') and item.zValue() <= -999:
                axis_items.append(item)

        self.scene.clear()
        
        # Re-add axis lines and grid lines
        self._add_axis_lines()
        self._add_grid_lines()

        # Draw all document objects
        for obj in self.document.objects.get_all_objects():
            t = getattr(obj, 'object_type', None)
            if t is None:
                continue
            tname = t.value if hasattr(t, 'value') else str(t)

            color = QColor(obj.attributes.get('color', 'black'))
            pen = QPen(color)
            pen.setWidth(obj.attributes.get('linewidth', 1))

            if tname == "line":
                pts = obj.coords
                if len(pts) == 2:
                    self.scene.addLine(
                        pts[0].x, pts[0].y, pts[1].x, pts[1].y, pen
                    )
            elif tname == "circle":
                pts = obj.coords
                r = obj.attributes.get('radius', 0)
                if pts and r:
                    x, y = pts[0].x, pts[0].y
                    self.scene.addEllipse(
                        x - r, y - r, 2*r, 2*r, pen
                    )
            elif tname == "point":
                pts = obj.coords
                if pts:
                    x, y = pts[0].x, pts[0].y
                    brush = QBrush(color)
                    self.scene.addEllipse(
                        x-2, y-2, 4, 4, pen, brush
                    )
            elif tname == "polygon":
                pts = obj.coords
                if len(pts) >= 3:
                    from PySide6.QtGui import QPolygonF
                    polygon = QPolygonF()
                    for pt in pts:
                        polygon.append(QPointF(pt.x, pt.y))
                    self.scene.addPolygon(polygon, pen)
            # Add more object types as needed...

    def _draw_image_object(self, obj):
        """Draw an image object on the scene."""
        # TODO: Implement image drawing with QGraphicsPixmapItem
        pass

    def _draw_image_placeholder(self, obj):
        """Draw a placeholder rectangle for images."""
        # TODO: Implement placeholder drawing
        pass

    def on_object_created(self, obj):
        """Handle when a tool creates a new object"""
        self.draw_objects()
        self.update_title()

    def _load_tool_icon(self, icon_name):
        """Load an icon for a tool, preferring SVG over PNG"""
        if not icon_name:
            return None

        # Construct the path to the images directory
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
                        48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    return QIcon(scaled_pixmap)
            except Exception as e:
                print(f"Failed to load PNG icon {png_path}: {e}")

        return None

    def _add_axis_lines(self):
        """Add axis lines at X=0 and Y=0 for reference"""
        # Create a distinctive pen for axis lines
        axis_pen = QPen(QColor(128, 128, 128))  # Gray color
        axis_pen.setWidth(1)
        # axis_pen.setStyle(Qt.DashLine)  # Dashed line style

        # Add horizontal axis line (Y=0) across the scene width
        scene_rect = self.scene.sceneRect()
        h_axis_line = self.scene.addLine(
            scene_rect.left(), 0,
            scene_rect.right(), 0,
            axis_pen
        )

        # Add vertical axis line (X=0) across the scene height
        v_axis_line = self.scene.addLine(
            0, scene_rect.top(),
            0, scene_rect.bottom(),
            axis_pen
        )

        # Set the axis lines and origin marker to be behind other objects
        h_axis_line.setZValue(-1000)
        v_axis_line.setZValue(-1000)

    def _add_grid_lines(self):
        """Add dotted grid lines that align with ruler major tickmarks"""
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
        grid_pen.setStyle(Qt.DotLine)  # Dotted line style

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
        self.ruler_manager.update_rulers()
        # Redraw grid lines to match new view
        self._redraw_grid()

    def _redraw_grid(self):
        """Remove existing grid lines and redraw them."""
        # Remove existing grid lines (z-value -1001)
        items_to_remove = []
        for item in self.scene.items():
            if hasattr(item, 'zValue') and item.zValue() == -1001:
                items_to_remove.append(item)

        for item in items_to_remove:
            self.scene.removeItem(item)

        # Add new grid lines
        self._add_grid_lines()
