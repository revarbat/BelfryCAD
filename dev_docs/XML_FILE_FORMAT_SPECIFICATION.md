# BelfryCAD XML File Format Specification

## Overview

BelfryCAD uses a zip-compressed XML format for storing CAD documents. The format supports all CAD objects, parameters, constraints, and document preferences in a structured, human-readable format.

## File Structure

The file is a ZIP archive containing:
- `document.xml` - Main document data
- `metadata.json` - Additional metadata (optional)

## XML Namespace

All XML elements use the namespace: `http://belfrydw.com/xml/BelfryCAD/1.0`

## Document Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<belfry:belfrycad_document version="1.0" xmlns:belfry="http://belfrydw.com/xml/BelfryCAD/1.0">
    <belfry:header>
        <belfry:preferences units="inches" precision="3" use_fractions="false" />
    </belfry:header>
    
    <belfry:parameters>
        <belfry:parameter name="radius" expression="5.0" />
        <belfry:parameter name="height" expression="2 * $radius" />
    </belfry:parameters>
    
    <belfry:objects>
        <!-- CAD objects and groups -->
    </belfry:objects>
    
    <belfry:constraints>
        <!-- Constraints between objects -->
    </belfry:constraints>
</belfry:belfrycad_document>
```

## Document Header

The header section contains document preferences:

```xml
<belfry:header>
    <belfry:preferences 
        units="inches"           <!-- mm, cm, m, inches, ft, yd -->
        precision="3"            <!-- Decimal places for display -->
        use_fractions="false"    <!-- true/false for fraction display -->
        grid_visible="true"      <!-- Show grid -->
        show_rulers="true"       <!-- Show rulers -->
        canvas_bg_color="#ffffff" <!-- Background color -->
        grid_color="#cccccc"     <!-- Grid color -->
        selection_color="#0080ff" <!-- Selection color -->
    />
</belfry:header>
```

## Parameters Section

Parameters define named expressions that can be referenced throughout the document:

```xml
<belfry:parameters>
    <belfry:parameter name="radius" expression="5.0" />
    <belfry:parameter name="height" expression="2 * $radius" />
    <belfry:parameter name="angle" expression="45º" />
    <belfry:parameter name="area" expression="pi * $radius^2" />
</belfry:parameters>
```

### Parameter Expressions

Parameters support mathematical expressions with:
- Basic arithmetic: `+`, `-`, `*`, `/`, `^` (exponentiation)
- Variables: `$name` (references other parameters)
- Constants: `pi`, `e`, `phi`
- Functions: `sin()`, `cos()`, `sqrt()`, etc.
- Units: `º` (degrees to radians), `'` (feet), `"` (inches)

## CAD Objects Section

The objects section contains all CAD objects and groups:

### Basic Object Properties

All CAD objects have these common properties:
- `id` - Unique object identifier
- `name` - Object name
- `color` - Object color (CSS color format)
- `line_width` - Line width (optional)
- `visible` - Visibility (true/false)
- `locked` - Locked state (true/false)
- `parent` - Parent group ID (optional)

### Fixed Values

For constraint system compatibility, object properties can be marked as fixed (unchanging):
- `fixed="true"` - Property is fixed and cannot be modified by constraints
- `fixed="false"` or omitted - Property is free and can be modified by constraints (default)

**Note**: The `fixed` attribute defaults to `false` when not specified, so it's only necessary to include `fixed="true"` when a property should be fixed.

### Line Object

```xml
<belfry:line id="line1" name="My Line" color="black" line_width="0.05" visible="true" locked="false">
    <belfry:start_point x="0.0" y="0.0" />
    <belfry:end_point x="10.0" y="5.0" />
</belfry:line>
```

### Circle Object

```xml
<belfry:circle id="circle1" name="My Circle" color="blue" line_width="0.1" visible="true" locked="false">
    <belfry:center_point x="5.0" y="5.0" />
    <belfry:radius value="3.0" />
</belfry:circle>
```

### Arc Object

```xml
<belfry:arc id="arc1" name="My Arc" color="red" line_width="0.05" visible="true" locked="false">
    <belfry:center_point x="0.0" y="0.0" />
    <belfry:radius value="5.0" />
    <belfry:start_angle value="0.0" />
    <belfry:span_angle value="90.0" />
</belfry:arc>
```

