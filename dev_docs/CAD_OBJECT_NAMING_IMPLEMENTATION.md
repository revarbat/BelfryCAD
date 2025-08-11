# CAD Object Naming Implementation

## Overview

This document describes the implementation of string names for CadObjects with automatic naming and editing capabilities.

## Features Implemented

### 1. Automatic Naming System

- **Sequential Naming**: Objects are automatically named with sequential numbers (line1, line2, circle1, etc.)
- **Type-Based Naming**: Names are based on object type (line, circle, arc, ellipse, bezier, gear, polygon, group)
- **Unique Names**: All names are guaranteed to be unique within the document

### 2. Object Tree Integration

- **Name Display**: Object names are displayed in the object tree instead of generic type names
- **Double-Click Editing**: Users can double-click on object names in the tree to edit them
- **Real-time Updates**: Name changes are immediately reflected in the tree

### 3. Name Management

- **Unique Enforcement**: Names must be unique - duplicate names are rejected
- **Validation**: Invalid names are rejected with user feedback
- **Persistence**: Names are saved with object data

## Implementation Details

### CadObject Changes

1. **Added `_name` attribute**: Private attribute to store the object's name
2. **Added `name` property**: Public property to get/set the object's name
3. **Updated `get_data()` method**: Includes name in serialized data
4. **Updated `create_object_from_data()` method**: Handles name field during deserialization

### Document Changes

1. **Added `_name_counter`**: Tracks name counters for each object type
2. **Added `get_unique_name()` method**: Generates unique names for objects
3. **Added `rename_object()` method**: Handles object renaming with validation
4. **Updated `add_object()` method**: Automatically generates names for new objects

### Object Tree Pane Changes

1. **Added `name_changed` signal**: Emitted when object names change
2. **Updated display logic**: Shows object names instead of generic type names
3. **Added double-click editing**: Users can edit names by double-clicking
4. **Added validation**: Shows error messages for invalid names

### Main Window Changes

1. **Added `_on_object_tree_name_changed()` handler**: Handles name change events
2. **Connected name change signal**: Links object tree to main window

## Usage Examples

### Creating Objects with Automatic Names

```python
from src.BelfryCAD.models.document import Document
from src.BelfryCAD.models.cad_objects.line_cad_object import LineCadObject
from src.BelfryCAD.cad_geometry import Point2D

doc = Document()
line1 = LineCadObject(doc, Point2D(0, 0), Point2D(10, 10))
line2 = LineCadObject(doc, Point2D(5, 5), Point2D(15, 15))
doc.add_object(line1)  # Named "line1"
doc.add_object(line2)  # Named "line2"

print(line1.name)  # Output: "line1"
print(line2.name)  # Output: "line2"
```

### Renaming Objects

```python
# Rename an object
success = doc.rename_object(line1.object_id, "my_custom_line")
if success:
    print(f"Renamed to: {line1.name}")  # Output: "my_custom_line"
else:
    print("Rename failed - name already exists")
```

### Object Tree Integration

1. **Viewing Names**: Object names are displayed in the object tree
2. **Editing Names**: Double-click on any object name to edit it
3. **Validation**: Invalid names (duplicates, empty) show error messages
4. **Real-time Updates**: Changes are immediately reflected in the UI

## Technical Notes

### Name Generation Algorithm

1. **Base Name**: Determined by object type (line, circle, arc, etc.)
2. **Counter**: Starts from 1 and increments until a unique name is found
3. **Uniqueness Check**: Compares against all existing object names in the document
4. **Final Name**: Format: `{base_name}{counter}` (e.g., "line1", "circle2")

### Error Handling

1. **Duplicate Names**: Rejected with user feedback
2. **Empty Names**: Rejected with user feedback
3. **Invalid Characters**: Handled by the UI layer
4. **Network Issues**: Graceful degradation

### Performance Considerations

1. **Name Lookup**: O(n) where n is the number of objects
2. **Tree Updates**: Efficient refresh mechanism
3. **Memory Usage**: Minimal overhead for name storage
4. **Serialization**: Names included in object data

## Future Enhancements

1. **Name Patterns**: Support for custom naming patterns
2. **Bulk Renaming**: Rename multiple objects at once
3. **Name Templates**: Predefined name templates
4. **Name Validation**: More sophisticated validation rules
5. **Name History**: Track name changes for undo/redo 