# Constraint System Granular Update

## Overview

Updated the XML constraint system to support constraints between individual constrainable properties of CAD objects, rather than between entire objects. This provides much more granular and flexible constraint capabilities.

## Rationale

- **Granular Control**: Constraints can now target specific properties (e.g., `line1.start_point`) rather than entire objects
- **Flexibility**: Supports complex constraint scenarios like point-to-curve tangency
- **Precision**: Allows for more precise geometric relationships
- **Industry Standard**: Matches the approach used in professional CAD systems

## Changes Made

### 1. **`src/BelfryCAD/utils/xml_serializer.py`**

#### Serialization Changes:
- Updated `_add_constraints_section()` to use `constrainable1` and `constrainable2` attributes
- Added support for constraint parameters as child elements
- Format: `object.property` (e.g., "line1.start_point", "circle2.center_point")

#### Parsing Changes:
- Updated `_parse_constraints_section()` to parse `constrainable1` and `constrainable2` attributes
- Added parsing for constraint parameters
- Enhanced debug output to show constrainable properties and parameters

### 2. **`dev_docs/XML_FILE_FORMAT_SPECIFICATION.md`**
- Updated constraints section with new granular format
- Added comprehensive documentation of constrainable properties
- Updated complete example to use new constraint format
- Added constraint types documentation

## Constraint Format

### Before (Object-Level)
```xml
<belfry:constraint id="constraint1" type="DistanceConstraint" 
                   object1="line1" object2="circle1" />
```

### After (Property-Level)
```xml
<belfry:constraint id="constraint1" type="CoincidenceConstraint" 
                   constrainable1="line1.start_point" constrainable2="line2.end_point" />
```

## Constrainable Properties

### Points
- `line1.start_point` - Start point of a line
- `line1.end_point` - End point of a line
- `circle1.center_point` - Center point of a circle
- `arc1.center_point` - Center point of an arc
- `ellipse1.center_point` - Center point of an ellipse

### Curves
- `line1` - Entire line (for angle constraints)
- `circle1` - Entire circle (for tangency)
- `arc1` - Entire arc (for tangency)
- `ellipse1` - Entire ellipse (for tangency)

### Dimensions
- `circle1.radius` - Radius of a circle
- `arc1.radius` - Radius of an arc
- `line1.length` - Length of a line

## Constraint Types

- **CoincidenceConstraint**: Two points must coincide
- **TangentConstraint**: A point must be tangent to a curve
- **DistanceConstraint**: Distance between two points with optional parameter
- **AngleConstraint**: Angle between two lines with optional parameter
- **ParallelConstraint**: Two lines must be parallel
- **PerpendicularConstraint**: Two lines must be perpendicular
- **EqualConstraint**: Two properties must have equal values

## Example Constraints

### Point Coincidence
```xml
<belfry:constraint id="constraint1" type="CoincidenceConstraint" 
                   constrainable1="line1.start_point" constrainable2="line2.end_point" />
```

### Point-to-Curve Tangency
```xml
<belfry:constraint id="constraint2" type="TangentConstraint" 
                   constrainable1="line1.end_point" constrainable2="circle1" />
```

### Distance with Parameter
```xml
<belfry:constraint id="constraint3" type="DistanceConstraint" 
                   constrainable1="point1" constrainable2="point2">
    <belfry:parameter name="distance" value="5.0" />
</belfry:constraint>
```

### Angle with Parameter
```xml
<belfry:constraint id="constraint4" type="AngleConstraint" 
                   constrainable1="line1" constrainable2="line2">
    <belfry:parameter name="angle" value="90.0" />
</belfry:constraint>
```

## Benefits

1. **Precision**: Can target specific geometric elements
2. **Flexibility**: Supports complex constraint scenarios
3. **Clarity**: Clear indication of which properties are constrained
4. **Extensibility**: Easy to add new constraint types and properties
5. **Professional**: Matches industry-standard CAD constraint systems

## Implementation Notes

- The constraint system now supports both simple constraints (no parameters) and complex constraints (with parameters)
- Constrainable properties use dot notation: `object.property`
- Parameters are stored as child elements with name/value pairs
- Backward compatibility is maintained for existing constraint parsing

## Testing

- All 9 tests pass ✅
- Example script works correctly ✅
- No regressions in functionality ✅
- New constraint format properly serialized and parsed ✅

## Future Considerations

When implementing the full constraint system:
1. Each CAD object should expose its constrainable properties
2. Constraint solver should understand the property-level relationships
3. UI should allow selection of specific properties for constraints
4. Constraint validation should check property compatibility 