### Ellipse Object

```xml
<belfry:ellipse id="ellipse1" name="My Ellipse" color="green" line_width="0.05" visible="true" locked="false">
    <belfry:center_point x="0.0" y="0.0" />
    <belfry:major_radius value="5.0" />
    <belfry:minor_radius value="3.0" />
    <belfry:rotation_angle value="0.0" />
</belfry:ellipse>
```

### Bezier Curve Object

```xml
<belfry:cubicbezier id="bezier1" name="My Bezier" color="purple" line_width="0.05" visible="true" locked="false">
    <belfry:control_point index="0" x="0.0" y="0.0" />
    <belfry:control_point index="1" x="2.0" y="3.0" />
    <belfry:control_point index="2" x="8.0" y="3.0" />
    <belfry:control_point index="3" x="10.0" y="0.0" />
</belfry:cubicbezier>
```

### Gear Object

```xml
<belfry:gear id="gear1" name="My Gear" color="orange" line_width="0.05" visible="true" locked="false">
    <belfry:center_point x="0.0" y="0.0" />
    <belfry:pitch_radius value="10.0" fixed="false" />
    <belfry:num_teeth value="20" fixed="false" />
    <belfry:pressure_angle value="20.0" fixed="false" />
</belfry:gear>
```

### Group Object

Groups can contain other objects and groups:

```xml
<belfry:group id="group1" name="My Group" color="black" visible="true" locked="false">
    <belfry:line id="line2" name="Line in Group" color="red">
        <belfry:start_point x="0.0" y="0.0" />
        <belfry:end_point x="5.0" y="5.0" />
    </belfry:line>
    
    <belfry:circle id="circle2" name="Circle in Group" color="blue">
        <belfry:center_point x="2.5" y="2.5" />
        <belfry:radius value="1.0" fixed="false" />
    </belfry:circle>
</belfry:group>
```

## Fixed vs Free Data

Individual CAD object data can be marked as fixed (unchanging) or free (modifiable by constraints):

```xml
<belfry:radius value="5.0" fixed="true" />   <!-- Fixed radius -->
<belfry:radius value="5.0" fixed="false" />  <!-- Free radius (can be constrained) -->
```

## Parameter Expressions in Objects

Object data can use parameter expressions:

```xml
<belfry:circle id="circle1" name="Parameterized Circle">
    <belfry:center_point x="0.0" y="0.0" />
    <belfry:radius value="$radius" fixed="false" />
</belfry:circle>
```

## Constraints Section

Constraints define relationships between individual constrainable properties of CAD objects:

```xml
<belfry:constraints>
    <!-- Point-to-point coincidence -->
    <belfry:constraint id="constraint1" type="CoincidenceConstraint" 
                       constrainable1="line1.start_point" constrainable2="line2.end_point" />
    
    <!-- Point-to-curve tangency -->
    <belfry:constraint id="constraint2" type="TangentConstraint" 
                       constrainable1="line1.end_point" constrainable2="circle1" />
    
    <!-- Distance constraint with parameter -->
    <belfry:constraint id="constraint3" type="DistanceConstraint" 
                       constrainable1="point1" constrainable2="point2">
        <belfry:parameter name="distance" value="5.0" />
    </belfry:constraint>
    
    <!-- Angle constraint -->
    <belfry:constraint id="constraint4" type="AngleConstraint" 
                       constrainable1="line1" constrainable2="line2">
        <belfry:parameter name="angle" value="90.0" />
    </belfry:constraint>
</belfry:constraints>
```

### Constrainable Properties

Constraints operate on individual properties of CAD objects:

**Points:**
- `line1.start_point` - Start point of a line
- `line1.end_point` - End point of a line
- `circle1.center_point` - Center point of a circle
- `arc1.center_point` - Center point of an arc
- `ellipse1.center_point` - Center point of an ellipse

**Curves:**
- `line1` - Entire line (for angle constraints)
- `circle1` - Entire circle (for tangency)
- `arc1` - Entire arc (for tangency)
- `ellipse1` - Entire ellipse (for tangency)

