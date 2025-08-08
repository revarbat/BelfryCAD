# ConstraintsManager Implementation

## Overview

The `ConstraintsManager` class provides centralized constraint management for the Document class. It handles the creation, tracking, solving, and removal of constraints between CadObjects.

## Architecture

### Key Components

1. **ConstraintsManager**: Central manager that handles all constraint operations
2. **Document Integration**: Document class uses ConstraintsManager for constraint operations
3. **CadObject Integration**: CadObjects provide `make_constrainables()` and `update_from_solved_constraints()` methods

### Class Structure

```python
class ConstraintsManager:
    def __init__(self, document: 'Document'):
        self.document = document
        self.solver = ConstraintSolver()
        self.constrained_objects: Set[str] = set()
        self.object_constraints: Dict[Tuple[str, Optional[str]], List[str]] = {}
        self.constraints: Dict[str, Constraint] = {}
        self.objects_with_constrainables: Set[str] = set()
```

## Key Features

### 1. Constraint Tracking

The manager tracks constraints in multiple ways:

- **By ID**: `self.constraints[constraint_id] = constraint`
- **By Object Pairs**: `self.object_constraints[(obj1_id, obj2_id)] = [constraint_ids]`
- **Constrained Objects**: `self.constrained_objects = set of object_ids`

### 2. Automatic Constrainable Creation

When adding constraints, the manager automatically creates constrainables for objects:

```python
def _create_constrainables_for_object(self, object_id: str) -> bool:
    obj = self.document.get_object(object_id)
    if obj and hasattr(obj, 'make_constrainables'):
        obj.make_constrainables(self.solver)
        self.objects_with_constrainables.add(object_id)
        return True
    return False
```

### 3. Solver Rebuilding

When removing constraints, the solver is rebuilt from scratch:

```python
def _rebuild_solver(self):
    self.solver = ConstraintSolver()
    # Recreate constrainables for all constrained objects
    for object_id in self.constrained_objects:
        obj = self.document.get_object(object_id)
        if obj and hasattr(obj, 'make_constrainables'):
            obj.make_constrainables(self.solver)
    # Add all remaining constraints
    for constraint_id, constraint in self.constraints.items():
        self.solver.add_constraint(constraint.residual, constraint_id)
```

## API Reference

### Core Methods

#### `add_constraint(constraint_id, constraint, object_id1, object_id2=None)`
Adds a constraint between two objects.

**Parameters:**
- `constraint_id`: Unique identifier for the constraint
- `constraint`: The constraint object
- `object_id1`: ID of the first object
- `object_id2`: ID of the second object (None for single-object constraints)

**Returns:** `bool` - True if constraint was added successfully

#### `remove_constraint(constraint_id)`
Removes a constraint by ID.

**Parameters:**
- `constraint_id`: ID of the constraint to remove

**Returns:** `bool` - True if constraint was removed successfully

#### `solve_constraints(max_iter=50, tol=1e-8)`
Solves all constraints and updates objects.

**Parameters:**
- `max_iter`: Maximum number of solver iterations
- `tol`: Tolerance for convergence

**Returns:** `bool` - True if solver converged

### Query Methods

#### `get_constraints_for_object(object_id)`
Gets all constraint IDs involving a specific object.

#### `get_constraints_between_objects(object_id1, object_id2)`
Gets all constraint IDs between two specific objects.

#### `get_constraint_count()`
Gets the total number of constraints.

#### `has_constraints()`
Checks if there are any constraints.

### Management Methods

#### `clear_all_constraints()`
Clears all constraints from the manager.

#### `remove_constraints_between_objects(object_id1, object_id2=None)`
Removes all constraints between two objects.

## Document Integration

The Document class provides a simplified interface to the ConstraintsManager:

```python
# Add constraint
doc.add_constraint(constraint_id, constraint, object_id1, object_id2)

# Solve constraints
doc.solve_constraints()

# Remove constraint
doc.remove_constraint(constraint_id)

# Query constraints
doc.get_constraints_for_object(object_id)
doc.get_constraint_count()
doc.has_constraints()
```

