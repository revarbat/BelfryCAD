"""
Factory for creating CAD object viewmodels.
"""

from typing import Optional, Type, Dict, Any, TYPE_CHECKING

from ...models.cad_object import CadObject
from ...models.cad_objects.line_cad_object import LineCadObject
from ...models.cad_objects.circle_cad_object import CircleCadObject
from ...models.cad_objects.arc_cad_object import ArcCadObject
from ...models.cad_objects.ellipse_cad_object import EllipseCadObject
from ...models.cad_objects.cubic_bezier_cad_object import CubicBezierCadObject
from ...models.cad_objects.gear_cad_object import GearCadObject

from .cad_viewmodels.cad_viewmodel import CadViewModel
from .cad_viewmodels.line_viewmodel import LineViewModel
from .cad_viewmodels.circle_viewmodel import CircleViewModel
from .cad_viewmodels.arc_viewmodel import ArcViewModel
from .cad_viewmodels.ellipse_viewmodel import EllipseViewModel
from .cad_viewmodels.cubic_bezier_viewmodel import CubicBezierViewModel
from .cad_viewmodels.gear_viewmodel import GearViewModel

if TYPE_CHECKING:
    from ..document_window import DocumentWindow


class CadObjectFactory:
    """Factory for creating CAD object viewmodels."""

    # Mapping of CadObject types to their corresponding ViewModel classes
    _viewmodel_map: Dict[Type[CadObject], Type[CadViewModel]] = {
        LineCadObject: LineViewModel,
        CircleCadObject: CircleViewModel,
        ArcCadObject: ArcViewModel,
        EllipseCadObject: EllipseViewModel,
        CubicBezierCadObject: CubicBezierViewModel,
        GearCadObject: GearViewModel,
    }

    def __init__(self, document_window: Optional['DocumentWindow'] = None):
        """Initialize the factory.
        
        Args:
            document_window: Reference to the document window
        """
        self._document_window = document_window

    def create_viewmodel(self, cad_object: CadObject) -> Optional[CadViewModel]:
        """Create a viewmodel for the given CAD object.
        
        Args:
            cad_object: The CAD object to create a viewmodel for
            
        Returns:
            The created viewmodel, or None if no suitable viewmodel class is found
        """
        # Get the viewmodel class for this object type
        vm_class = self._viewmodel_map.get(type(cad_object))
        if not vm_class or not self._document_window:
            return None
            
        # Create and return the viewmodel
        return vm_class(self._document_window, cad_object)

    def create_gear_viewmodel(self, model: GearCadObject) -> GearViewModel:
        """Create a gear viewmodel.
        
        Args:
            model: The gear CAD object
            
        Returns:
            The created gear viewmodel
        """
        if not self._document_window:
            raise ValueError("Document window is required to create viewmodels")
        viewmodel = GearViewModel(self._document_window, model)
        return viewmodel

    def create_circle_viewmodel(self, model: CircleCadObject) -> CircleViewModel:
        """Create a circle viewmodel.
        
        Args:
            model: The circle CAD object
            
        Returns:
            The created circle viewmodel
        """
        if not self._document_window:
            raise ValueError("Document window is required to create viewmodels")
        viewmodel = CircleViewModel(self._document_window, model)
        return viewmodel

    def create_line_viewmodel(self, model: LineCadObject) -> LineViewModel:
        """Create a line viewmodel.
        
        Args:
            model: The line CAD object
            
        Returns:
            The created line viewmodel
        """
        if not self._document_window:
            raise ValueError("Document window is required to create viewmodels")
        viewmodel = LineViewModel(self._document_window, model)
        return viewmodel

    def create_arc_viewmodel(self, model: ArcCadObject) -> ArcViewModel:
        """Create an arc viewmodel.
        
        Args:
            model: The arc CAD object
            
        Returns:
            The created arc viewmodel
        """
        if not self._document_window:
            raise ValueError("Document window is required to create viewmodels")
        viewmodel = ArcViewModel(self._document_window, model)
        return viewmodel

    def create_ellipse_viewmodel(self, model: EllipseCadObject) -> EllipseViewModel:
        """Create an ellipse viewmodel.
        
        Args:
            model: The ellipse CAD object
            
        Returns:
            The created ellipse viewmodel
        """
        if not self._document_window:
            raise ValueError("Document window is required to create viewmodels")
        viewmodel = EllipseViewModel(self._document_window, model)
        return viewmodel

    def create_cubic_bezier_viewmodel(self, model: CubicBezierCadObject) -> CubicBezierViewModel:
        """Create a cubic bezier viewmodel.
        
        Args:
            model: The cubic bezier CAD object
            
        Returns:
            The created cubic bezier viewmodel
        """
        if not self._document_window:
            raise ValueError("Document window is required to create viewmodels")
        viewmodel = CubicBezierViewModel(self._document_window, model)
        return viewmodel 