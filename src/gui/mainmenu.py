"""
Main Menu System for PyTkCAD

This module implements the main menu bar functionality, translated from the 
original TCL mainmenu.tcl implementation.
"""

from PySide6.QtWidgets import QMenuBar, QMenu
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QKeySequence, QActionGroup, QAction
from typing import Optional, List, Dict, Any


class RecentFilesManager(QObject):
    """Manages the recent files menu and functionality."""
    
    file_selected = Signal(str)  # Signal emitted when a recent file is selected
    
    def __init__(self, preferences, parent=None):
        super().__init__(parent)
        self.preferences = preferences
        self.recent_menu = None
        
    def create_recent_menu(self, parent_menu: QMenu) -> QMenu:
        """Create and return the recent files submenu."""
        self.recent_menu = QMenu("Open Recent", parent_menu)
        self.update_recent_menu()
        return self.recent_menu
    
    def update_recent_menu(self):
        """Update the recent files menu with current list."""
        if not self.recent_menu:
            return
            
        # Clear existing items
        self.recent_menu.clear()
        
        # Get recent files from preferences
        recent_files = self.preferences.get("recent_files", [])
        
        # Add recent file entries
        count = 0
        for filename in recent_files:
            if filename and len(filename) > 0:
                action = QAction(filename, self.recent_menu)
                action.triggered.connect(
                    lambda checked, f=filename: self.file_selected.emit(f)
                )
                self.recent_menu.addAction(action)
                count += 1
        
        # Add separator and clear option if we have files
        if count > 0:
            self.recent_menu.addSeparator()
            clear_action = QAction("Clear Menu", self.recent_menu)
            clear_action.triggered.connect(self.clear_recent_files)
            self.recent_menu.addAction(clear_action)
        else:
            # Add disabled placeholder if no recent files
            no_files_action = QAction("No Recent Files", self.recent_menu)
            no_files_action.setEnabled(False)
            self.recent_menu.addAction(no_files_action)
    
    def add_recent_file(self, filename: str):
        """Add a file to the recent files list."""
        recent_files = self.preferences.get("recent_files", [])
        
        # Remove if already in list
        if filename in recent_files:
            recent_files.remove(filename)
        
        # Add to beginning
        recent_files.insert(0, filename)
        
        # Limit to 10 recent files
        recent_files = recent_files[:10]
        
        # Save back to preferences
        self.preferences.set("recent_files", recent_files)
        
        # Update menu
        self.update_recent_menu()
    
    def clear_recent_files(self):
        """Clear the recent files list."""
        self.preferences.set("recent_files", [])
        self.update_recent_menu()