## Usage Examples

### Basic Constraint Addition

```python
# Create objects
line1 = LineCadObject(doc, Point2D(0, 0), Point2D(10, 0))
line2 = LineCadObject(doc, Point2D(0, 5), Point2D(10, 5))

# Add to document
line1_id = doc.add_object(line1)
line2_id = doc.add_object(line2)

# Create constrainables
line1.make_constrainables(doc.constraints_manager.solver)
line2.make_constrainables(doc.constraints_manager.solver)

# Add constraint
constraint_id = doc.get_constraint_id("coincident", line1_id, line2_id)
coincident_constraint = CoincidentConstraint(
    line1.get_constrainables()[1][1],  # end_point
    line2.get_constrainables()[0][1]   # start_point
)
doc.add_constraint(constraint_id, coincident_constraint, line1_id, line2_id)

# Solve constraints
doc.solve_constraints()
```

### Complex Constraint Network

```python
# Create a rectangle with 4 lines and multiple constraints
lines = []
line_ids = []

for i in range(4):
    line = LineCadObject(doc, Point2D(i*10, 0), Point2D((i+1)*10, 0))
    line_id = doc.add_object(line)
    lines.append(line)
    line_ids.append(line_id)
    line.make_constrainables(doc.constraints_manager.solver)

# Add constraints for rectangle
# Horizontal constraints
for i in [0, 2]:
    constraint = HorizontalConstraint(
        lines[i].get_constrainables()[0][1],
        lines[i].get_constrainables()[1][1]
    )
    doc.add_constraint(f"horizontal{i}", constraint, line_ids[i])

# Vertical constraints
for i in [1, 3]:
    constraint = VerticalConstraint(
        lines[i].get_constrainables()[0][1],
        lines[i].get_constrainables()[1][1]
    )
    doc.add_constraint(f"vertical{i}", constraint, line_ids[i])

# Connect corners
for i in range(4):
    constraint = CoincidentConstraint(
        lines[i].get_constrainables()[1][1],
        lines[(i+1)%4].get_constrainables()[0][1]
    )
    doc.add_constraint(f"coincident{i}", constraint, line_ids[i], line_ids[(i+1)%4])

# Solve
doc.solve_constraints()
```

## Benefits

### 1. **Centralized Management**
- All constraint operations go through a single manager
- Consistent constraint handling across the application
- Easy to track and debug constraint issues

### 2. **Automatic Constrainable Creation**
- Objects automatically get constrainables when needed
- No manual management of constrainable creation
- Prevents errors from missing constrainables

### 3. **Efficient Solver Rebuilding**
- Solver is rebuilt only when constraints are removed
- Maintains solver state for better performance
- Handles complex constraint networks efficiently

### 4. **Comprehensive Tracking**
- Multiple ways to query constraint relationships
- Easy to find constraints by object or constraint type
- Supports complex constraint networks

### 5. **Integration with Document**
- Seamless integration with Document class
- Simplified API for common operations
- Maintains backward compatibility

## Testing

The implementation includes comprehensive tests:

- **Basic functionality**: Adding, removing, solving constraints
- **Complex scenarios**: Multiple objects with multiple constraints
- **Error handling**: Invalid objects, missing constrainables
- **Performance**: Large constraint networks

## Future Enhancements

### Potential Improvements

1. **Constraint Validation**: Validate constraints before adding
2. **Conflict Detection**: Detect conflicting constraints
3. **Performance Optimization**: Incremental solver updates
4. **Constraint Types**: Support for more constraint types
5. **Visualization**: Tools for visualizing constraint networks

### Advanced Features

1. **Constraint Groups**: Group related constraints
2. **Constraint Templates**: Predefined constraint patterns
3. **Automatic Constraint Suggestions**: Suggest constraints based on geometry
4. **Constraint History**: Undo/redo for constraint operations

## Conclusion

The ConstraintsManager provides a robust, efficient, and user-friendly way to manage constraints in the CAD system. It handles the complexity of constraint management while providing a simple interface for common operations. 