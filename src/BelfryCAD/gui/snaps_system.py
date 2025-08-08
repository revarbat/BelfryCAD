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

from .widgets.cad_scene import CadScene
from .grid_info import GridInfo
from .panes.snaps_pane import snaps_pane_info
from .graphics_items.control_points import ControlPoint

from .graphics_items.grid_graphics_items import GridBackground, RulersForeground


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
    source_item: Optional['QGraphicsItem'] = None
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
            exclude_cps: Optional[List[ControlPoint]] = None,
            exclude_cad_item: Optional['QGraphicsItem'] = None
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
                snap_points.extend(self._find_quadrant_snaps(mouse_pos, exclude_cad_item=exclude_cad_item))
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
    
    def _get_cad_items_near_point(self, mouse_pos: QPointF) -> List['QGraphicsItem']:
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
        cad_items = [item for item in nearby_items if hasattr(item, 'object_id')]
        
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
            item: 'QGraphicsItem',
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
    
    def _get_item_midpoints(self, item: 'QGraphicsItem') -> List[QPointF]:
        """Get midpoint snap points for a CAD item."""
        midpoints = []
        
        # Get the item's bounding rectangle
        rect = item.boundingRect()
        if rect.isValid():
            # Add the center point of the bounding rectangle
            center = rect.center()
            midpoints.append(center)
        
        return midpoints

    def _find_quadrant_snaps(self, mouse_pos: QPointF, exclude_cad_item: Optional['QGraphicsItem'] = None) -> List[SnapPoint]:
        """Find quadrant snap points near the mouse position."""
        snap_points = []
        
        # Get CAD items near the mouse position
        cad_items = self._get_cad_items_near_point(mouse_pos)
        
        # Filter out the excluded item
        if exclude_cad_item:
            cad_items = [item for item in cad_items if item != exclude_cad_item]
        
        # Get quadrant points from each item
        for item in cad_items:
            quadrant_points = self._get_item_quadrants(item)
            for point in quadrant_points:
                distance = self._calculate_distance(mouse_pos, point)
                if distance <= self.snap_tolerance:
                    snap_points.append(SnapPoint(
                        point=point,
                        snap_type=SnapType.QUADRANT,
                        distance=distance,
                        source_item=item
                    ))
        
        return snap_points

    def _get_item_quadrants(self, item: 'QGraphicsItem') -> List[QPointF]:
        """Get quadrant snap points for a CAD item."""
        quadrants = []
        
        # Get the item's bounding rectangle
        rect = item.boundingRect()
        if rect.isValid():
            # Add the four corner points
            quadrants.extend([
                rect.topLeft(),
                rect.topRight(),
                rect.bottomLeft(),
                rect.bottomRight()
            ])
        
        return quadrants

    def _find_tangent_snaps(self, mouse_pos: QPointF, 
                           recent_points: List[QPointF]) -> List[SnapPoint]:
        """Find tangent snap points near the mouse position."""
        snap_points = []
        
        if not recent_points:
            return snap_points
        
        # Use the most recent point as reference
        ref_point = recent_points[-1]
        
        # Get CAD items near the mouse position
        cad_items = self._get_cad_items_near_point(mouse_pos)
        
        # Get tangent points from each item
        for item in cad_items:
            tangent_points = self._get_item_tangent_points(item, ref_point)
            for point in tangent_points:
                distance = self._calculate_distance(mouse_pos, point)
                if distance <= self.snap_tolerance:
                    snap_points.append(SnapPoint(
                        point=point,
                        snap_type=SnapType.TANGENT,
                        distance=distance,
                        source_item=item
                    ))
        
        return snap_points

    def _get_item_tangent_points(self, item: 'QGraphicsItem', 
                               ref_point: QPointF) -> List[QPointF]:
        """Get tangent snap points for a CAD item relative to a reference point."""
        tangent_points = []
        
        # For now, just return the center of the item's bounding rectangle
        # This is a simplified implementation
        rect = item.boundingRect()
        if rect.isValid():
            center = rect.center()
            tangent_points.append(center)
        
        return tangent_points

    def _find_perpendicular_snaps(
            self,
            mouse_pos: QPointF, 
            recent_points: List[QPointF]
    ) -> List[SnapPoint]:
        """Find perpendicular snap points near the mouse position."""
        snap_points = []
        
        if not recent_points:
            return snap_points
        
        # Use the most recent point as reference
        ref_point = recent_points[-1]
        
        # Get CAD items near the mouse position
        cad_items = self._get_cad_items_near_point(mouse_pos)
        
        # Get perpendicular points from each item
        for item in cad_items:
            perpendicular_points = self._get_item_perpendicular_points(item, ref_point)
            for point in perpendicular_points:
                distance = self._calculate_distance(mouse_pos, point)
                if distance <= self.snap_tolerance:
                    snap_points.append(SnapPoint(
                        point=point,
                        snap_type=SnapType.PERPENDICULAR,
                        distance=distance,
                        source_item=item
                    ))
        
        return snap_points

    def _get_item_perpendicular_points(
            self,
            item: 'QGraphicsItem', 
            ref_point: QPointF
    ) -> List[QPointF]:
        """Get perpendicular snap points for a CAD item relative to a reference point."""
        perpendicular_points = []
        
        # For now, just return the center of the item's bounding rectangle
        # This is a simplified implementation
        rect = item.boundingRect()
        if rect.isValid():
            center = rect.center()
            perpendicular_points.append(center)
        
        return perpendicular_points

    def _find_intersection_snaps(self, mouse_pos: QPointF) -> List[SnapPoint]:
        """Find intersection snap points near the mouse position."""
        # This is a placeholder implementation
        return []

    def _find_nearest_snaps(self, mouse_pos: QPointF) -> List[SnapPoint]:
        """Find nearest point snap points near the mouse position."""
        snap_points = []
        
        # Get CAD items near the mouse position
        cad_items = self._get_cad_items_near_point(mouse_pos)
        
        # Get nearest points from each item
        for item in cad_items:
            nearest_point = self._get_item_nearest_point(item, mouse_pos)
            if nearest_point:
                distance = self._calculate_distance(mouse_pos, nearest_point)
                if distance <= self.snap_tolerance:
                    snap_points.append(SnapPoint(
                        point=nearest_point,
                        snap_type=SnapType.CONTOURS,
                        distance=distance,
                        source_item=item
                    ))
        
        return snap_points

    def _get_item_nearest_point(self, item: 'QGraphicsItem', 
                               mouse_pos: QPointF) -> Optional[QPointF]:
        """Get the nearest point on a CAD item to the mouse position."""
        # For now, just return the center of the item's bounding rectangle
        # This is a simplified implementation
        rect = item.boundingRect()
        if rect.isValid():
            return rect.center()
        return None

    def _point_to_line_nearest(self, point: QPointF, line_start: QPointF, 
                              line_end: QPointF, item: 'QGraphicsItem') -> QPointF:
        """Find the nearest point on a line to a given point."""
        # This is a placeholder implementation
        return line_start

    def _point_to_circle_nearest(self, point: QPointF, center: QPointF, 
                                radius: float, item: 'QGraphicsItem') -> QPointF:
        """Find the nearest point on a circle to a given point."""
        # This is a placeholder implementation
        return center
    
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