**Dimensions:**
- `circle1.radius` - Radius of a circle
- `arc1.radius` - Radius of an arc
- `line1.length` - Length of a line

### Constraint Types

- **CoincidenceConstraint**: Two points must coincide
- **TangentConstraint**: A point must be tangent to a curve
- **DistanceConstraint**: Distance between two points with optional parameter
- **AngleConstraint**: Angle between two lines with optional parameter
- **ParallelConstraint**: Two lines must be parallel
- **PerpendicularConstraint**: Two lines must be perpendicular
- **EqualConstraint**: Two properties must have equal values

## Transformations

All CAD objects support transformations. The transformation system allows for:
- Translation
- Rotation
- Scaling
- Skewing
- Arbitrary transformation matrices

Transformations are stored as attributes or child elements:

```xml
<belfry:line id="line1" name="Transformed Line">
    <belfry:transformation>
        <belfry:translate x="10.0" y="5.0" />
        <belfry:rotate angle="45.0" center_x="0.0" center_y="0.0" />
        <belfry:scale factor="2.0" center_x="0.0" center_y="0.0" />
    </belfry:transformation>
    <belfry:start_point x="0.0" y="0.0" />
    <belfry:end_point x="10.0" y="0.0" />
</belfry:line>
```

## Complete Example

Here's a complete example of a BelfryCAD document:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<belfry:belfrycad_document version="1.0" xmlns:belfry="http://belfrydw.com/xml/BelfryCAD/1.0">
    <belfry:header>
        <belfry:preferences 
            units="inches" 
            precision="3" 
            use_fractions="false"
            grid_visible="true"
            show_rulers="true"
            canvas_bg_color="#ffffff"
            grid_color="#cccccc"
            selection_color="#0080ff"
        />
    </belfry:header>
    
    <belfry:parameters>
        <belfry:parameter name="radius" expression="2.5" />
        <belfry:parameter name="height" expression="2 * $radius" />
        <belfry:parameter name="angle" expression="45º" />
    </belfry:parameters>
    
    <belfry:objects>
        <belfry:group id="group1" name="Main Group" color="black" visible="true" locked="false">
            <belfry:line id="line1" name="Base Line" color="black" line_width="0.05" visible="true" locked="false">
                <belfry:start_point x="0.0" y="0.0" />
                <belfry:end_point x="10.0" y="0.0" />
            </belfry:line>
            
            <belfry:circle id="circle1" name="Main Circle" color="blue" line_width="0.05" visible="true" locked="false">
                <belfry:center_point x="5.0" y="5.0" />
                <belfry:radius value="$radius" />
            </belfry:circle>
            
            <belfry:arc id="arc1" name="Top Arc" color="red" line_width="0.05" visible="true" locked="false">
                <belfry:center_point x="5.0" y="5.0" />
                <belfry:radius value="$radius" />
                <belfry:start_angle value="0.0" />
                <belfry:span_angle value="$angle" />
            </belfry:arc>
        </belfry:group>
    </belfry:objects>
    
    <belfry:constraints>
        <!-- Line end point coincides with circle center -->
        <belfry:constraint id="constraint1" type="CoincidenceConstraint" 
                           constrainable1="line1.end_point" constrainable2="circle1.center_point" />
        
        <!-- Arc is tangent to circle -->
        <belfry:constraint id="constraint2" type="TangentConstraint" 
                           constrainable1="arc1" constrainable2="circle1" />
    </belfry:constraints>
</belfry:belfrycad_document>
```

## File Extension

BelfryCAD files use the `.belcad` extension, which represents a zip-compressed XML file.

## Implementation Notes

1. **Compression**: Files are compressed using ZIP DEFLATE algorithm
2. **Encoding**: XML uses UTF-8 encoding
3. **Validation**: XML should be validated against the schema (future enhancement)
4. **Backward Compatibility**: Version attribute allows for format evolution
5. **Error Handling**: Invalid files should be handled gracefully with user feedback

## Future Enhancements

- XML Schema Definition (XSD) for validation
- Binary data support for large geometries
- Incremental save support
- Version migration tools
- External reference support
- Enhanced grouping system 