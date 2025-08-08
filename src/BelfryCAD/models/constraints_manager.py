"""
ConstraintsManager - Manages constraints between CadObjects in a Document.

This module provides a centralized way to manage constraints between CAD objects,
including adding, removing, and solving constraints.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, TYPE_CHECKING
from .cad_object import CadObject
from ..utils.constraints import ConstraintSolver, Constraint, Constrainable

if TYPE_CHECKING:
    from .document import Document


class ConstraintsManager:
    """
    Manages constraints between CadObjects in a Document.
    
    This class handles:
    - Tracking which CadObjects have constraints
    - Adding constraints between objects
    - Removing constraints
    - Solving constraints and updating objects
    - Rebuilding the solver when needed
    """
    
    def __init__(self, document: 'Document'):
        """
        Initialize the constraints manager.
        
        Args:
            document: The document this manager belongs to
        """
        self.document = document
        self.solver = ConstraintSolver()
        
        # Track which objects have constraints
        self.constrained_objects: Set[str] = set()
        
        # Track constraints by object pairs
        # Key: (object_id1, object_id2) or (object_id1, None) for single-object constraints
        # Value: List of constraint IDs
        self.object_constraints: Dict[Tuple[str, Optional[str]], List[str]] = {}
        
        # Track all constraints by ID
        self.constraints: Dict[str, Constraint] = {}
        
        # Track which objects have constrainables created
        self.objects_with_constrainables: Set[str] = set()
    
    def add_constraint(self, constraint_id: str, constraint: Constraint, 
                      object_id1: str, object_id2: Optional[str] = None) -> bool:
        """
        Add a constraint between two objects.
        
        Args:
            constraint_id: Unique identifier for the constraint
            constraint: The constraint object
            object_id1: ID of the first object
            object_id2: ID of the second object (None for single-object constraints)
            
        Returns:
            True if constraint was added successfully, False otherwise
        """
        # Validate objects exist
        obj1 = self.document.get_object(object_id1)
        if not obj1:
            return False
        
        if object_id2:
            obj2 = self.document.get_object(object_id2)
            if not obj2:
                return False
        
        # Ensure objects have constrainables created
        if object_id1 not in self.objects_with_constrainables:
            self._create_constrainables_for_object(object_id1)
        
        if object_id2 and object_id2 not in self.objects_with_constrainables:
            self._create_constrainables_for_object(object_id2)
        
        # Add constraint to tracking
        self.constraints[constraint_id] = constraint
        self.constrained_objects.add(object_id1)
        if object_id2:
            self.constrained_objects.add(object_id2)
        
        # Track constraint by object pair
        pair_key = (object_id1, object_id2)
        if pair_key not in self.object_constraints:
            self.object_constraints[pair_key] = []
        self.object_constraints[pair_key].append(constraint_id)
        
        # Add constraint to solver
        self.solver.add_constraint(constraint.residual, constraint_id)
        
        return True
    
    def remove_constraint(self, constraint_id: str) -> bool:
        """
        Remove a constraint by ID.
        
        Args:
            constraint_id: ID of the constraint to remove
            
        Returns:
            True if constraint was removed successfully, False otherwise
        """
        if constraint_id not in self.constraints:
            return False
        
        # Remove from solver by rebuilding
        self._rebuild_solver()
        
        # Remove from tracking
        constraint = self.constraints.pop(constraint_id)
        
        # Find and remove from object_constraints
        for pair_key, constraint_ids in list(self.object_constraints.items()):
            if constraint_id in constraint_ids:
                constraint_ids.remove(constraint_id)
                if not constraint_ids:
                    del self.object_constraints[pair_key]
                break
        
        # Update constrained_objects set
        self._update_constrained_objects_set()
        
        return True
    
    def remove_constraints_between_objects(self, object_id1: str, object_id2: Optional[str] = None) -> List[str]:
        """
        Remove all constraints between two objects.
        
        Args:
            object_id1: ID of the first object
            object_id2: ID of the second object (None for single-object constraints)
            
        Returns:
            List of constraint IDs that were removed
        """
        pair_key = (object_id1, object_id2)
        if pair_key not in self.object_constraints:
            return []
        
        constraint_ids = self.object_constraints[pair_key].copy()
        
        # Remove each constraint
        for constraint_id in constraint_ids:
            self.remove_constraint(constraint_id)
        
        return constraint_ids
    
    def get_constraints_for_object(self, object_id: str) -> List[str]:
        """
        Get all constraint IDs involving a specific object.
        
        Args:
            object_id: ID of the object
            
        Returns:
            List of constraint IDs
        """
        constraint_ids = []
        
        for (obj1, obj2), ids in self.object_constraints.items():
            if obj1 == object_id or obj2 == object_id:
                constraint_ids.extend(ids)
        
        return constraint_ids
    
    def get_constraints_between_objects(self, object_id1: str, object_id2: str) -> List[str]:
        """
        Get all constraint IDs between two specific objects.
        
        Args:
            object_id1: ID of the first object
            object_id2: ID of the second object
            
        Returns:
            List of constraint IDs
        """
        # Check both directions
        pair_key1 = (object_id1, object_id2)
        pair_key2 = (object_id2, object_id1)
        
        constraint_ids = []
        
        if pair_key1 in self.object_constraints:
            constraint_ids.extend(self.object_constraints[pair_key1])
        
        if pair_key2 in self.object_constraints:
            constraint_ids.extend(self.object_constraints[pair_key2])
        
        return constraint_ids
    
    def solve_constraints(self, max_iter: int = 50, tol: float = 1e-8) -> bool:
        """
        Solve all constraints and update objects.
        
        This method identifies connected components in the constraint graph
        and solves each component independently.
        
        Args:
            max_iter: Maximum number of solver iterations
            tol: Tolerance for convergence
            
        Returns:
            True if all components converged, False if any failed
        """
        if not self.constraints:
            return True
        
        # Find connected components in the constraint graph
        components = self._find_connected_components()
        
        # Solve each component independently
        all_successful = True
        for component in components:
            if not self._solve_component(component, max_iter, tol):
                all_successful = False
                print(f"Failed to solve constraint component with {len(component)} objects")
        
        return all_successful

    def _find_connected_components(self) -> List[Set[str]]:
        """
        Find connected components in the constraint graph.
        
        Returns:
            List of sets, where each set contains object IDs that form a connected component
        """
        if not self.constrained_objects:
            return []
        
        # Build adjacency list for the constraint graph
        graph = {}
        for object_id in self.constrained_objects:
            graph[object_id] = set()
        
        # Add edges based on constraints
        for (obj1, obj2), constraint_ids in self.object_constraints.items():
            if obj1 in graph:
                if obj2:
                    graph[obj1].add(obj2)
                if obj2 in graph:
                    graph[obj2].add(obj1)
        
        # Find connected components using DFS
        visited = set()
        components = []
        
        def dfs(node: str, component: Set[str]):
            """Depth-first search to find connected component."""
            if node in visited:
                return
            visited.add(node)
            component.add(node)
            
            for neighbor in graph.get(node, set()):
                dfs(neighbor, component)
        
        # Find all connected components
        for node in graph:
            if node not in visited:
                component = set()
                dfs(node, component)
                if component:  # Only add non-empty components
                    components.append(component)
        
        return components

    def _solve_component(self, component: Set[str], max_iter: int, tol: float) -> bool:
        """
        Solve constraints for a single connected component.
        
        Args:
            component: Set of object IDs in the component
            max_iter: Maximum number of solver iterations
            tol: Tolerance for convergence
            
        Returns:
            True if component solved successfully, False otherwise
        """
        # Create a new solver for this component
        component_solver = ConstraintSolver()
        
        # Track which objects have constrainables in this component
        component_objects_with_constrainables = set()
        
        # Create constrainables for all objects in the component
        for object_id in component:
            obj = self.document.get_object(object_id)
            if obj and hasattr(obj, 'make_constrainables'):
                obj.make_constrainables(component_solver)
                component_objects_with_constrainables.add(object_id)
        
        # Add constraints that involve objects in this component
        component_constraints = []
        for constraint_id, constraint in self.constraints.items():
            # Find which objects this constraint involves
            constraint_objects = set()
            for (obj1, obj2), constraint_ids in self.object_constraints.items():
                if constraint_id in constraint_ids:
                    constraint_objects.add(obj1)
                    if obj2:
                        constraint_objects.add(obj2)
            
            # If all objects in this constraint are in our component, add it
            if constraint_objects.issubset(component):
                component_solver.add_constraint(constraint.residual, constraint_id)
                component_constraints.append(constraint_id)
        
        if not component_constraints:
            return True  # No constraints to solve
        
        # Update constrainables with current object values
        for object_id in component:
            obj = self.document.get_object(object_id)
            if obj and hasattr(obj, 'update_constrainables_before_solving'):
                obj.update_constrainables_before_solving(component_solver)
        
        # Solve the component
        try:
            component_solver.solve()
            
            # Update objects in this component
            for object_id in component:
                obj = self.document.get_object(object_id)
                if obj and hasattr(obj, 'update_from_solved_constraints'):
                    obj.update_from_solved_constraints(component_solver)
            
            return True
        except Exception as e:
            print(f"Component solver failed: {e}")
            return False
    
    def _create_constrainables_for_object(self, object_id: str) -> bool:
        """
        Create constrainables for an object if they don't exist.
        
        Args:
            object_id: ID of the object
            
        Returns:
            True if constrainables were created, False otherwise
        """
        obj = self.document.get_object(object_id)
        if not obj or not hasattr(obj, 'make_constrainables'):
            return False
        
        # Create constrainables for the object
        obj.make_constrainables(self.solver)
        self.objects_with_constrainables.add(object_id)
        
        return True
    
    def _rebuild_solver(self):
        """Rebuild the solver with remaining constraints."""
        # Create new solver
        self.solver = ConstraintSolver()
        
        # Recreate constrainables for all constrained objects
        for object_id in self.constrained_objects:
            obj = self.document.get_object(object_id)
            if obj and hasattr(obj, 'make_constrainables'):
                obj.make_constrainables(self.solver)
        
        # Add all remaining constraints
        for constraint_id, constraint in self.constraints.items():
            self.solver.add_constraint(constraint.residual, constraint_id)
    
    def _update_constrained_objects_set(self):
        """Update the set of objects that have constraints."""
        self.constrained_objects.clear()
        
        for (obj1, obj2) in self.object_constraints.keys():
            self.constrained_objects.add(obj1)
            if obj2:
                self.constrained_objects.add(obj2)
    
    def clear_all_constraints(self):
        """Clear all constraints from the manager."""
        self.constraints.clear()
        self.object_constraints.clear()
        self.constrained_objects.clear()
        self.objects_with_constrainables.clear()
        self.solver = ConstraintSolver()
    
    def get_constraint_count(self) -> int:
        """Get the total number of constraints."""
        return len(self.constraints)
    
    def get_constrained_object_count(self) -> int:
        """Get the number of objects that have constraints."""
        return len(self.constrained_objects)
    
    def has_constraints(self) -> bool:
        """Check if there are any constraints."""
        return len(self.constraints) > 0
    
    def get_constraint_info(self) -> Dict[str, Any]:
        """
        Get information about the current constraint state.
        
        Returns:
            Dictionary with constraint information
        """
        components = self._find_connected_components()
        return {
            'total_constraints': len(self.constraints),
            'constrained_objects': len(self.constrained_objects),
            'object_constraints': dict(self.object_constraints),
            'constraint_ids': list(self.constraints.keys()),
            'connected_components': len(components),
            'component_sizes': [len(comp) for comp in components]
        }

    def get_connected_components(self) -> List[Set[str]]:
        """
        Get the connected components in the constraint graph.
        
        Returns:
            List of sets, where each set contains object IDs that form a connected component
        """
        return self._find_connected_components()

    def get_component_info(self) -> List[Dict[str, Any]]:
        """
        Get detailed information about each connected component.
        
        Returns:
            List of dictionaries with component information
        """
        components = self._find_connected_components()
        component_info = []
        
        for i, component in enumerate(components):
            # Count constraints in this component
            component_constraints = 0
            for constraint_id, constraint in self.constraints.items():
                constraint_objects = set()
                for (obj1, obj2), constraint_ids in self.object_constraints.items():
                    if constraint_id in constraint_ids:
                        constraint_objects.add(obj1)
                        if obj2:
                            constraint_objects.add(obj2)
                
                if constraint_objects.issubset(component):
                    component_constraints += 1
            
            component_info.append({
                'component_id': i,
                'object_count': len(component),
                'constraint_count': component_constraints,
                'object_ids': list(component)
            })
        
        return component_info 