# MVVM Refactor Implementation

## Overview

This document describes the implementation of the MVVM (Model-View-ViewModel) pattern in BelfryCAD. The refactor separates business logic from presentation logic and improves testability, maintainability, and code organization.

## Directory Structure

```
src/BelfryCAD/
├── models/                    # Pure business logic (no UI dependencies)
│   ├── __init__.py
│   ├── cad_object.py         # CADObject, Point, ObjectType
│   ├── layer.py              # Layer, LayerManager
│   └── document.py           # Document
├── gui/
│   ├── viewmodels/           # Presentation logic with signals
│   │   ├── __init__.py
│   │   ├── document_viewmodel.py
│   │   ├── layer_viewmodel.py
│   │   ├── cad_object_viewmodel.py
│   │   └── control_points_viewmodel.py
│   ├── views/                # Pure UI components (to be moved)
│   │   ├── graphics_items/   # CadItems and graphics items
│   │   └── widgets/          # UI widgets
│   └── main_window_mvvm.py   # Refactored MainWindow example
```

## Model Layer

### CADObject Model
- **Location**: `src/BelfryCAD/models/cad_object.py`
- **Purpose**: Pure business logic for CAD objects
- **Key Features**:
  - No UI dependencies
  - Contains object data and business operations
  - Provides control point calculations
  - Handles object transformations

```python
class CADObject:
    def __init__(self, object_type: ObjectType, points: List[Point] = None, 
                 properties: Dict[str, Any] = None):
        self.object_id = str(uuid.uuid4())
        self.object_type = object_type
        self.points = points or []
        self.properties = properties or {}
        self.layer_id = 0
        self.visible = True
        self.locked = False
    
    def get_control_points(self) -> List[Tuple[float, float, str]]:
        """Get control point data for this object type"""
        # Business logic for control points
    
    def move_control_point(self, cp_index: int, x: float, y: float):
        """Move a specific control point"""
        # Business logic for control point movement
```

### Layer Model
- **Location**: `src/BelfryCAD/models/layer.py`
- **Purpose**: Pure business logic for layer management
- **Key Features**:
  - Layer properties and operations
  - Object-to-layer relationships
  - Visibility and lock states

### Document Model
- **Location**: `src/BelfryCAD/models/document.py`
- **Purpose**: Pure business logic for document management
- **Key Features**:
  - Object collection and management
  - Layer integration
  - Selection operations
  - Document state tracking

## ViewModel Layer

### DocumentViewModel
- **Location**: `src/BelfryCAD/gui/viewmodels/document_viewmodel.py`
- **Purpose**: Presentation logic for document operations
- **Key Features**:
  - Emits signals for UI updates
  - Manages selection state
  - Handles tool activation
  - Coordinates with other ViewModels

```python
class DocumentViewModel(QObject):
    # Signals for UI updates
    document_changed = Signal()
    object_added = Signal(str, CADObject)
    object_selected = Signal(str)
    selection_changed = Signal(list)
    
    def select_objects_at_point(self, point: QPointF, tolerance: float = 5.0):
        """Select objects at a specific point"""
        model_point = Point(point.x(), point.y())
        selected_ids = self._document.select_objects_at_point(model_point, tolerance)
        
        # Update selection and emit signals
        self._selected_object_ids = selected_ids
        for object_id in selected_ids:
            self.object_selected.emit(object_id)
        self.selection_changed.emit(self._selected_object_ids)
```

### ControlPointsViewModel
- **Location**: `src/BelfryCAD/gui/viewmodels/control_points_viewmodel.py`
- **Purpose**: Manages control points for selected objects
- **Key Features**:
  - Control point creation and management
  - Drag and drop operations
  - Signal emission for UI updates

### LayerViewModel
- **Location**: `src/BelfryCAD/gui/viewmodels/layer_viewmodel.py`
- **Purpose**: Presentation logic for layer operations
- **Key Features**:
  - Layer visibility and lock management
  - Active layer tracking
  - Layer property changes

### CADObjectViewModel
- **Location**: `src/BelfryCAD/gui/viewmodels/cad_object_viewmodel.py`
- **Purpose**: Presentation logic for individual CAD objects
- **Key Features**:
  - Object selection state
  - Position and transformation handling
  - Property management

## View Layer (Refactored)

