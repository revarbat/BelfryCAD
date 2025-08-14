"""
XML Serializer for BelfryCAD Documents

This module provides serialization and deserialization of BelfryCAD documents
to/from a zip-compressed XML format. The format supports:

- Document preferences (units, precision, etc.)
- Parameters and expressions
- CAD objects with transformations
- Constraints system
- Object grouping
- Fixed/free constraint data
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
import json
import math

from ..models.document import Document
from ..models.cad_object import CadObject
from ..models.cad_objects.group_cad_object import GroupCadObject
from ..models.cad_objects.line_cad_object import LineCadObject
from ..models.cad_objects.circle_cad_object import CircleCadObject
from ..models.cad_objects.arc_cad_object import ArcCadObject
from ..models.cad_objects.ellipse_cad_object import EllipseCadObject
from ..models.cad_objects.cubic_bezier_cad_object import CubicBezierCadObject
from ..models.cad_objects.gear_cad_object import GearCadObject
from ..utils.cad_expression import CadExpression
from ..utils.constraints import ConstraintSolver, Constraint
from ..cad_geometry import Point2D, Transform2D


class BelfryCADXMLSerializer:
    """
    Serializer for BelfryCAD documents to/from XML format.
    
    The XML format is stored in a zip file with the following structure:
    - document.xml: Main document data
    - metadata.json: Additional metadata (optional)
    """
    
    # XML namespace for BelfryCAD
    NAMESPACE = "http://belfrydw.com/xml/BelfryCAD/1.0"
    
    # Supported units
    SUPPORTED_UNITS = ["mm", "cm", "m", "inches", "ft", "yd"]
    
    def __init__(self):
        """Initialize the serializer."""
        # Register the namespace
        ET.register_namespace('belfry', self.NAMESPACE)
        # Track current unit scale for save/load operations; default to 1.0
        self._current_unit_scale: float = 1.0
    
    # Scaling helpers -----------------------------------------------------
    def _compute_unit_scale(self, units: Optional[str]) -> float:
        """Map document units to a numeric scale aligned with GridInfo.unit_scale.
        Fallback to 1.0 when units are unknown.
        """
        if not units:
            return 1.0
        u = units.lower()
        if u in ("in", "inch", "inches"):
            return 2.54
        if u in ("ft", "foot", "feet"):
            return 12.0 * 2.54
        if u in ("yd", "yard", "yards"):
            return 36.0 * 2.54
        if u in ("mm", "millimeter", "millimeters"):
            return 0.1
        if u in ("cm", "centimeter", "centimeters"):
            return 1.0
        if u in ("m", "meter", "meters"):
            return 100.0
        return 1.0
    
    def _set_scale_from_preferences(self, preferences: Dict[str, Any]):
        """Set current scale based on preferences dict."""
        units = preferences.get('units') if preferences else None
        self._current_unit_scale = self._compute_unit_scale(units)
    
    def _write_point_attrs(self, elem: ET.Element, x: float, y: float):
        """Write x,y to element after dividing by current scale."""
        scale = self._current_unit_scale if self._current_unit_scale else 1.0
        elem.set('x', str(x / scale))
        elem.set('y', str(y / scale))
    
    def _read_point_attrs(self, elem: ET.Element) -> Tuple[float, float]:
        """Read x,y from element and multiply by current scale."""
        scale = self._current_unit_scale if self._current_unit_scale else 1.0
        x = float(elem.get('x', 0)) * scale
        y = float(elem.get('y', 0)) * scale
        return x, y
    
    def _write_scalar(self, elem: ET.Element, name: str, value: float):
        """Write scalar value attribute after dividing by current scale."""
        scale = self._current_unit_scale if self._current_unit_scale else 1.0
        elem.set(name, str(value / scale))
    
    def _read_scalar(self, elem: ET.Element, name: str, default: float = 0.0) -> float:
        """Read scalar value attribute and multiply by current scale."""
        scale = self._current_unit_scale if self._current_unit_scale else 1.0
        raw = float(elem.get(name, default))
        return raw * scale
    
    def save_document(self, document: Document, filepath: str, 
                     preferences: Dict[str, Any] = None) -> bool:
        """
        Save a document to a zip-compressed XML file.
        
        Args:
            document: The document to save
            filepath: Path to save the file
            preferences: Document preferences to include
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create the root XML element
            root = ET.Element(f"{{{self.NAMESPACE}}}belfrycad_document")
            root.set("version", "1.0")
            
            # Establish scale from preferences for write-out
            self._set_scale_from_preferences(preferences or {})
            
            # Add document header with preferences
            self._add_document_header(root, preferences or {})
            
            # Add parameters section
            self._add_parameters_section(root, document)
            
            # Add CAD objects section
            self._add_cad_objects_section(root, document)
            
            # Add constraints section
            self._add_constraints_section(root, document)
            
            # Create zip file
            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add the XML content
                xml_content = ET.tostring(root, encoding='unicode', xml_declaration=True)
                zf.writestr('document.xml', xml_content)
                
                # Add metadata
                metadata = {
                    'version': '1.0',
                    'created_by': 'BelfryCAD',
                    'object_count': len(document.objects),
                    'constraint_count': document.get_constraint_count() if hasattr(document, 'get_constraint_count') else 0
                }
                zf.writestr('metadata.json', json.dumps(metadata, indent=2))
                
            return True
            
        except Exception as e:
            print(f"Error saving document: {e}")
            return False
    
    def load_document(self, filepath: str, document: Document = None) -> Optional[Document]:
        """
        Load a document from a zip-compressed XML file.
        
        Args:
            filepath: Path to the file to load
            document: Optional existing document to populate
            
        Returns:
            The loaded document, or None if failed
        """
        try:
            # Create new document if none provided
            if document is None:
                document = Document()
            
            with zipfile.ZipFile(filepath, 'r') as zf:
                # Read the XML content
                xml_content = zf.read('document.xml').decode('utf-8')
                root = ET.fromstring(xml_content)
                
                # Parse document header (sets preferences)
                self._parse_document_header(root, document)
                # Establish scale using parsed preferences
                prefs = getattr(document, 'preferences', {}) if hasattr(document, 'preferences') else {}
                self._set_scale_from_preferences(prefs)
                
                # Parse parameters
                self._parse_parameters_section(root, document)
                
                # Parse CAD objects
                self._parse_cad_objects_section(root, document)
                
                # Parse constraints
                self._parse_constraints_section(root, document)
                
            return document
            
        except Exception as e:
            print(f"Error loading document: {e}")
            return None
    
    def save_document_xml(self, document: Document, filepath: str, 
                          preferences: Dict[str, Any] = None) -> bool:
        """
        Save a document to an uncompressed XML file (.belcadx format).
        
        Args:
            document: The document to save
            filepath: Path to save the file
            preferences: Document preferences to include
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create the root XML element
            root = ET.Element(f"{{{self.NAMESPACE}}}belfrycad_document")
            root.set("version", "1.0")
            
            # Establish scale from preferences for write-out
            self._set_scale_from_preferences(preferences or {})
            
            # Add document header with preferences
            self._add_document_header(root, preferences or {})
            
            # Add parameters section
            self._add_parameters_section(root, document)
            
            # Add CAD objects section
            self._add_cad_objects_section(root, document)
            
            # Add constraints section
            self._add_constraints_section(root, document)
            
            # Write directly to XML file (no compression)
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)  # Pretty-print the XML
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="utf-8"?>\n')
                tree.write(f, encoding='unicode', xml_declaration=False)
                
            return True
            
        except Exception as e:
            print(f"Error saving document to XML: {e}")
            return False
    
    def load_document_xml(self, filepath: str, document: Document = None) -> Optional[Document]:
        """
        Load a document from an uncompressed XML file (.belcadx format).
        
        Args:
            filepath: Path to the file to load
            document: Optional existing document to populate
            
        Returns:
            The loaded document, or None if failed
        """
        try:
            # Create new document if none provided
            if document is None:
                document = Document()
            
            # Read and parse the XML file directly
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            # Parse document header (sets preferences)
            self._parse_document_header(root, document)
            # Establish scale using parsed preferences
            prefs = getattr(document, 'preferences', {}) if hasattr(document, 'preferences') else {}
            self._set_scale_from_preferences(prefs)
            
            # Parse parameters
            self._parse_parameters_section(root, document)
            
            # Parse CAD objects
            self._parse_cad_objects_section(root, document)
            
            # Parse constraints
            self._parse_constraints_section(root, document)
            
            return document
            
        except Exception as e:
            print(f"Error loading document from XML: {e}")
            return None
    
    def _add_document_header(self, root: ET.Element, preferences: Dict[str, Any]):
        """Add document header with preferences."""
        header = ET.SubElement(root, f"{{{self.NAMESPACE}}}header")
        
        # Document preferences
        prefs = ET.SubElement(header, f"{{{self.NAMESPACE}}}preferences")
        
        # Units
        units = preferences.get('units', 'inches')
        if units in self.SUPPORTED_UNITS:
            prefs.set('units', units)
        
        # Precision
        precision = preferences.get('precision', 3)
        prefs.set('precision', str(precision))
        
        # Fractions vs decimal
        use_fractions = preferences.get('use_fractions', False)
        prefs.set('use_fractions', str(use_fractions).lower())
        
        # Other preferences
        for key, value in preferences.items():
            if key not in ['units', 'precision', 'use_fractions']:
                prefs.set(key, str(value))
    
    def _add_parameters_section(self, root: ET.Element, document: Document):
        """Add parameters section."""
        # Get parameters from document if available
        parameters = getattr(document, 'parameters', {})
        if not parameters:
            return
            
        params_section = ET.SubElement(root, f"{{{self.NAMESPACE}}}parameters")
        
        for name, expression in parameters.items():
            param = ET.SubElement(params_section, f"{{{self.NAMESPACE}}}parameter")
            param.set('name', name)
            param.set('expression', str(expression))
    
    def _add_cad_objects_section(self, root: ET.Element, document: Document):
        """Add CAD objects section."""
        objects_section = ET.SubElement(root, f"{{{self.NAMESPACE}}}objects")
        
        # Add groups first
        for obj_id, obj in document.objects.items():
            if isinstance(obj, GroupCadObject):
                self._add_group_element(objects_section, obj, document)
        
        # Add non-group objects
        for obj_id, obj in document.objects.items():
            if not isinstance(obj, GroupCadObject):
                self._add_cad_object_element(objects_section, obj, document)
    
    def _add_group_element(self, parent: ET.Element, group: GroupCadObject, document: Document):
        """Add a group element to the XML."""
        group_elem = ET.SubElement(parent, f"{{{self.NAMESPACE}}}group")
        
        # Basic properties
        group_elem.set('id', group.object_id)
        group_elem.set('name', group.name or '')
        group_elem.set('color', group.color or 'black')
        if group.line_width is not None:
            # scale line width by dividing by unit scale
            lw_elem_val = (group.line_width / (self._current_unit_scale or 1.0))
            group_elem.set('line_width', str(lw_elem_val))
        group_elem.set('visible', str(group.visible).lower())
        group_elem.set('locked', str(group.locked).lower())
        
        # Parent reference
        if group.parent_id:
            group_elem.set('parent', group.parent_id)
        
        # Add children
        for child_id in group.children:
            child_obj = document.get_object(child_id)
            if child_obj:
                if isinstance(child_obj, GroupCadObject):
                    self._add_group_element(group_elem, child_obj, document)
                else:
                    self._add_cad_object_element(group_elem, child_obj, document)
    
    def _add_cad_object_element(self, parent: ET.Element, obj: CadObject, document: Document):
        """Add a CAD object element to the XML."""
        # Determine object type
        obj_type = type(obj).__name__.replace('CadObject', '').lower()
        
        # Create base element for CAD object with common attributes
        obj_elem = ET.SubElement(parent, f"{{{self.NAMESPACE}}}{obj_type}")
        obj_elem.set('id', obj.object_id)
        obj_elem.set('name', obj.name or '')
        obj_elem.set('color', obj.color or 'black')
        if obj.line_width is not None:
            lw_elem_val = (obj.line_width / (self._current_unit_scale or 1.0))
            obj_elem.set('line_width', str(lw_elem_val))
        obj_elem.set('visible', str(obj.visible).lower())
        obj_elem.set('locked', str(obj.locked).lower())
        
        # Parent reference
        if obj.parent_id:
            obj_elem.set('parent', obj.parent_id)
        
        # Object-specific data
        self._add_object_data(obj_elem, obj)
    
    def _add_object_data(self, obj_elem: ET.Element, obj: CadObject):
        """Add object-specific data to the XML element."""
        obj_type = type(obj).__name__
        
        if isinstance(obj, LineCadObject):
            self._add_line_data(obj_elem, obj)
        elif isinstance(obj, CircleCadObject):
            self._add_circle_data(obj_elem, obj)
        elif isinstance(obj, ArcCadObject):
            self._add_arc_data(obj_elem, obj)
        elif isinstance(obj, EllipseCadObject):
            self._add_ellipse_data(obj_elem, obj)
        elif isinstance(obj, CubicBezierCadObject):
            self._add_bezier_data(obj_elem, obj)
        elif isinstance(obj, GearCadObject):
            self._add_gear_data(obj_elem, obj)
    
    def _add_line_data(self, obj_elem: ET.Element, line: LineCadObject):
        """Add line-specific data."""
        # Start point
        start_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}start_point")
        self._write_point_attrs(start_elem, line.start_point.x, line.start_point.y)
        
        # End point
        end_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}end_point")
        self._write_point_attrs(end_elem, line.end_point.x, line.end_point.y)
    
    def _add_circle_data(self, obj_elem: ET.Element, circle: CircleCadObject):
        """Add circle-specific data."""
        # Center point
        center_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}center_point")
        self._write_point_attrs(center_elem, circle.center_point.x, circle.center_point.y)
        
        # Radius
        radius_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}radius")
        self._write_scalar(radius_elem, 'value', circle.radius)
    
    def _add_arc_data(self, obj_elem: ET.Element, arc: ArcCadObject):
        """Add arc-specific data."""
        # Center point
        center_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}center_point")
        self._write_point_attrs(center_elem, arc.center_point.x, arc.center_point.y)
        
        # Radius
        radius_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}radius")
        self._write_scalar(radius_elem, "value", arc.radius)
        
        # Start angle in degrees
        start_angle_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}start_angle")
        start_angle_degrees = math.degrees(arc.start_angle)
        start_angle_elem.set("value", str(start_angle_degrees))
        
        # Span angle in degrees
        span_angle_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}span_angle")
        span_angle_degrees = math.degrees(arc.span_angle)
        span_angle_elem.set("value", str(span_angle_degrees))
    
    def _add_ellipse_data(self, obj_elem: ET.Element, ellipse: EllipseCadObject):
        """Add ellipse-specific data."""
        # Center point
        center_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}center_point")
        self._write_point_attrs(center_elem, ellipse.center_point.x, ellipse.center_point.y)
        
        # Radius1 (semi-major axis) - distance from center to major axis point
        radius1_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}radius1")
        radius1 = ellipse.center_point.distance_to(ellipse.major_axis_point)
        self._write_scalar(radius1_elem, "value", radius1)
        
        # Radius2 (semi-minor axis) - distance from center to minor axis point
        radius2_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}radius2")
        radius2 = ellipse.center_point.distance_to(ellipse.minor_axis_point)
        self._write_scalar(radius2_elem, "value", radius2)
        
        # Rotation angle in degrees (counter-clockwise)
        rotation_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}rotation_angle")
        rotation_degrees = math.degrees(ellipse.rotation)
        rotation_elem.set("value", str(rotation_degrees))
    
    def _add_bezier_data(self, obj_elem: ET.Element, bezier: CubicBezierCadObject):
        """Add bezier-specific data."""
        # Control points
        for i, point in enumerate(bezier.points):
            point_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}control_point")
            point_elem.set('index', str(i))
            self._write_point_attrs(point_elem, point.x, point.y)
    
    def _add_gear_data(self, obj_elem: ET.Element, gear: GearCadObject):
        """Add gear-specific data."""
        # Center point
        center_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}center_point")
        self._write_point_attrs(center_elem, gear.center_point.x, gear.center_point.y)
        
        # Pitch radius
        pitch_radius_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}pitch_radius")
        self._write_scalar(pitch_radius_elem, 'value', gear.pitch_radius)
        
        # Number of teeth
        teeth_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}num_teeth")
        teeth_elem.set('value', str(gear.num_teeth))
        
        # Pressure angle (unitless)
        pressure_angle_elem = ET.SubElement(obj_elem, f"{{{self.NAMESPACE}}}pressure_angle")
        pressure_angle_elem.set('value', str(gear.pressure_angle))
    
    def _add_constraints_section(self, root: ET.Element, document: Document):
        """Add constraints section."""
        if not hasattr(document, 'constraints_manager') or not document.constraints_manager.has_constraints():
            return
            
        constraints_section = ET.SubElement(root, f"{{{self.NAMESPACE}}}constraints")
        
        # Get constraints from the manager
        manager = document.constraints_manager
        for constraint_id, constraint in manager.constraints.items():
            constraint_elem = ET.SubElement(constraints_section, f"{{{self.NAMESPACE}}}constraint")
            constraint_elem.set('id', constraint_id)
            constraint_elem.set('type', type(constraint).__name__)
            
            # Add constrainable properties involved in this constraint
            if hasattr(constraint, 'constrainable1') and hasattr(constraint, 'constrainable2'):
                # Format: object.property (e.g., "line1.start_point")
                constrainable1 = constraint.constrainable1
                constrainable2 = constraint.constrainable2
                
                if hasattr(constrainable1, 'object_id') and hasattr(constrainable1, 'property_name'):
                    constraint_elem.set('constrainable1', f"{constrainable1.object_id}.{constrainable1.property_name}")
                if hasattr(constrainable2, 'object_id') and hasattr(constrainable2, 'property_name'):
                    constraint_elem.set('constrainable2', f"{constrainable2.object_id}.{constrainable2.property_name}")
            
            # Add constraint-specific parameters
            if hasattr(constraint, 'parameters'):
                for param_name, param_value in constraint.parameters.items():
                    param_elem = ET.SubElement(constraint_elem, f"{{{self.NAMESPACE}}}parameter")
                    param_elem.set('name', param_name)
                    param_elem.set('value', str(param_value))
    
    def _parse_document_header(self, root: ET.Element, document: Document):
        """Parse document header and preferences."""
        header = root.find(f"{{{self.NAMESPACE}}}header")
        if header is None:
            return
            
        prefs = header.find(f"{{{self.NAMESPACE}}}preferences")
        if prefs is not None:
            # Store preferences in document
            document.preferences = {}
            for key, value in prefs.attrib.items():
                if key in ['use_fractions', 'grid_visible', 'show_rulers']:
                    document.preferences[key] = value.lower() == 'true'
                elif key == 'precision':
                    document.preferences[key] = int(value)
                else:
                    document.preferences[key] = value
    
    def _parse_parameters_section(self, root: ET.Element, document: Document):
        """Parse parameters section."""
        params_section = root.find(f"{{{self.NAMESPACE}}}parameters")
        if params_section is None:
            return
            
        # Create CadExpression for parameters
        expressions = {}
        for param_elem in params_section.findall(f"{{{self.NAMESPACE}}}parameter"):
            name = param_elem.get('name')
            expression = param_elem.get('expression')
            if name and expression:
                expressions[name] = expression
        
        # Store parameters in document
        document.parameters = expressions
        document.cad_expression = CadExpression(expressions)
    
    def _parse_cad_objects_section(self, root: ET.Element, document: Document):
        """Parse CAD objects section."""
        objects_section = root.find(f"{{{self.NAMESPACE}}}objects")
        if objects_section is None:
            return
        
        # Parse all top-level objects
        for obj_elem in objects_section:
            self._parse_cad_object_element(obj_elem, document, parent_group_id=None)
    
    def _parse_cad_object_element(self, obj_elem: ET.Element, document: Document, parent_group_id: Optional[str] = None):
        """Parse a CAD object element, handling grouping by nested structure or parent attribute."""
        tag = obj_elem.tag.replace(f"{{{self.NAMESPACE}}}", "")
        
        # Get basic properties
        obj_id = obj_elem.get('id')
        name = obj_elem.get('name', '')
        color = obj_elem.get('color', 'black')
        line_width_str = obj_elem.get('line_width')
        if line_width_str:
            line_width = float(line_width_str) * (self._current_unit_scale or 1.0)
        else:
            line_width = None
        visible = obj_elem.get('visible', 'true').lower() == 'true'
        locked = obj_elem.get('locked', 'false').lower() == 'true'
        parent_id_attr = obj_elem.get('parent')
        
        # If not explicitly set, use the nesting parent group id
        parent_id = parent_id_attr if parent_id_attr else parent_group_id
        
        # Create object based on type (do not recurse here)
        if tag == 'group':
            obj = self._create_group_object(document, obj_elem, name, color, line_width)
        else:
            obj = self._create_cad_object(document, tag, obj_elem, name, color, line_width)
        
        if obj:
            # Set properties
            obj.visible = visible
            obj.locked = locked
            if parent_id:
                obj.parent_id = parent_id
            
            # Set the name directly to avoid Document's name generation
            obj._name = name
            
            # Preserve the original object ID
            obj.object_id = obj_id
            
            # Add to document
            document.objects[obj_id] = obj
            
            # Handle grouping and root groups
            if parent_id and parent_id in document.objects:
                parent = document.objects[parent_id]
                if isinstance(parent, GroupCadObject):
                    parent.add_child(obj_id)
            else:
                # No parent; if this is a group, mark as root group
                if isinstance(obj, GroupCadObject):
                    document.root_groups.add(obj_id)
            
            # If this is a group, parse its children with this as parent
            if tag == 'group':
                for child_elem in obj_elem:
                    self._parse_cad_object_element(child_elem, document, parent_group_id=obj_id)
    
    def _create_group_object(self, document: Document, obj_elem: ET.Element, 
                           name: str, color: str, line_width: Optional[float]) -> GroupCadObject:
        """Create a group object from XML. Children are handled by _parse_cad_object_element."""
        group = GroupCadObject(document, name, color, line_width)
        return group
    
    def _create_cad_object(self, document: Document, obj_type: str, obj_elem: ET.Element,
                          name: str, color: str, line_width: Optional[float]) -> Optional[CadObject]:
        """Create a CAD object from XML based on type."""
        try:
            if obj_type == 'line':
                return self._create_line_object(document, obj_elem, name, color, line_width)
            elif obj_type == 'circle':
                return self._create_circle_object(document, obj_elem, name, color, line_width)
            elif obj_type == 'arc':
                return self._create_arc_object(document, obj_elem, name, color, line_width)
            elif obj_type == 'ellipse':
                return self._create_ellipse_object(document, obj_elem, name, color, line_width)
            elif obj_type == 'cubicbezier':
                return self._create_bezier_object(document, obj_elem, name, color, line_width)
            elif obj_type == 'gear':
                return self._create_gear_object(document, obj_elem, name, color, line_width)
            else:
                print(f"Unknown object type: {obj_type}")
                return None
        except Exception as e:
            print(f"Error creating {obj_type} object: {e}")
            return None
    
    def _create_line_object(self, document: Document, obj_elem: ET.Element,
                           name: str, color: str, line_width: Optional[float]) -> LineCadObject:
        """Create a line object from XML."""
        start_elem = obj_elem.find(f"{{{self.NAMESPACE}}}start_point")
        end_elem = obj_elem.find(f"{{{self.NAMESPACE}}}end_point")
        
        if start_elem is None or end_elem is None:
            raise ValueError("Line object missing start or end point")
        
        sx, sy = self._read_point_attrs(start_elem)
        ex, ey = self._read_point_attrs(end_elem)
        
        start_point = Point2D(sx, sy)
        end_point = Point2D(ex, ey)
        
        return LineCadObject(document, start_point, end_point, color, line_width)
    
    def _create_circle_object(self, document: Document, obj_elem: ET.Element,
                             name: str, color: str, line_width: Optional[float]) -> CircleCadObject:
        """Create a circle object from XML."""
        center_elem = obj_elem.find(f"{{{self.NAMESPACE}}}center_point")
        radius_elem = obj_elem.find(f"{{{self.NAMESPACE}}}radius")
        
        if center_elem is None or radius_elem is None:
            raise ValueError("Circle object missing center point or radius")
        
        cx, cy = self._read_point_attrs(center_elem)
        radius = self._read_scalar(radius_elem, 'value', 0)
        
        center_point = Point2D(cx, cy)
        perimeter_point = center_point + Point2D(radius, 0)  # Point on perimeter
        
        return CircleCadObject(document, center_point, perimeter_point, color, line_width)
    
    def _create_arc_object(self, document: Document, obj_elem: ET.Element,
                          name: str, color: str, line_width: Optional[float]) -> ArcCadObject:
        """Create an arc object from XML."""
        center_elem = obj_elem.find(f"{{{self.NAMESPACE}}}center_point")
        radius_elem = obj_elem.find(f"{{{self.NAMESPACE}}}radius")
        start_angle_elem = obj_elem.find(f"{{{self.NAMESPACE}}}start_angle")
        span_angle_elem = obj_elem.find(f"{{{self.NAMESPACE}}}span_angle")
        
        if center_elem is None or radius_elem is None or start_angle_elem is None or span_angle_elem is None:
            raise ValueError("Arc object missing required elements")
        
        cx, cy = self._read_point_attrs(center_elem)
        radius = self._read_scalar(radius_elem, "value")
        start_angle_degrees = float(start_angle_elem.get("value", "0"))
        span_angle_degrees = float(span_angle_elem.get("value", "90")) # Default to 90 degrees if not present
        
        start_angle_radians = math.radians(start_angle_degrees)
        span_angle_radians = math.radians(span_angle_degrees)
        
        center_point = Point2D(cx, cy)
        
        # Calculate start and end points from center, radius, and angles
        start_point = center_point + Point2D(radius * math.cos(start_angle_radians), 
                                             radius * math.sin(start_angle_radians))
        end_angle_radians = start_angle_radians + span_angle_radians
        end_point = center_point + Point2D(radius * math.cos(end_angle_radians), 
                                           radius * math.sin(end_angle_radians))
        
        return ArcCadObject(document, center_point, start_point, end_point, color, line_width)
    
    def _create_ellipse_object(self, document: Document, obj_elem: ET.Element,
                              name: str, color: str, line_width: Optional[float]) -> EllipseCadObject:
        """Create an ellipse object from XML."""
        center_elem = obj_elem.find(f"{{{self.NAMESPACE}}}center_point")
        radius1_elem = obj_elem.find(f"{{{self.NAMESPACE}}}radius1")
        radius2_elem = obj_elem.find(f"{{{self.NAMESPACE}}}radius2")
        rotation_elem = obj_elem.find(f"{{{self.NAMESPACE}}}rotation_angle")
        
        if center_elem is None or radius1_elem is None or radius2_elem is None:
            raise ValueError("Ellipse object missing required elements")
        
        # Read center point
        cx, cy = self._read_point_attrs(center_elem)
        center_point = Point2D(cx, cy)
        
        # Read radii (semi-axes)
        radius1 = self._read_scalar(radius1_elem, "value")
        radius2 = self._read_scalar(radius2_elem, "value")
        
        # Read rotation angle (default to 0 if not present for backward compatibility)
        rotation_degrees = 0.0
        if rotation_elem is not None:
            rotation_degrees = float(rotation_elem.get("value", "0"))
        rotation_radians = math.radians(rotation_degrees)
        
        # Create major and minor axis points based on center, radii, and rotation
        major_axis_point = center_point + Point2D(radius1 * math.cos(rotation_radians), 
                                                  radius1 * math.sin(rotation_radians))
        minor_axis_point = center_point + Point2D(radius2 * math.cos(rotation_radians + math.pi/2), 
                                                  radius2 * math.sin(rotation_radians + math.pi/2))
        
        return EllipseCadObject(document, center_point, major_axis_point, minor_axis_point, color, line_width)
    
    def _create_bezier_object(self, document: Document, obj_elem: ET.Element,
                             name: str, color: str, line_width: Optional[float]) -> CubicBezierCadObject:
        """Create a bezier object from XML."""
        points: List[Point2D] = []
        for point_elem in obj_elem.findall(f"{{{self.NAMESPACE}}}control_point"):
            x, y = self._read_point_attrs(point_elem)
            points.append(Point2D(x, y))
        
        if len(points) < 4:
            raise ValueError("Bezier object must have at least 4 control points")
        
        return CubicBezierCadObject(document, points, color, line_width)
    
    def _create_gear_object(self, document: Document, obj_elem: ET.Element,
                           name: str, color: str, line_width: Optional[float]) -> GearCadObject:
        """Create a gear object from XML."""
        center_elem = obj_elem.find(f"{{{self.NAMESPACE}}}center_point")
        pitch_radius_elem = obj_elem.find(f"{{{self.NAMESPACE}}}pitch_radius")
        teeth_elem = obj_elem.find(f"{{{self.NAMESPACE}}}num_teeth")
        pressure_angle_elem = obj_elem.find(f"{{{self.NAMESPACE}}}pressure_angle")
        
        if center_elem is None or pitch_radius_elem is None or teeth_elem is None or pressure_angle_elem is None:
            raise ValueError("Gear object missing required elements")
        
        cx, cy = self._read_point_attrs(center_elem)
        pitch_radius = self._read_scalar(pitch_radius_elem, 'value', 0)
        num_teeth = int(teeth_elem.get('value', 0))
        pressure_angle = float(pressure_angle_elem.get('value', 20.0))
        
        center_point = Point2D(cx, cy)
        
        return GearCadObject(document, center_point, pitch_radius, num_teeth, pressure_angle, color, line_width)
    
    def _parse_constraints_section(self, root: ET.Element, document: Document):
        """Parse constraints section."""
        constraints_section = root.find(f"{{{self.NAMESPACE}}}constraints")
        if constraints_section is None:
            return
            
        # Parse constraints and add to document
        for constraint_elem in constraints_section.findall(f"{{{self.NAMESPACE}}}constraint"):
            constraint_id = constraint_elem.get('id')
            constraint_type = constraint_elem.get('type')
            constrainable1 = constraint_elem.get('constrainable1')  # e.g., "line1.start_point"
            constrainable2 = constraint_elem.get('constrainable2')  # e.g., "circle2.center_point"
            
            # Parse constraint parameters
            parameters = {}
            for param_elem in constraint_elem.findall(f"{{{self.NAMESPACE}}}parameter"):
                param_name = param_elem.get('name')
                param_value = param_elem.get('value')
                if param_name and param_value:
                    # Try to convert to appropriate type
                    try:
                        if '.' in param_value:
                            parameters[param_name] = float(param_value)
                        else:
                            parameters[param_name] = param_value
                    except ValueError:
                        parameters[param_name] = param_value
            
            if constraint_id and constrainable1 and constrainable2:
                # Note: Full constraint reconstruction would require more complex logic
                # based on the specific constraint types and their parameters
                print(f"Found constraint {constraint_id} of type {constraint_type}")
                print(f"  Between: {constrainable1} and {constrainable2}")
                if parameters:
                    print(f"  Parameters: {parameters}")


# Convenience functions
def save_belfrycad_document(document: Document, filepath: str, 
                           preferences: Dict[str, Any] = None) -> bool:
    """Save a BelfryCAD document to a zip-compressed XML file."""
    serializer = BelfryCADXMLSerializer()
    return serializer.save_document(document, filepath, preferences)


def load_belfrycad_document(filepath: str, document: Document = None) -> Optional[Document]:
    """Load a BelfryCAD document from a zip-compressed XML file."""
    serializer = BelfryCADXMLSerializer()
    return serializer.load_document(filepath, document)


def save_belfrycad_xml_document(document: Document, filepath: str, 
                               preferences: Dict[str, Any] = None) -> bool:
    """Save a BelfryCAD document to an uncompressed XML file (.belcadx format)."""
    serializer = BelfryCADXMLSerializer()
    return serializer.save_document_xml(document, filepath, preferences)


def load_belfrycad_xml_document(filepath: str, document: Document = None) -> Optional[Document]:
    """Load a BelfryCAD document from an uncompressed XML file (.belcadx format)."""
    serializer = BelfryCADXMLSerializer()
    return serializer.load_document_xml(filepath, document) 