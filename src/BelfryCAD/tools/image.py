"""
Image tool for BelfryCAD.

This tool allows users to insert and manipulate image objects in the CAD document.
"""

from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpinBox, QDoubleSpinBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from ..models.cad_object import CadObject, ObjectType
from ..cad_geometry import Point2D
from ..utils.logger import get_logger
from .base import CadTool

if TYPE_CHECKING:
    from ..gui.document_window import DocumentWindow

logger = get_logger(__name__)


class ImageCadObject(CadObject):
    """CAD object representing an image."""
    
    def __init__(self, document_window: 'DocumentWindow', object_id: int, position: Point2D, width: float, height: float,
                 filename: str = "", **kwargs):
        super().__init__(
            document_window, object_id, ObjectType.IMAGE, coords=[position], **kwargs)
        self.position = position
        self.width = width
        self.height = height
        self.filename = filename
        self.pixmap = None
        
        # Load the image if filename is provided
        if filename:
            self.load_image(filename)
    
    def load_image(self, filename: str):
        """Load an image from file."""
        try:
            self.pixmap = QPixmap(filename)
            if self.pixmap.isNull():
                logger.error(f"Failed to load image: {filename}")
                return False
            self.filename = filename
            return True
        except Exception as e:
            logger.error(f"Error loading image {filename}: {e}")
            return False
    
    def get_bounds(self):
        """Get the bounding box of the image."""
        return (
            self.position.x,
            self.position.y,
            self.position.x + self.width,
            self.position.y + self.height
        )
    
    def translate(self, dx: float, dy: float):
        """Translate the image by the given offset."""
        self.position = Point2D(self.position.x + dx, self.position.y + dy)
    
    def scale(self, scale_factor: float, center: Point2D):
        """Scale the image around the given center point."""
        # Scale the position relative to center
        dx = self.position.x - center.x
        dy = self.position.y - center.y
        self.position = Point2D(center.x + dx * scale_factor, center.y + dy * scale_factor)
        
        # Scale dimensions
        self.width *= scale_factor
        self.height *= scale_factor
    
    def rotate(self, angle: float, center: Point2D):
        """Rotate the image around the given center point."""
        # TODO: Implement rotation
        pass


class ImageTool(CadTool):
    """CadTool for inserting images into the CAD document."""
    
    def __init__(self, document_window, document, preferences):
        super().__init__(document_window, document, preferences)
        self.logger = get_logger(__name__)
    
    def activate(self):
        """Activate the image tool."""
        super().activate()
        self.insert_image()
    
    def insert_image(self):
        """Show file dialog and insert selected image."""
        # Show file dialog for image selection
        filename, _ = QFileDialog.getOpenFileName(
            self.document_window,
            "Select Image",
            "",
            "Image files (*.png *.jpg *.jpeg *.bmp *.gif);;All files (*.*)"
        )
        
        if not filename:
            return
        
        # Create image object
        image_obj = ImageCadObject(
            self.document_window,
            self.document.get_next_object_id(),
            Point2D(0, 0),  # Default position
            100, 100,  # Default size
            filename
        )
        
        # Add to document
        self.document.add_object(image_obj)
        self.document.mark_modified()
        
        # Emit signal
        self.object_created.emit(image_obj)
        
        self.logger.info(f"Inserted image: {filename}")
    
    def show_properties_dialog(self, image_obj: ImageCadObject):
        """Show properties dialog for the image."""
        dialog = QDialog(self.document_window)
        dialog.setWindowTitle("Image Properties")
        dialog.setModal(True)
        
        layout = QVBoxLayout()
        
        # Width and height controls
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Width:"))
        width_spin = QDoubleSpinBox()
        width_spin.setRange(1, 10000)
        width_spin.setValue(image_obj.width)
        size_layout.addWidget(width_spin)
        
        size_layout.addWidget(QLabel("Height:"))
        height_spin = QDoubleSpinBox()
        height_spin.setRange(1, 10000)
        height_spin.setValue(image_obj.height)
        size_layout.addWidget(height_spin)
        
        layout.addLayout(size_layout)
        
        # Position controls
        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("X:"))
        x_spin = QDoubleSpinBox()
        x_spin.setRange(-10000, 10000)
        x_spin.setValue(image_obj.position.x)
        pos_layout.addWidget(x_spin)
        
        pos_layout.addWidget(QLabel("Y:"))
        y_spin = QDoubleSpinBox()
        y_spin.setRange(-10000, 10000)
        y_spin.setValue(image_obj.position.y)
        pos_layout.addWidget(y_spin)
        
        layout.addLayout(pos_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update image properties
            image_obj.width = width_spin.value()
            image_obj.height = height_spin.value()
            image_obj.position = Point2D(x_spin.value(), y_spin.value())
            
            # Mark document as modified
            self.document.mark_modified()