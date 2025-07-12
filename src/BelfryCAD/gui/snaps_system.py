"""
Snaps System for BelfryCAD

This module provides a comprehensive snapping system that can snap to:
- Grid points
- Control points of CAD items
- Quadrant points of circles
- Tangent points on circles
- Endpoints, midpoints, centers, etc.

The system takes a mouse position and recent construction points,
then returns the closest snap point based on enabled snap types.
"""

import math
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum
from dataclasses import dataclass

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPainterPath

from .views.widgets.cad_scene import CadScene
from .grid_info import GridInfo
from .panes.snaps_pane import snaps_pane_info
from .views.graphics_items.cad_item import CadItem
from .views.graphics_items.control_points import ControlPoint


class SnapType(Enum):
    """Types of snaps available in the system."""
    GRID = "grid"
    CONTROLPOINTS = "controlpoints"
    MIDPOINT = "midpoints"
    QUADRANT = "quadrants"
    TANGENT = "tangents"
    PERPENDICULAR = "perpendicular"
    INTERSECTION = "intersect"
    ANGLES = "angles"
    CONTOURS = "contours"


@dataclass
class SnapPoint:
    """Represents a snap point with metadata."""
    point: QPointF
    snap_type: SnapType
    distance: float
    source_item: Optional[CadItem] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SnapsSystem:
    """Main snaps system that handles all snapping logic."""
    
    def __init__(self, scene: CadScene, grid_info: GridInfo):
        self.scene = scene
        self.grid_info = grid_info
        self.snap_tolerance = 15.0  # pixels
        self._snap_cache = {}  # Cache for expensive calculations
        
    def get_snap_point(
            self, mouse_pos: QPointF, 
            recent_points: Optional[List[QPointF]] = None,
            exclude_cps: Optional[List[ControlPoint]] = None
    ) -> Optional[QPointF]:
        """
        Get the closest snap point based on current snap settings.
        
        Args:
            mouse_pos: Current mouse position in scene coordinates
            recent_points: List of recent construction points (for tangent calculations)
            exclude_cps: List of ControlPoint objects to exclude from control point snapping
            
        Returns:
            The closest snap point, or None if no snap is found
        """
        if recent_points is None:
            recent_points = []
            
        # Get enabled snap types
        enabled_snaps = self._get_enabled_snaps()
        if not enabled_snaps:
            return mouse_pos
            
        # Find all possible snap points
        snap_points = []
        
        for snap_type in enabled_snaps:
            if snap_type == SnapType.GRID:
                snap_points.extend(self._find_grid_snaps(mouse_pos))
            elif snap_type == SnapType.CONTROLPOINTS:
                snap_points.extend(self._find_control_point_snaps(mouse_pos, exclude_cps=exclude_cps))
            elif snap_type == SnapType.MIDPOINT:
                snap_points.extend(self._find_midpoint_snaps(mouse_pos))
            elif snap_type == SnapType.QUADRANT:
                snap_points.extend(self._find_quadrant_snaps(mouse_pos))
            elif snap_type == SnapType.TANGENT:
                if recent_points:
                    snap_points.extend(self._find_tangent_snaps(mouse_pos, recent_points))
            elif snap_type == SnapType.PERPENDICULAR:
                if recent_points:
                    snap_points.extend(self._find_perpendicular_snaps(mouse_pos, recent_points))
            elif snap_type == SnapType.INTERSECTION:
                snap_points.extend(self._find_intersection_snaps(mouse_pos))
            elif snap_type == SnapType.CONTOURS:
                snap_points.extend(self._find_nearest_snaps(mouse_pos))
            elif snap_type == SnapType.ANGLES:
                snap_points.extend(self._find_angles_snaps(mouse_pos, recent_points))
        
        # Find the closest snap point
        scaling = self._get_current_scaling()
        if snap_points:
            closest = min(snap_points, key=lambda sp: sp.distance)
            if closest.distance <= self.snap_tolerance / scaling:
                return closest.point
                
        return mouse_pos
    
    def _get_enabled_snaps(self) -> List[SnapType]:
        """Get list of currently enabled snap types."""
        enabled_snaps = []
        
        # Check if all snaps are enabled
        if not snaps_pane_info.snap_all:
            return []
        
        # Check individual snap types
        for snap_type in SnapType:
            if snaps_pane_info.snap_states.get(snap_type.value, False):
                enabled_snaps.append(snap_type)
        return enabled_snaps
    
    def _find_grid_snaps(self, mouse_pos: QPointF) -> List[SnapPoint]:
        """Find grid snap points near the mouse position."""
        snap_points = []
        
        # Get current grid spacing from grid info
        scaling = self._get_current_scaling()
        spacings, _ = self.grid_info.get_relevant_spacings(scaling)
        grid_spacing = spacings[-1] if spacings else 1.0
        
        # Find the nearest grid point
        grid_x = round(mouse_pos.x() / grid_spacing) * grid_spacing
        grid_y = round(mouse_pos.y() / grid_spacing) * grid_spacing
        grid_point = QPointF(grid_x, grid_y)
        
        distance = math.sqrt((mouse_pos.x() - grid_point.x())**2 + 
                           (mouse_pos.y() - grid_point.y())**2)
        
        snap_points.append(SnapPoint(
            point=grid_point,
            snap_type=SnapType.GRID,
            distance=distance
        ))
        
        return snap_points
    
    def _get_cad_items_near_point(self, mouse_pos: QPointF) -> List[CadItem]:
        """Get CAD items within snap tolerance distance of the mouse position."""
        # Create a rectangle around the mouse position with snap tolerance
        tolerance = self.snap_tolerance
        search_rect = QRectF(
            mouse_pos.x() - tolerance,
            mouse_pos.y() - tolerance,
            tolerance * 2,
            tolerance * 2
        )
        
        # Get items within the search rectangle
        nearby_items = self.scene.items(search_rect)
        
        # Filter to only CAD items
        cad_items = [item for item in nearby_items if isinstance(item, CadItem)]
        
        return cad_items

    def _find_control_point_snaps(
            self,
            mouse_pos: QPointF,
            exclude_cps: Optional[List[ControlPoint]] = None
    ) -> List[SnapPoint]:
        """Find control point snap points near the mouse position."""
        snap_points = []
        
        # Get only CAD items within snap tolerance distance
        cad_items = self._get_cad_items_near_point(mouse_pos)
        
        for item in cad_items:
            # Get control points for this item
            control_points = self._get_item_control_points(item, exclude_cps=exclude_cps)
            for cp_pos in control_points:
                distance = math.sqrt((mouse_pos.x() - cp_pos.x())**2 + 
                                   (mouse_pos.y() - cp_pos.y())**2)
                
                snap_points.append(SnapPoint(
                    point=cp_pos,
                    snap_type=SnapType.CONTROLPOINTS,
                    distance=distance,
                    source_item=item
                ))
        
        return snap_points
    
    def _get_item_control_points(
            self,
            item: CadItem,
            exclude_cps: Optional[List['ControlPoint']] = None
    ) -> List[QPointF]:
        """Get control point positions for a CAD item using getControlPoints()."""
        control_points = []
        
        # Use the getControlPoints() method if available
        if hasattr(item, 'getControlPoints'):
            try:
                # Get control points (already in scene coordinates)
                control_points = item.getControlPoints(exclude_cps=exclude_cps)
                    
            except Exception as e:
                print(f"Error getting control points for {type(item).__name__}: {e}")
        
        return control_points
    
    def _find_midpoint_snaps(self, mouse_pos: QPointF) -> List[SnapPoint]:
        """Find midpoint snap points near the mouse position."""
        snap_points = []
        
        # Get only CAD items within snap tolerance distance
        cad_items = self._get_cad_items_near_point(mouse_pos)
        
        for item in cad_items:
            midpoints = self._get_item_midpoints(item)
            for midpoint in midpoints:
                distance = math.sqrt((mouse_pos.x() - midpoint.x())**2 + 
                                   (mouse_pos.y() - midpoint.y())**2)
                
                snap_points.append(SnapPoint(
                    point=midpoint,
                    snap_type=SnapType.MIDPOINT,
                    distance=distance,
                    source_item=item
                ))
        
        return snap_points
    
    def _get_item_midpoints(self, item: CadItem) -> List[QPointF]:
        """Get midpoint positions for a CAD item."""
        midpoints = []
        
        if hasattr(item, '_start_point') and hasattr(item, '_end_point'):
            # Line-like items
            start_point = getattr(item, '_start_point', None)
            end_point = getattr(item, '_end_point', None)
            if start_point and end_point:
                start_scene = item.mapToScene(start_point)
                end_scene = item.mapToScene(end_point)
                midpoint = QPointF((start_scene.x() + end_scene.x()) / 2,
                                 (start_scene.y() + end_scene.y()) / 2)
                midpoints.append(midpoint)
        elif hasattr(item, '_points'):
            # Polyline-like items - find midpoints of segments
            points = getattr(item, '_points', [])
            if len(points) >= 2:
                for i in range(len(points) - 1):
                    p1_scene = item.mapToScene(points[i])
                    p2_scene = item.mapToScene(points[i + 1])
                    midpoint = QPointF((p1_scene.x() + p2_scene.x()) / 2,
                                     (p1_scene.y() + p2_scene.y()) / 2)
                    midpoints.append(midpoint)
        
        return midpoints

    def _find_quadrant_snaps(self, mouse_pos: QPointF) -> List[SnapPoint]:
        """Find quadrant snap points near the mouse position."""
        snap_points = []
        
        # Get only CAD items within snap tolerance distance
        cad_items = self._get_cad_items_near_point(mouse_pos)
        
        for item in cad_items:
            quadrants = self._get_item_quadrants(item)
            for quadrant in quadrants:
                distance = math.sqrt((mouse_pos.x() - quadrant.x())**2 + 
                                   (mouse_pos.y() - quadrant.y())**2)
                
                snap_points.append(SnapPoint(
                    point=quadrant,
                    snap_type=SnapType.QUADRANT,
                    distance=distance,
                    source_item=item
                ))
        
        return snap_points
    
    def _get_item_quadrants(self, item: CadItem) -> List[QPointF]:
        """Get quadrant positions for a CAD item."""
        quadrants = []
        
                # Only circles have quadrants
        if hasattr(item, '_center_point') and hasattr(item, 'radius'):
            center_point = getattr(item, '_center_point', None)
            radius = getattr(item, 'radius', None)
            if center_point and radius is not None:
                # Calculate quadrant points (top, right, bottom, left)
                quadrants = [
                    QPointF(center_point.x(), center_point.y() + radius),  # Top
                    QPointF(center_point.x() + radius, center_point.y()),  # Right
                    QPointF(center_point.x(), center_point.y() - radius),  # Bottom
                    QPointF(center_point.x() - radius, center_point.y())   # Left
                ]
            else:
                quadrants = []
        else:
            quadrants = []
        
        return quadrants
    
    def _find_tangent_snaps(self, mouse_pos: QPointF, 
                           recent_points: List[QPointF]) -> List[SnapPoint]:
        """Find tangent snap points near the mouse position."""
        snap_points = []
        
        if not recent_points:
            return snap_points
        
        # Use the most recent point as the reference point
        ref_point = recent_points[-1]
        
        # Get only CAD items within snap tolerance distance
        cad_items = self._get_cad_items_near_point(mouse_pos)
        
        for item in cad_items:
            tangent_points = self._get_item_tangent_points(item, ref_point)
            for tangent_point in tangent_points:
                distance = math.sqrt((mouse_pos.x() - tangent_point.x())**2 + 
                                   (mouse_pos.y() - tangent_point.y())**2)
                
                snap_points.append(SnapPoint(
                    point=tangent_point,
                    snap_type=SnapType.TANGENT,
                    distance=distance,
                    source_item=item,
                    metadata={'reference_point': ref_point}
                ))
        
        return snap_points
    
    def _get_item_tangent_points(self, item: CadItem, 
                                ref_point: QPointF) -> List[QPointF]:
        """Get tangent points for a CAD item from a reference point."""
        tangent_points = []
        
        # Only circles have tangent points
        if hasattr(item, '_center_point') and hasattr(item, 'radius'):
            center_point = item._center_point # type: ignore
            radius = item.radius # type: ignore
            
            # Calculate distance from reference point to center
            delta = ref_point - center_point
            distance_to_center = delta.length()
            
            # Only calculate tangents if reference point is outside the circle
            if distance_to_center > radius:
                # Calculate tangent points using geometric construction
                distance_to_tangent = (distance_to_center**2 - radius**2)**0.5
                ref_angle = math.atan2(delta.y(), delta.x())
                delta_angle = math.asin(radius / distance_to_center)
                tangent1_angle = ref_angle + delta_angle
                tangent2_angle = ref_angle - delta_angle
                tangent1_point = ref_point + distance_to_tangent * QPointF(
                    math.cos(tangent1_angle), math.sin(tangent1_angle))
                tangent2_point = ref_point + distance_to_tangent * QPointF(
                    math.cos(tangent2_angle), math.sin(tangent2_angle))
                tangent_points = [tangent1_point, tangent2_point]
                
        return tangent_points
    
    def _find_perpendicular_snaps(
            self,
            mouse_pos: QPointF, 
            recent_points: List[QPointF]
    ) -> List[SnapPoint]:
        """Find perpendicular snap points near the mouse position."""
        snap_points = []
        
        if len(recent_points) < 1:
            return snap_points
        
        # Use the last recent point as the reference point
        ref_point = recent_points[-1]
        
        # Get only CAD items within snap tolerance distance
        cad_items = self._get_cad_items_near_point(mouse_pos)
        
        for item in cad_items:
            perp_points = self._get_item_perpendicular_points(item, ref_point)
            for perp_point in perp_points:
                distance = math.sqrt((mouse_pos.x() - perp_point.x())**2 + 
                                   (mouse_pos.y() - perp_point.y())**2)
                
                snap_points.append(SnapPoint(
                    point=perp_point,
                    snap_type=SnapType.PERPENDICULAR,
                    distance=distance,
                    source_item=item,
                    metadata={'ref_point': ref_point}
                ))
        
        return snap_points
    
    def _get_item_perpendicular_points(
            self,
            item: CadItem, 
            ref_point: QPointF
    ) -> List[QPointF]:
        """Get perpendicular points for a CAD item from a reference point."""
        perp_points = []
        
        
        # For line-like items, find perpendicular points
        if hasattr(item, '_start_point') and hasattr(item, '_end_point'):
            start_point = getattr(item, '_start_point', None)
            end_point = getattr(item, '_end_point', None)
            
            if start_point is not None and end_point is not None:
                # Calculate line segment vector
                line_vec = end_point - start_point
                line_length_sq = line_vec.lengthSquared()
                
                if line_length_sq > 0:
                    # Calculate the perpendicular projection of ref_point onto the line
                    # Vector from start to reference point
                    ref_vec = ref_point - start_point
                    
                    # Project reference vector onto line vector
                    t = (ref_vec.x()*line_vec.x() + ref_vec.y()*line_vec.y()) / line_length_sq
                    
                    if 0 <= t <= 1:                    
                        # Calculate the perpendicular point on the line segment
                        perp_point = start_point + t * line_vec
                        
                        # Convert back to scene coordinates
                        perp_points.append(perp_point)
        
        # For polyline-like items, find perpendicular points on each segment
        elif hasattr(item, '_points') and len(getattr(item, '_points', [])) >= 2:
            points = getattr(item, '_points', [])
            for i in range(len(points) - 1):
                start_point = points[i]
                end_point = points[i + 1]
                
                # Calculate line segment vector
                line_vec = end_point - start_point
                line_length_sq = line_vec.lengthSquared()
                
                if line_length_sq > 0:
                    # Calculate the perpendicular projection of ref_point onto the line
                    # Vector from start to reference point
                    ref_vec = ref_point - start_point
                    
                    # Project reference vector onto line vector
                    t = (ref_vec.x()*line_vec.x() + ref_vec.y()*line_vec.y()) / line_length_sq
                    
                    if 0 <= t <= 1:
                        # Calculate the perpendicular point on the line segment
                        perp_point = start_point + t * line_vec
                        perp_points.append(perp_point)
        
        return perp_points
    
    def _find_intersection_snaps(self, mouse_pos: QPointF) -> List[SnapPoint]:
        """Find intersection snap points near the mouse position."""
        snap_points = []
        
        # This is a simplified implementation
        # In a full implementation, you'd calculate actual intersections
        # between all pairs of line-like items
        
        return snap_points
    
    def _find_nearest_snaps(self, mouse_pos: QPointF) -> List[SnapPoint]:
        """Find nearest snap points near the mouse position."""
        snap_points = []
        
        # Get only CAD items within snap tolerance distance
        cad_items = self._get_cad_items_near_point(mouse_pos)
        
        # Find the nearest point on any CAD item
        for item in cad_items:
            nearest_point = self._get_item_nearest_point(item, mouse_pos)
            if nearest_point:
                distance = math.sqrt((mouse_pos.x() - nearest_point.x())**2 + 
                                   (mouse_pos.y() - nearest_point.y())**2)
                
                snap_points.append(SnapPoint(
                    point=nearest_point,
                    snap_type=SnapType.CONTOURS,
                    distance=distance,
                    source_item=item
                ))
        
        return snap_points
    
    def _get_item_nearest_point(self, item: CadItem, 
                               mouse_pos: QPointF) -> Optional[QPointF]:
        """Get the nearest point on a CAD item to the mouse position."""
        # Convert mouse position to item's local coordinates
        mouse_local = item.mapFromScene(mouse_pos)
        
        # For line-like items, find nearest point on the line
        if hasattr(item, '_start_point') and hasattr(item, '_end_point'):
            return self._point_to_line_nearest(
                mouse_local, item._start_point, item._end_point, item) # type: ignore
        
        # For circle-like items, find nearest point on the circle
        elif hasattr(item, '_center_point') and hasattr(item, 'radius'):
            return self._point_to_circle_nearest(
                mouse_local, item._center_point, item.radius, item) # type: ignore
        
        return None
    
    def _point_to_line_nearest(self, point: QPointF, line_start: QPointF, 
                              line_end: QPointF, item: CadItem) -> QPointF:
        """Find the nearest point on a line to a given point."""
        # Vector from line start to end
        line_vec_x = line_end.x() - line_start.x()
        line_vec_y = line_end.y() - line_start.y()
        
        # Vector from line start to point
        point_vec_x = point.x() - line_start.x()
        point_vec_y = point.y() - line_start.y()
        
        # Project point vector onto line vector
        line_length_sq = line_vec_x*line_vec_x + line_vec_y*line_vec_y
        if line_length_sq > 0:
            t = (point_vec_x*line_vec_x + point_vec_y*line_vec_y) / line_length_sq
            t = max(0, min(1, t))  # Clamp to line segment
            
            # Calculate nearest point
            nearest_local = QPointF(
                line_start.x() + t * line_vec_x,
                line_start.y() + t * line_vec_y
            )
            
            return item.mapToScene(nearest_local)
        
        return item.mapToScene(line_start)
    
    def _point_to_circle_nearest(self, point: QPointF, center: QPointF, 
                                radius: float, item: CadItem) -> QPointF:
        """Find the nearest point on a circle to a given point."""
        # Vector from center to point
        vec_x = point.x() - center.x()
        vec_y = point.y() - center.y()
        vec_length = math.sqrt(vec_x*vec_x + vec_y*vec_y)
        
        if vec_length > 0:
            # Normalize and scale by radius
            nearest_local = QPointF(
                center.x() + radius * vec_x / vec_length,
                center.y() + radius * vec_y / vec_length
            )
            
            return item.mapToScene(nearest_local)
        
        return item.mapToScene(center)
    
    def set_snap_tolerance(self, tolerance: float):
        """Set the snap tolerance in pixels."""
        self.snap_tolerance = tolerance
    
    def _get_current_scaling(self) -> float:
        """Get the current view scaling factor."""
        if self.scene and self.scene.views():
            view = self.scene.views()[0]
            return view.transform().m11()
        return 1.0
    
    def clear_cache(self):
        """Clear the snap calculation cache."""
        self._snap_cache.clear()

    def _find_angles_snaps(
            self,
            mouse_pos: QPointF,
            recent_points: List[QPointF]
    ) -> List[SnapPoint]:
        """Find angle snap points near the mouse position."""
        snap_points = []
        if not recent_points:
            return snap_points
        ref_point = recent_points[-1]
        delta = ref_point - mouse_pos
        radius = (delta.x()**2 + delta.y()**2)**0.5
        angle = math.degrees(math.atan2(delta.y(), delta.x()))
        snap_angle = round(angle / 15) * 15
        snap_point = ref_point + radius * QPointF(
            math.cos(math.radians(snap_angle)),
            math.sin(math.radians(snap_angle))
        )
        snap_points.append(SnapPoint(
            point=snap_point,
            snap_type=SnapType.ANGLES,
            distance=0,
        ))
                
        return snap_points