### MainWindow as Pure View
- **Location**: `src/BelfryCAD/gui/main_window_mvvm.py`
- **Purpose**: Pure UI component that delegates to ViewModels
- **Key Features**:
  - Contains only UI components
  - Connects to ViewModels for business logic
  - Responds to ViewModel signals
  - Delegates user actions to ViewModels

```python
class MainWindow(QMainWindow):
    def __init__(self, config, preferences, document: Document):
        super().__init__()
        
        # Create ViewModels
        self.document_viewmodel = DocumentViewModel(document)
        self.control_points_viewmodel = ControlPointsViewModel()
        self.layer_viewmodel = LayerViewModel(document.layer_manager)
        
        # Connect ViewModel signals to UI updates
        self._connect_viewmodel_signals()
    
    def handle_mouse_press(self, event):
        """Handle mouse press - delegate to DocumentViewModel"""
        self.document_viewmodel.handle_mouse_press(event)
    
    def _on_object_selected(self, object_id: str):
        """Handle object selection from ViewModel signal"""
        cad_object = self.document_viewmodel.get_object(object_id)
        if cad_object:
            self.control_points_viewmodel.add_selected_object(object_id, cad_object)
```

## Benefits of MVVM Refactor

### 1. Separation of Concerns
- **Models**: Pure business logic, no UI dependencies
- **ViewModels**: Presentation logic with signals
- **Views**: Pure UI components

### 2. Testability
- Models can be tested without UI components
- ViewModels can be tested with mock signals
- UI logic is isolated and testable

### 3. Maintainability
- Clear boundaries between layers
- Changes to UI don't affect business logic
- Business logic changes don't require UI updates

### 4. Reusability
- Models can be used in different UI frameworks
- ViewModels can be reused across different views
- UI components are framework-specific but isolated

### 5. Real-time Updates
- Signals provide automatic UI updates
- No manual synchronization required
- Consistent state across components

## Signal Flow

```
User Action → View → ViewModel → Model
     ↓
Model Change → ViewModel Signal → View Update
```

### Example: Object Selection
1. User clicks on object in view
2. View calls `document_viewmodel.select_objects_at_point()`
3. ViewModel updates model and emits signals
4. View responds to signals and updates UI
5. Control points are created via ViewModel coordination

## Migration Strategy

### Phase 1: Create Models
- [x] Extract business logic from existing classes
- [x] Create pure model classes
- [x] Remove UI dependencies

### Phase 2: Create ViewModels
- [x] Create ViewModels with signals
- [x] Implement presentation logic
- [x] Connect ViewModels to each other

### Phase 3: Refactor Views
- [ ] Move CadItems to `gui/views/`
- [ ] Refactor MainWindow to use ViewModels
- [ ] Update existing UI components

### Phase 4: Update Tools
- [ ] Update tools to use ViewModels
- [ ] Remove direct model access
- [ ] Implement tool-specific ViewModels

## Testing Strategy

### Model Testing
```python
def test_cad_object_control_points():
    obj = CADObject(ObjectType.LINE, [Point(0, 0), Point(10, 10)])
    control_points = obj.get_control_points()
    assert len(control_points) == 2
    assert control_points[0][2] == "endpoint"
```

### ViewModel Testing
```python
def test_document_viewmodel_selection():
    document = Document()
    viewmodel = DocumentViewModel(document)
    
    # Test selection
    viewmodel.select_object("obj1")
    assert "obj1" in viewmodel.selected_object_ids
    
    # Test signal emission
    with qtbot.waitSignal(viewmodel.object_selected):
        viewmodel.select_object("obj2")
```

### View Testing
```python
def test_mainwindow_delegates_to_viewmodel():
    window = MainWindow(config, preferences, document)
    
    # Test delegation
    with qtbot.waitSignal(window.document_viewmodel.object_selected):
        window.handle_mouse_press(mock_event)
```

## Next Steps

1. **Complete View Refactor**: Move all UI components to `gui/views/`
2. **Update Tools**: Refactor tools to use ViewModels
3. **Add More ViewModels**: Create ViewModels for tools, preferences, etc.
4. **Implement Undo/Redo**: Add ViewModel support for undo/redo operations
5. **Performance Optimization**: Optimize signal connections and updates
6. **Documentation**: Update all documentation to reflect MVVM structure

## Conclusion

The MVVM refactor provides a solid foundation for BelfryCAD's architecture. It separates concerns, improves testability, and makes the codebase more maintainable. The signal-based communication ensures real-time updates while maintaining loose coupling between components. 