class MainMenuBar(QObject):
    """Main menu bar implementation for PyTkCAD."""
    
    # File menu signals
    new_triggered = Signal()
    open_triggered = Signal()
    save_triggered = Signal()
    save_as_triggered = Signal()
    close_triggered = Signal()
    import_triggered = Signal()
    export_triggered = Signal()
    page_setup_triggered = Signal()
    print_triggered = Signal()
    
    # Edit menu signals
    undo_triggered = Signal()
    redo_triggered = Signal()
    cut_triggered = Signal()
    copy_triggered = Signal()
    paste_triggered = Signal()
    clear_triggered = Signal()
    select_all_triggered = Signal()
    select_similar_triggered = Signal()
    deselect_all_triggered = Signal()
    group_triggered = Signal()
    ungroup_triggered = Signal()
    
    # Arrange submenu signals
    raise_to_top_triggered = Signal()
    raise_triggered = Signal()
    lower_triggered = Signal()
    lower_to_bottom_triggered = Signal()
    
    # Transform signals
    rotate_90_ccw_triggered = Signal()
    rotate_90_cw_triggered = Signal()
    rotate_180_triggered = Signal()
    
    # Conversion signals
    convert_to_lines_triggered = Signal()
    convert_to_curves_triggered = Signal()
    simplify_curves_triggered = Signal()
    smooth_curves_triggered = Signal()
    join_curves_triggered = Signal()
    vectorize_bitmap_triggered = Signal()
    
    # Boolean operations signals
    union_polygons_triggered = Signal()
    difference_polygons_triggered = Signal()
    intersection_polygons_triggered = Signal()
    
    # View menu signals
    redraw_triggered = Signal()
    actual_size_triggered = Signal()
    zoom_to_fit_triggered = Signal()
    zoom_in_triggered = Signal()
    zoom_out_triggered = Signal()
    show_origin_toggled = Signal(bool)
    show_grid_toggled = Signal(bool)
    
    # CAM menu signals
    configure_mill_triggered = Signal()
    speeds_feeds_wizard_triggered = Signal()
    generate_gcode_triggered = Signal()
    backtrace_gcode_triggered = Signal()
    make_worm_triggered = Signal()
    make_worm_gear_triggered = Signal()
    make_gear_triggered = Signal()
    
    # Window menu signals
    minimize_triggered = Signal()
    cycle_windows_triggered = Signal()
    
    def __init__(self, parent_window, preferences):
        super().__init__(parent_window)
        self.parent_window = parent_window
        self.preferences = preferences
        self.menubar = parent_window.menuBar()
        
        # Initialize recent files manager
        self.recent_files_manager = RecentFilesManager(preferences, self)
        self.recent_files_manager.file_selected.connect(self._handle_recent_file)
        
        # Store references to checkable actions
        self.show_origin_action = None
        self.show_grid_action = None
        
        # Create all menus
        self._create_file_menu()
        self._create_edit_menu()
        self._create_view_menu()
        self._create_cam_menu()
        self._create_window_menu()
        
        # Connect keyboard shortcuts
        self._setup_keyboard_shortcuts()
    
    def _create_file_menu(self):
        """Create the File menu."""
        file_menu = self.menubar.addMenu("&File")
        
        # New
        new_action = QAction("&New", self.parent_window)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_triggered.emit)
        file_menu.addAction(new_action)
        
        # Open
        open_action = QAction("&Open...", self.parent_window)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_triggered.emit)
        file_menu.addAction(open_action)
        
        # Recent files submenu
        recent_menu = self.recent_files_manager.create_recent_menu(file_menu)
        file_menu.addMenu(recent_menu)
        
        file_menu.addSeparator()
        
        # Close
        close_action = QAction("&Close", self.parent_window)
        close_action.setShortcut(QKeySequence.Close)
        close_action.triggered.connect(self.close_triggered.emit)
        file_menu.addAction(close_action)
        
        # Save
        save_action = QAction("&Save", self.parent_window)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_triggered.emit)
        file_menu.addAction(save_action)
        
        # Save As
        save_as_action = QAction("Save &As...", self.parent_window)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_as_triggered.emit)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Import
        import_action = QAction("&Import...", self.parent_window)
        import_action.setShortcut(QKeySequence("Shift+Ctrl+O"))
        import_action.triggered.connect(self.import_triggered.emit)
        file_menu.addAction(import_action)
        
        # Export
        export_action = QAction("&Export...", self.parent_window)
        export_action.setShortcut(QKeySequence("Shift+Alt+Ctrl+S"))
        export_action.triggered.connect(self.export_triggered.emit)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Page Setup
        page_setup_action = QAction("Page Set&up...", self.parent_window)
        page_setup_action.setShortcut(QKeySequence("Shift+Ctrl+P"))
        page_setup_action.triggered.connect(self.page_setup_triggered.emit)
        file_menu.addAction(page_setup_action)
        
        # Print
        print_action = QAction("&Print...", self.parent_window)
        print_action.setShortcut(QKeySequence.Print)
        print_action.triggered.connect(self.print_triggered.emit)
        file_menu.addAction(print_action)
    
    def _create_edit_menu(self):
        """Create the Edit menu."""
        edit_menu = self.menubar.addMenu("&Edit")
        
        # Undo
        undo_action = QAction("&Undo", self.parent_window)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo_triggered.emit)
        edit_menu.addAction(undo_action)
        
        # Redo
        redo_action = QAction("&Redo", self.parent_window)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.redo_triggered.emit)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # Cut
        cut_action = QAction("Cu&t", self.parent_window)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.cut_triggered.emit)
        edit_menu.addAction(cut_action)
        
        # Copy
        copy_action = QAction("&Copy", self.parent_window)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy_triggered.emit)
        edit_menu.addAction(copy_action)
        
        # Paste
        paste_action = QAction("&Paste", self.parent_window)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste_triggered.emit)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        # Select All
        select_all_action = QAction("Select &All", self.parent_window)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(self.select_all_triggered.emit)
        edit_menu.addAction(select_all_action)
        
        # Select All Similar
        select_similar_action = QAction("Select All &Similar", self.parent_window)
        select_similar_action.triggered.connect(self.select_similar_triggered.emit)
        edit_menu.addAction(select_similar_action)
        
        # Deselect All
        deselect_all_action = QAction("&Deselect All", self.parent_window)
        deselect_all_action.setShortcut(QKeySequence("Ctrl+D"))
        deselect_all_action.triggered.connect(self.deselect_all_triggered.emit)
        edit_menu.addAction(deselect_all_action)
        
        edit_menu.addSeparator()
        
        # Clear
        clear_action = QAction("C&lear", self.parent_window)
        clear_action.setShortcut(QKeySequence.Delete)
        clear_action.triggered.connect(self.clear_triggered.emit)
        edit_menu.addAction(clear_action)
        
        edit_menu.addSeparator()
        
        # Group
        group_action = QAction("&Group", self.parent_window)
        group_action.setShortcut(QKeySequence("Ctrl+G"))
        group_action.triggered.connect(self.group_triggered.emit)
        edit_menu.addAction(group_action)
        
        # Ungroup
        ungroup_action = QAction("&Ungroup", self.parent_window)
        ungroup_action.setShortcut(QKeySequence("Shift+Ctrl+G"))
        ungroup_action.triggered.connect(self.ungroup_triggered.emit)
        edit_menu.addAction(ungroup_action)
        
        # Arrange submenu
        arrange_menu = edit_menu.addMenu("&Arrange")
        
        raise_to_top_action = QAction("Raise to &Top", self.parent_window)
        raise_to_top_action.triggered.connect(self.raise_to_top_triggered.emit)
        arrange_menu.addAction(raise_to_top_action)
        
        raise_action = QAction("&Raise", self.parent_window)
        raise_action.triggered.connect(self.raise_triggered.emit)
        arrange_menu.addAction(raise_action)
        
        lower_action = QAction("&Lower", self.parent_window)
        lower_action.triggered.connect(self.lower_triggered.emit)
        arrange_menu.addAction(lower_action)
        
        lower_to_bottom_action = QAction("Lower to &Bottom", self.parent_window)
        lower_to_bottom_action.triggered.connect(self.lower_to_bottom_triggered.emit)
        arrange_menu.addAction(lower_to_bottom_action)
        
        edit_menu.addSeparator()
        
        # Rotation commands
        rotate_ccw_action = QAction("Rotate 90 CCW", self.parent_window)
        rotate_ccw_action.setShortcut(QKeySequence("Ctrl+["))
        rotate_ccw_action.triggered.connect(self.rotate_90_ccw_triggered.emit)
        edit_menu.addAction(rotate_ccw_action)
        
        rotate_cw_action = QAction("Rotate 90 CW", self.parent_window)
        rotate_cw_action.setShortcut(QKeySequence("Ctrl+]"))
        rotate_cw_action.triggered.connect(self.rotate_90_cw_triggered.emit)
        edit_menu.addAction(rotate_cw_action)
        
        rotate_180_action = QAction("Rotate 180", self.parent_window)
        rotate_180_action.triggered.connect(self.rotate_180_triggered.emit)
        edit_menu.addAction(rotate_180_action)
        
        edit_menu.addSeparator()
        
        # Conversion commands
        to_lines_action = QAction("Convert to &Lines", self.parent_window)
        to_lines_action.setShortcut(QKeySequence("Ctrl+L"))
        to_lines_action.triggered.connect(self.convert_to_lines_triggered.emit)
        edit_menu.addAction(to_lines_action)
        
        to_curves_action = QAction("Convert to C&urves", self.parent_window)
        to_curves_action.setShortcut(QKeySequence("Ctrl+B"))
        to_curves_action.triggered.connect(self.convert_to_curves_triggered.emit)
        edit_menu.addAction(to_curves_action)
        
        simplify_curves_action = QAction("&Simplify Curves", self.parent_window)
        simplify_curves_action.setShortcut(QKeySequence("Alt+Ctrl+B"))
        simplify_curves_action.triggered.connect(self.simplify_curves_triggered.emit)
        edit_menu.addAction(simplify_curves_action)
        
        smooth_curves_action = QAction("S&mooth Curves", self.parent_window)
        smooth_curves_action.setShortcut(QKeySequence("Shift+Ctrl+B"))
        smooth_curves_action.triggered.connect(self.smooth_curves_triggered.emit)
        edit_menu.addAction(smooth_curves_action)
        
        join_curves_action = QAction("&Join Curves", self.parent_window)
        join_curves_action.setShortcut(QKeySequence("Ctrl+J"))
        join_curves_action.triggered.connect(self.join_curves_triggered.emit)
        edit_menu.addAction(join_curves_action)
        
        vectorize_action = QAction("&Vectorize Bitmap", self.parent_window)
        vectorize_action.triggered.connect(self.vectorize_bitmap_triggered.emit)
        edit_menu.addAction(vectorize_action)
        
        edit_menu.addSeparator()
        
        # Boolean operations
        union_action = QAction("&Union of Polygons", self.parent_window)
        union_action.setShortcut(QKeySequence("Alt+Ctrl+U"))
        union_action.triggered.connect(self.union_polygons_triggered.emit)
        edit_menu.addAction(union_action)
        
        difference_action = QAction("&Difference of Polygons", self.parent_window)
        difference_action.setShortcut(QKeySequence("Ctrl+Alt+Ctrl+D"))
        difference_action.triggered.connect(self.difference_polygons_triggered.emit)
        edit_menu.addAction(difference_action)
        
        intersection_action = QAction("&Intersection of Polygons", self.parent_window)
        intersection_action.setShortcut(QKeySequence("Alt+Ctrl+I"))
        intersection_action.triggered.connect(self.intersection_polygons_triggered.emit)
        edit_menu.addAction(intersection_action)
    
    def _create_view_menu(self):
        """Create the View menu."""
        view_menu = self.menubar.addMenu("&View")
        
        # Redraw
        redraw_action = QAction("&Redraw", self.parent_window)
        redraw_action.setShortcut(QKeySequence("Ctrl+R"))
        redraw_action.triggered.connect(self.redraw_triggered.emit)
        view_menu.addAction(redraw_action)
        
        # Actual Size
        actual_size_action = QAction("&Actual Size", self.parent_window)
        actual_size_action.setShortcut(QKeySequence("Ctrl+0"))
        actual_size_action.triggered.connect(self.actual_size_triggered.emit)
        view_menu.addAction(actual_size_action)
        
        # Zoom to Fit
        zoom_fit_action = QAction("Zoom to &Fit", self.parent_window)
        zoom_fit_action.triggered.connect(self.zoom_to_fit_triggered.emit)
        view_menu.addAction(zoom_fit_action)
        
        # Zoom In
        zoom_in_action = QAction("Zoom &In", self.parent_window)
        zoom_in_action.setShortcut(QKeySequence.ZoomIn)
        zoom_in_action.triggered.connect(self.zoom_in_triggered.emit)
        view_menu.addAction(zoom_in_action)
        
        # Zoom Out
        zoom_out_action = QAction("Zoom &Out", self.parent_window)
        zoom_out_action.setShortcut(QKeySequence.ZoomOut)
        zoom_out_action.triggered.connect(self.zoom_out_triggered.emit)
        view_menu.addAction(zoom_out_action)
        
        view_menu.addSeparator()
        
        # Show Origin (checkable)
        self.show_origin_action = QAction("Show &Origin", self.parent_window)
        self.show_origin_action.setCheckable(True)
        self.show_origin_action.setChecked(
            self.preferences.get("show_origin", True)
        )
        self.show_origin_action.triggered.connect(
            lambda checked: self.show_origin_toggled.emit(checked)
        )
        view_menu.addAction(self.show_origin_action)
        
        # Show Grid (checkable)
        self.show_grid_action = QAction("Show &Grid", self.parent_window)
        self.show_grid_action.setCheckable(True)
        self.show_grid_action.setChecked(
            self.preferences.get("show_grid", True)
        )
        self.show_grid_action.triggered.connect(
            lambda checked: self.show_grid_toggled.emit(checked)
        )
        view_menu.addAction(self.show_grid_action)
        
        view_menu.addSeparator()
        
        # Placeholder for subwindows menu items (to be added later)
    
    def _create_cam_menu(self):
        """Create the CAM menu."""
        cam_menu = self.menubar.addMenu("&CAM")
        
        # Configure Mill
        configure_mill_action = QAction("Configure &Mill...", self.parent_window)
        configure_mill_action.triggered.connect(self.configure_mill_triggered.emit)
        cam_menu.addAction(configure_mill_action)
        
        cam_menu.addSeparator()
        
        # Speeds & Feeds Wizard
        speeds_feeds_action = QAction("&Speeds && Feeds Wizard", self.parent_window)
        speeds_feeds_action.triggered.connect(self.speeds_feeds_wizard_triggered.emit)
        cam_menu.addAction(speeds_feeds_action)
        
        cam_menu.addSeparator()
        
        # Generate G-Code
        gcode_action = QAction("&Generate G-Code...", self.parent_window)
        gcode_action.triggered.connect(self.generate_gcode_triggered.emit)
        cam_menu.addAction(gcode_action)
        
        # Backtrace G-Code
        backtrace_action = QAction("&Backtrace G-Code...", self.parent_window)
        backtrace_action.triggered.connect(self.backtrace_gcode_triggered.emit)
        cam_menu.addAction(backtrace_action)
        
        cam_menu.addSeparator()
        
        # Wizards
        worm_action = QAction("Make a &Worm...", self.parent_window)
        worm_action.triggered.connect(self.make_worm_triggered.emit)
        cam_menu.addAction(worm_action)
        
        worm_gear_action = QAction("Make a Worm&Gear...", self.parent_window)
        worm_gear_action.triggered.connect(self.make_worm_gear_triggered.emit)
        cam_menu.addAction(worm_gear_action)
        
        gear_action = QAction("Make a &Gear...", self.parent_window)
        gear_action.triggered.connect(self.make_gear_triggered.emit)
        cam_menu.addAction(gear_action)
    
    def _create_window_menu(self):
        """Create the Window menu."""
        window_menu = self.menubar.addMenu("&Window")
        
        # Minimize
        minimize_action = QAction("&Minimize", self.parent_window)
        minimize_action.setShortcut(QKeySequence("Ctrl+M"))
        minimize_action.triggered.connect(self.minimize_triggered.emit)
        window_menu.addAction(minimize_action)
        
        # Cycle Through Windows
        cycle_action = QAction("&Cycle Through Windows", self.parent_window)
        cycle_action.setShortcut(QKeySequence("Ctrl+`"))
        cycle_action.triggered.connect(self.cycle_windows_triggered.emit)
        window_menu.addAction(cycle_action)
        
        window_menu.addSeparator()
        
        # Window list will be populated dynamically
    
    def _setup_keyboard_shortcuts(self):
        """Set up additional keyboard shortcuts not handled by menu actions."""
        # Most shortcuts are handled by the QAction shortcuts above
        # Add any additional global shortcuts here if needed
        pass
    
    def _handle_recent_file(self, filename: str):
        """Handle selection of a recent file."""
        # For now, just emit the open signal
        # The main window should handle opening the specific file
        self.open_triggered.emit()
    
    def add_recent_file(self, filename: str):
        """Add a file to the recent files list."""
        self.recent_files_manager.add_recent_file(filename)
    
    def update_view_preferences(self):
        """Update view menu checkboxes based on current preferences."""
        if self.show_origin_action:
            self.show_origin_action.setChecked(
                self.preferences.get("show_origin", True)
            )
        if self.show_grid_action:
            self.show_grid_action.setChecked(
                self.preferences.get("show_grid", True)
            )
    
    def set_document_state(self, has_document: bool, is_modified: bool = False):
        """Update menu item states based on document availability."""
        # Find and update document-dependent menu items
        # This would typically enable/disable save, export, etc.
        pass
