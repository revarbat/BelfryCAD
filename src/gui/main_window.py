# filepath: /Users/gminette/dev/git-repos/pyTkCAD/src/gui/main_window.py
"""Main window for the PyTkCAD application."""
import math
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

try:
    from PIL import Image, ImageTk
    import io
except ImportError:
    Image = None
    ImageTk = None
    io = None

from src.tools import available_tools, ToolManager


class MainWindow:
    def __init__(self, root, config, preferences, document):
        self.root = root
        self.config = config
        self.preferences = preferences
        self.document = document
        self._setup_ui()

    def _setup_ui(self):
        self.root.title(self.config.APP_NAME)
        self._create_menu()
        self._create_toolbar()
        self._create_canvas()
        self._setup_tools()

    def _create_menu(self):
        menubar = tk.Menu(self.root)

        # File menu
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.new_file)
        filemenu.add_command(label="Open...", command=self.open_file)
        filemenu.add_command(label="Save", command=self.save_file)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=filemenu)

        # Tools menu
        self.toolsmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=self.toolsmenu)

        self.root.config(menu=menubar)

    def _create_toolbar(self):
        """Create a toolbar with drawing tools"""
        self.toolbar_frame = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X)

        # We'll populate this with tool buttons in _setup_tools()

    def _create_canvas(self):
        self.canvas = tk.Canvas(self.root, bg="#ffffff")
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def _setup_tools(self):
        """Set up the tool system and register tools"""
        # Initialize tool manager
        self.tool_manager = ToolManager(
            self.canvas, self.document, self.preferences)
        # Register all available tools
        self.tools = {}
        for tool_class in available_tools:
            tool = self.tool_manager.register_tool(tool_class)
            self.tools[tool.definition.token] = tool
            # Add tool to tools menu
            self.toolsmenu.add_command(
                label=tool.definition.name,
                command=lambda t=tool.definition.token: self.activate_tool(t)
            )
            # Add tool button to toolbar
            btn = tk.Button(
                self.toolbar_frame,
                text=tool.definition.name,
                command=lambda t=tool.definition.token: self.activate_tool(t)
            )
            btn.pack(side=tk.LEFT)
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
        self.root.title(title)

    def new_file(self):
        if self.document.is_modified():
            if not self._confirm_discard_changes():
                return
        self.document.new()
        self.update_title()
        self.canvas.delete("all")
        self.draw_objects()

    def open_file(self):
        if self.document.is_modified():
            if not self._confirm_discard_changes():
                return
        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Open Document",
            defaultextension=".tkcad",
            filetypes=[
                ("TkCAD files", "*.tkcad"),
                ("SVG files", "*.svg"),
                ("DXF files", "*.dxf"),
                ("All files", "*.*")
            ]
        )
        if filename:
            try:
                self.document.load(filename)
                self.update_title()
                self.canvas.delete("all")
                self.draw_objects()
            except Exception as e:
                messagebox.showerror(
                    "Open Error",
                    f"Failed to open file:\n{e}"
                )

    def save_file(self):
        if not self.document.filename:
            filename = filedialog.asksaveasfilename(
                parent=self.root,
                title="Save Document",
                defaultextension=".tkcad",
                filetypes=[
                    ("TkCAD files", "*.tkcad"),
                    ("SVG files", "*.svg"),
                    ("DXF files", "*.dxf"),
                    ("All files", "*.*")
                ]
            )
            if not filename:
                return
            self.document.filename = filename
        try:
            self.document.save()
            self.update_title()
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file:\n{e}")

    def _confirm_discard_changes(self):
        result = messagebox.askyesno(
            "Unsaved Changes",
            "You have unsaved changes. Discard them?",
            parent=self.root
        )
        return result

    def draw_objects(self):
        self.canvas.delete("all")
        for obj in self.document.objects.get_all_objects():
            t = getattr(obj, 'object_type', None)
            if t is None:
                continue
            tname = t.value if hasattr(t, 'value') else str(t)
            if tname == "line":
                pts = obj.coords
                if len(pts) == 2:
                    self.canvas.create_line(
                        pts[0].x, pts[0].y, pts[1].x, pts[1].y,
                        fill=obj.attributes.get('color', 'black')
                    )
            elif tname == "circle":
                pts = obj.coords
                r = obj.attributes.get('radius', 0)
                if pts and r:
                    x, y = pts[0].x, pts[0].y
                    self.canvas.create_oval(
                        x - r, y - r, x + r, y + r,
                        outline=obj.attributes.get('color', 'black')
                    )
            elif tname == "point":
                pts = obj.coords
                if pts:
                    x, y = pts[0].x, pts[0].y
                    self.canvas.create_oval(
                        x-2, y-2, x+2, y+2,
                        fill=obj.attributes.get('color', 'black')
                    )
            elif tname == "arc":
                # Draw an arc
                pts = obj.coords
                if len(pts) >= 3:
                    center = pts[0]
                    radius = obj.attributes.get('radius', 0)
                    start_angle = obj.attributes.get('start_angle', 0)
                    end_angle = obj.attributes.get('end_angle', 0)

                    # Create points along the arc
                    arc_points = []
                    steps = 36  # Number of segments for the arc

                    # Ensure proper arc direction
                    if end_angle < start_angle:
                        end_angle += 2 * math.pi

                    angle_step = (end_angle - start_angle) / steps

                    for i in range(steps + 1):
                        angle = start_angle + i * angle_step
                        x = center.x + radius * math.cos(angle)
                        y = center.y + radius * math.sin(angle)
                        arc_points.extend([x, y])

                    if len(arc_points) >= 4:  # Need at least 2 points
                        self.canvas.create_line(
                            *arc_points,
                            fill=obj.attributes.get('color', 'black'),
                            width=obj.attributes.get('linewidth', 1)
                        )

                    # If selected, draw control points
                    if obj.selected:
                        # Draw center point
                        self.canvas.create_rectangle(
                            center.x - 3, center.y - 3,
                            center.x + 3, center.y + 3,
                            outline="red", fill="white"
                        )

                        # Draw start and end points
                        for pt in pts[1:3]:
                            self.canvas.create_rectangle(
                                pt.x - 3, pt.y - 3,
                                pt.x + 3, pt.y + 3,
                                outline="red", fill="white"
                            )

                        # Draw radius lines
                        self.canvas.create_line(
                            center.x, center.y, pts[1].x, pts[1].y,
                            fill="red", dash=(2, 2)
                        )
                        self.canvas.create_line(
                            center.x, center.y, pts[2].x, pts[2].y,
                            fill="red", dash=(2, 2)
                        )
            elif tname == "bezier":
                pts = obj.coords
                is_quadratic = obj.attributes.get('is_quadratic', True)

                # Draw the bezier curve
                if is_quadratic:
                    # Quadratic bezier - every set of 3 points forms a segment
                    for i in range(0, len(pts) - 2, 2):
                        p0 = pts[i]
                        p1 = pts[i+1]
                        p2 = pts[i+2]

                        # Calculate points along the curve
                        curve_points = []
                        steps = 20
                        for step in range(steps + 1):
                            t = step / steps
                            # Quadratic bezier formula
                            x = ((1-t)**2 * p0.x + 2*(1-t)*t * p1.x +
                                 t**2 * p2.x)
                            y = ((1-t)**2 * p0.y + 2*(1-t)*t * p1.y +
                                 t**2 * p2.y)
                            curve_points.extend([x, y])

                        # Draw the curve
                        self.canvas.create_line(
                            *curve_points,
                            fill=obj.attributes.get('color', 'black'),
                            width=obj.attributes.get('linewidth', 1),
                            smooth=True
                        )
                else:
                    # Cubic bezier - every set of 4 points forms a segment
                    for i in range(0, len(pts) - 3, 3):
                        p0 = pts[i]
                        p1 = pts[i+1]
                        p2 = pts[i+2]
                        p3 = pts[i+3]

                        # Calculate points along the curve
                        curve_points = []
                        steps = 20
                        for step in range(steps + 1):
                            t = step / steps
                            # Cubic bezier formula
                            x = ((1-t)**3 * p0.x + 3*(1-t)**2*t * p1.x +
                                 3*(1-t)*t**2 * p2.x + t**3 * p3.x)
                            y = ((1-t)**3 * p0.y + 3*(1-t)**2*t * p1.y +
                                 3*(1-t)*t**2 * p2.y + t**3 * p3.y)
                            curve_points.extend([x, y])

                        # Draw the curve
                        self.canvas.create_line(
                            *curve_points,
                            fill=obj.attributes.get('color', 'black'),
                            width=obj.attributes.get('linewidth', 1),
                            smooth=True
                        )

                # If object is selected, draw its control points
                if obj.selected:
                    for i, p in enumerate(pts):
                        # Endpoints are rectangles, control points are ovals
                        if (is_quadratic and (i % 2 == 0)) or \
                           (not is_quadratic and (i % 3 == 0)):
                            # Endpoint
                            self.canvas.create_rectangle(
                                p.x - 3, p.y - 3, p.x + 3, p.y + 3,
                                outline="red", fill="white"
                            )
                        else:
                            # Control point
                            self.canvas.create_oval(
                                p.x - 3, p.y - 3, p.x + 3, p.y + 3,
                                outline="red", fill="white"
                            )
            elif tname == "image":
                # Draw image objects
                self._draw_image_object(obj)
        # ...extend for more object types as needed...

    def _draw_image_object(self, obj):
        """Draw an image object on the canvas."""
        if not Image or not ImageTk:
            # PIL/Pillow not available, show placeholder
            self._draw_image_placeholder(obj)
            return

        # Get image data and geometry from object
        geometry = getattr(obj, 'geometry', {})
        if not geometry:
            return

        image_data = geometry.get('image_data')
        if not image_data:
            return

        try:
            x = geometry.get('x', 0)
            y = geometry.get('y', 0)
            width = geometry.get('width', 100)
            height = geometry.get('height', 100)
            rotation = geometry.get('rotation', 0.0)

            # Create PIL image from stored data
            img = Image.open(io.BytesIO(image_data))

            # Resize image to display dimensions
            if width > 0 and height > 0:
                img = img.resize(
                    (int(width), int(height)),
                    Image.Resampling.LANCZOS
                )

            # Apply rotation if needed
            if rotation != 0.0:
                img = img.rotate(rotation, expand=True)

            # Convert to PhotoImage for tkinter
            photo = ImageTk.PhotoImage(img)

            # Create canvas image
            self.canvas.create_image(x, y, image=photo, anchor='nw')

            # Store reference to prevent garbage collection
            if not hasattr(self.canvas, 'image_refs'):
                self.canvas.image_refs = []
            self.canvas.image_refs.append(photo)

            # If object is selected, draw selection frame
            if getattr(obj, 'selected', False):
                self._draw_image_selection_frame(x, y, width, height)

        except Exception as e:
            print(f"Error drawing image: {e}")
            # Fall back to placeholder
            self._draw_image_placeholder(obj)

    def _draw_image_placeholder(self, obj):
        """Draw a placeholder rectangle for images when PIL is unavailable."""
        geometry = getattr(obj, 'geometry', {})
        if not geometry:
            return

        x = geometry.get('x', 0)
        y = geometry.get('y', 0)
        width = geometry.get('width', 100)
        height = geometry.get('height', 100)

        # Draw placeholder rectangle
        self.canvas.create_rectangle(
            x, y, x + width, y + height,
            outline='gray', dash=(5, 5), fill='lightgray'
        )

        # Add "IMAGE" text in center
        center_x = x + width / 2
        center_y = y + height / 2
        self.canvas.create_text(
            center_x, center_y,
            text="IMAGE",
            fill='black',
            font=('Arial', 10)
        )

        # If object is selected, draw selection frame
        if getattr(obj, 'selected', False):
            self._draw_image_selection_frame(x, y, width, height)

    def _draw_image_selection_frame(self, x, y, width, height):
        """Draw selection frame around an image."""
        # Draw selection rectangle
        self.canvas.create_rectangle(
            x - 2, y - 2, x + width + 2, y + height + 2,
            outline='red', width=2, dash=(3, 3)
        )

        # Draw corner handles
        handle_size = 6
        corners = [
            (x, y),                          # Top-left
            (x + width, y),                  # Top-right
            (x + width, y + height),         # Bottom-right
            (x, y + height)                  # Bottom-left
        ]

        for corner_x, corner_y in corners:
            self.canvas.create_rectangle(
                corner_x - handle_size//2, corner_y - handle_size//2,
                corner_x + handle_size//2, corner_y + handle_size//2,
                outline='red', fill='white', width=2
            )
