# Tool Definition Class System

## Overview

The tool definition system has been refactored from a method-based approach to a class-based approach. This provides better organization, type safety, and easier access to tool definitions.

## Changes Made

### 1. Base Tool Class Updates

The `Tool` base class now includes:
- A class-level `tool_definitions` attribute that subclasses can override
- Updated `_get_definition()` method that uses class-level definitions by default
- Backward compatibility with the old method-based approach

### 2. Tool Definition Pattern

Instead of implementing `_get_definition()` method, tools now define their definitions as class attributes:

**Old Pattern:**
```python
class LineTool(Tool):
    def _get_definition(self) -> List[ToolDefinition]:
        return [ToolDefinition(
            token="LINE",
            name="Line Tool",
            category=ToolCategory.LINES,
            icon="tool-line",
            cursor="crosshair",
            is_creator=True,
            secondary_key="L",
            node_info=["Start Point", "End Point"]
        )]
```

**New Pattern:**
```python
class LineTool(Tool):
    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="LINE",
            name="Line Tool",
            category=ToolCategory.LINES,
            icon="tool-line",
            cursor="crosshair",
            is_creator=True,
            secondary_key="L",
            node_info=["Start Point", "End Point"]
        )
    ]
```

## Benefits

1. **Better Organization**: Tool definitions are clearly visible at the class level
2. **Type Safety**: IDE can provide better autocomplete and error checking
3. **Easier Access**: Tool definitions can be accessed without instantiating the tool
4. **Backward Compatibility**: Old method-based approach still works as fallback
5. **Multiple Definitions**: Tools can easily define multiple tool variants

## Migration Guide

To migrate existing tools to the new system:

1. Replace the `_get_definition()` method with a `tool_definitions` class attribute
2. Move the ToolDefinition instances from the method to the class attribute
3. Remove the method entirely

## Example Migration

**Before:**
```python
class MyTool(Tool):
    def _get_definition(self) -> List[ToolDefinition]:
        return [ToolDefinition(
            token="MYTOOL",
            name="My Tool",
            category=ToolCategory.LINES,
            icon="tool-mytool",
            cursor="crosshair",
            is_creator=True
        )]
```

**After:**
```python
class MyTool(Tool):
    # Class-level tool definition
    tool_definitions = [
        ToolDefinition(
            token="MYTOOL",
            name="My Tool",
            category=ToolCategory.LINES,
            icon="tool-mytool",
            cursor="crosshair",
            is_creator=True
        )
    ]
```

## Tools Updated

The following tools have been updated to use the new class-based system:

- `LineTool` (src/BelfryCAD/tools/line.py)
- `PointTool` (src/BelfryCAD/tools/point.py)
- `CircleTool` (src/BelfryCAD/tools/circle.py)
- `Circle2PTTool` (src/BelfryCAD/tools/circle.py)
- `Circle3PTTool` (src/BelfryCAD/tools/circle.py)

## Testing

The new system has been tested and verified to work correctly. Tool definitions are properly accessible and the system maintains backward compatibility with existing code. 