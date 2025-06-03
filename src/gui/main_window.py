# filepath: /Users/gminette/dev/git-repos/pyTkCAD/src/gui/main_window.py
"""Main window for the PyTkCAD application."""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFileDialog, QMessageBox, QGraphicsView,
    QGraphicsScene
)
from PySide6.QtCore import QPointF
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


class CADGraphicsView(QGraphicsView):
    """Custom graphics view for CAD drawing operations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)  # We'll handle dragging ourselves
        self.tool_manager = None  # Will be set by the main window

    def set_tool_manager(self, tool_manager):
        """Set the tool manager for handling events"""
        self.tool_manager = tool_manager

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

        # Tools menu
        self.tools_menu = menubar.addMenu("Tools")

    def _create_toolbar(self):
        """Create a toolbar with drawing tools"""
        from PySide6.QtCore import Qt, QSize
        self.toolbar = self.addToolBar("Tools")
        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)
        # Set the icon size to 32x32 for better visibility
        self.toolbar.setIconSize(QSize(32, 32))
        # Reduce spacing between toolbar buttons to zero
        self.toolbar.layout().setSpacing(0)
        self.toolbar.setContentsMargins(0, 0, 0, 0)
        # Make toolbar more compact
        self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        # Apply custom stylesheet for zero spacing with 32x32 icons
        self.toolbar.setStyleSheet("""
            QToolBar {
                spacing: 0px;
                border: none;
            }
            QToolButton {
                margin: 0px;
                padding: 0px;
                border: none;
            }
        """)
        # We'll populate this with tool buttons in _setup_tools()

    def _create_canvas(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Remove all spacing around the canvas
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create graphics view and scene
        self.scene = QGraphicsScene()
        self.canvas = CADGraphicsView()
        self.canvas.setScene(self.scene)
        
        # Remove any default margins/padding from the graphics view
        self.canvas.setContentsMargins(0, 0, 0, 0)
        self.canvas.setStyleSheet("""
            QGraphicsView {
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """)

        layout.addWidget(self.canvas)

    def _setup_tools(self):
        """Set up the tool system and register tools"""
        # Initialize tool manager
        self.tool_manager = ToolManager(
            self.scene, self.document, self.preferences)

        # Connect tool manager to graphics view
        self.canvas.set_tool_manager(self.tool_manager)

        # Register all available tools
        self.tools = {}
        for tool_class in available_tools:
            tool = self.tool_manager.register_tool(tool_class)
            self.tools[tool.definition.token] = tool
            # Connect tool signals to redraw
            tool.object_created.connect(self.on_object_created)

            # Create icon for the tool
            icon = self._load_tool_icon(tool.definition.icon)

            # Add tool to tools menu
            menu_action = QAction(tool.definition.name, self)
            if icon:
                menu_action.setIcon(icon)
            menu_action.triggered.connect(
                lambda checked, t=tool.definition.token: self.activate_tool(t)
            )
            self.tools_menu.addAction(menu_action)

            # Add tool button to toolbar with icon
            toolbar_action = QAction(self)
            if icon:
                toolbar_action.setIcon(icon)
                toolbar_action.setToolTip(tool.definition.name)
            else:
                toolbar_action.setText(tool.definition.name)
            toolbar_action.triggered.connect(
                lambda checked, t=tool.definition.token: self.activate_tool(t)
            )
            self.toolbar.addAction(toolbar_action)

        # Activate the selector tool by default
        if "OBJSEL" in self.tools:
            self.activate_tool("OBJSEL")

    def activate_tool(self, tool_token):
        """Activate a tool by its token"""
        self.tool_manager.activate_tool(tool_token)

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
        self.scene.clear()
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
        self.scene.clear()
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
        """Load an icon for a tool from the images directory"""
        if not icon_name:
            return None

        # Construct the path to the icon file
        images_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'images')
        icon_path = os.path.join(images_dir, f"{icon_name}.gif")

        # Check if the icon file exists
        if not os.path.exists(icon_path):
            return None

        try:
            # Load the image and convert to QIcon at native 32x32 size
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # Use the native 32x32 size of the icon files
                return QIcon(pixmap)
        except Exception as e:
            print(f"Failed to load icon {icon_path}: {e}")

        return None
