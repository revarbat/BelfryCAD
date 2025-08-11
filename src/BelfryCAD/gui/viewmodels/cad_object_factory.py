"""
CAD Object Factory for creating proper MVVM structure.

This factory creates the MVVM chain: Model -> ViewModel
for CAD objects, ensuring proper separation of concerns.
The ViewModels are responsible for creating and managing their own view items.
"""

from typing import Dict, Type, Optional, TYPE_CHECKING, Tuple
from PySide6.QtCore import QObject
from PySide6.QtGui import QColor

from ...models.cad_objects.gear_cad_object import GearCadObject
from ...models.cad_objects.circle_cad_object import CircleCadObject
from ...models.cad_objects.line_cad_object import LineCadObject
from ...models.cad_objects.arc_cad_object import ArcCadObject
from ...models.cad_objects.ellipse_cad_object import EllipseCadObject
from ...models.cad_objects.cubic_bezier_cad_object import CubicBezierCadObject
from ...cad_geometry import Point2D

from .cad_viewmodels import (
    CadViewModel,
    GearViewModel,
    CircleViewModel,
    LineViewModel,
    ArcViewModel,
    EllipseViewModel,
    CubicBezierViewModel
)

if TYPE_CHECKING:
    from ...models.cad_object import CadObject


class CADObjectFactory(QObject):
    """Factory for creating CAD objects with proper MVVM structure."""
    
    def __init__(self, main_window=None):
        super().__init__()
        self._main_window = main_window
        self._viewmodel_classes: Dict[str, Type] = {
            "gear": GearViewModel,
            "circle": CircleViewModel,
            "line": LineViewModel,
            "arc": ArcViewModel,
            "ellipse": EllipseViewModel,
            "cubic_bezier": CubicBezierViewModel,
        }
    
    def create_viewmodel_for(self, cad_object: 'CadObject') -> Optional[CadViewModel]:
        """
        Create a ViewModel instance for an existing CadObject model.
        
        Args:
            cad_object: The model object to wrap in a ViewModel
        
        Returns:
            A CadViewModel instance appropriate for the model, or None for unsupported types
        """
        # Derive type key similar to model class naming convention
        type_name = type(cad_object).__name__.replace('CadObject', '').lower()
        # Normalize known names that differ from keys
        mapping_overrides = {
            'cubic_bezier': 'cubic_bezier',
        }
        # For classes like LineCadObject -> 'line'
        if type_name.endswith('_cad_object'):
            type_name = type_name.replace('_cad_object', '')
        type_key = mapping_overrides.get(type_name, type_name)
        vm_class = self._viewmodel_classes.get(type_key)
        if not vm_class:
            return None
        return vm_class(self._main_window, cad_object)
    
    def create_gear_object(self,
                          center_point: Point2D,
                          pitch_diameter: float,
                          num_teeth: int,
                          pressure_angle: float = 20.0,
                          color: str = "black",
                          line_width: Optional[float] = 0.05) -> Tuple['CadObject', 'CadViewModel']:
        """Create a gear object with MVVM structure."""
        # Create Model
        model = GearCadObject(
            center_point=center_point,
            pitch_diameter=pitch_diameter,
            num_teeth=num_teeth,
            pressure_angle=pressure_angle,
            color=color,
            line_width=line_width
        )
        
        # Create ViewModel
        viewmodel = GearViewModel(self._main_window, model)
        
        return model, viewmodel
    
    def create_circle_object(self,
                           center_point: Point2D,
                           radius: float,
                           color: str = "black",
                           line_width: Optional[float] = 0.05) -> Tuple['CadObject', 'CadViewModel']:
        """
        Create a circle object with MVVM structure.
        
        Args:
            center_point: Center point of the circle
            radius: Radius of the circle
            color: Color of the circle
            line_width: Line width of the circle
            
        Returns:
            Tuple of (model, viewmodel)
        """
        # Create Model
        perimeter_point = center_point + Point2D(radius, 0)
        model = CircleCadObject(
            center_point=center_point,
            perimeter_point=perimeter_point,
            color=color,
            line_width=line_width
        )
        
        # Create ViewModel
        viewmodel = CircleViewModel(self._main_window, model)
        
        return model, viewmodel
    
    def create_line_object(self,
                          start_point: Point2D,
                          end_point: Point2D,
                          color: str = "black",
                          line_width: Optional[float] = 0.05) -> Tuple['CadObject', 'CadViewModel']:
        """
        Create a line object with MVVM structure.
        
        Args:
            start_point: Start point of the line
            end_point: End point of the line
            color: Color of the line
            line_width: Line width of the line
            
        Returns:
            Tuple of (model, viewmodel)
        """
        # Create Model
        model = LineCadObject(
            start_point=start_point,
            end_point=end_point,
            color=color,
            line_width=line_width
        )
        
        # Create ViewModel
        viewmodel = LineViewModel(self._main_window, model)
        
        return model, viewmodel
    
    def create_arc_object(self,
                         center_point: Point2D,
                         start_point: Point2D,
                         end_point: Point2D,
                         color: str = "black",
                         line_width: Optional[float] = 0.05) -> Tuple['CadObject', 'CadViewModel']:
        """
        Create an arc object with MVVM structure.
        
        Args:
            center_point: Center point of the arc
            start_point: Start point of the arc
            end_point: End point of the arc
            color: Color of the arc
            line_width: Line width of the arc
            
        Returns:
            Tuple of (model, viewmodel)
        """
        # Create Model
        model = ArcCadObject(
            center_point=center_point,
            start_point=start_point,
            end_point=end_point,
            color=color,
            line_width=line_width,
            main_window=self._main_window
        )
        
        # Create ViewModel
        viewmodel = ArcViewModel(self._main_window, model)
        
        return model, viewmodel
    
    def create_ellipse_object(self,
                             center_point: Point2D,
                             major_axis_point: Point2D,
                             minor_axis_point: Point2D,
                             color: str = "black",
                             line_width: Optional[float] = 0.05) -> Tuple['CadObject', 'CadViewModel']:
        """
        Create an ellipse object with MVVM structure.
        
        Args:
            center_point: Center point of the ellipse
            major_axis_point: Point defining the major axis
            minor_axis_point: Point defining the minor axis
            color: Color of the ellipse
            line_width: Line width of the ellipse
            
        Returns:
            Tuple of (model, viewmodel)
        """
        # Create Model
        model = EllipseCadObject(
            center_point=center_point,
            major_axis_point=major_axis_point,
            minor_axis_point=minor_axis_point,
            color=color,
            line_width=line_width,
            main_window=self._main_window
        )
        
        # Create ViewModel
        viewmodel = EllipseViewModel(self._main_window, model)
        
        return model, viewmodel
    
    def create_cubic_bezier_object(self,
                                  points: list,
                                  color: str = "black",
                                  line_width: Optional[float] = 0.05) -> Tuple['CadObject', 'CadViewModel']:
        """
        Create a cubic bezier object with MVVM structure.
        
        Args:
            points: List of control points for the bezier curve
            color: Color of the bezier curve
            line_width: Line width of the bezier curve
            
        Returns:
            Tuple of (model, viewmodel)
        """
        # Create Model
        model = CubicBezierCadObject(
            points=points,
            color=color,
            line_width=line_width,
            main_window=self._main_window
        )
        
        # Create ViewModel
        viewmodel = CubicBezierViewModel(self._main_window, model)
        
        return model, viewmodel 