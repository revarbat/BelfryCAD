# Complex Test Document

## Overview

The `complex_test_document.belcad` file is a comprehensive test document for BelfryCAD that demonstrates all major features of the system.

## Document Contents

### Objects (20 total)
- **5 LineCadObject**: Base plate rectangle and center line
- **5 CircleCadObject**: Mounting holes and reference circle
- **2 GearCadObject**: Drive and driven gears
- **1 ArcCadObject**: Spring representation
- **1 EllipseCadObject**: Elliptical cam
- **1 CubicBezierCadObject**: Decorative curve
- **5 GroupCadObject**: Organizational groups

### Parameters (15 total)
- **Base dimensions**: `base_width`, `base_height`
- **Hole specifications**: `hole_diameter`, `mounting_clearance`
- **Gear specifications**: `gear_ratio`, `gear_pressure_angle`, `gear_teeth_1`, `gear_teeth_2`, `gear_pitch_radius_1`, `gear_pitch_radius_2`
- **Spring specifications**: `spring_length`, `spring_coils`, `spring_diameter`
- **Geometric parameters**: `center_distance`, `angle_offset`

### Groups (5 total)
1. **Base Assembly**: Contains the 4 lines forming the base plate rectangle
2. **Mounting Holes**: Contains the 4 mounting holes
3. **Gear Assembly**: Contains the drive and driven gears
4. **Mechanism**: Contains spring, cam, and decorative elements
5. **Reference Elements**: Contains center line and reference circle

## Parameter Expressions

The document includes several parameter expressions that demonstrate the CadExpression system:

- `gear_teeth_2 = $gear_teeth_1 * $gear_ratio` → 20 * 2.5 = 50
- `gear_pitch_radius_2 = $gear_pitch_radius_1 * $gear_ratio` → 25.0 * 2.5 = 62.5

## Object Properties

### Colors
- **Black**: Base assembly lines
- **Blue**: Mounting holes
- **Red**: Gears
- **Green**: Spring and mechanism group
- **Purple**: Elliptical cam
- **Orange**: Decorative bezier curve
- **Gray**: Center line and reference group
- **Light Blue**: Reference circle

### Line Widths
- **0.5**: Base assembly lines
- **0.3**: Mounting holes and spring
- **0.4**: Gears and cam
- **0.2**: Center line and reference elements

## Usage

### Generate the Document
```bash
python examples/complex_test_document.py
```

### Test the Document
```bash
python examples/test_complex_document.py
```

### Load in Your Application
```python
from BelfryCAD.utils.xml_serializer import load_belfrycad_document

document = load_belfrycad_document("complex_test_document.belcad")
```

## Test Scenarios

This document is ideal for testing:

1. **Object Loading**: All CAD object types
2. **Parameter Evaluation**: Complex expressions with variables
3. **Group Hierarchy**: Nested group structures
4. **Object Properties**: Colors, line widths, visibility, locking
5. **Parent-Child Relationships**: Group membership
6. **Document Preferences**: Units, precision, display settings
7. **Serialization**: Save/load functionality
8. **UI Rendering**: Object tree display
9. **Constraint System**: Future constraint testing
10. **Performance**: Large document handling

## Document Structure

```
Base Assembly (Group)
├── Base Line 1 (Line)
├── Base Line 2 (Line)
├── Base Line 3 (Line)
└── Base Line 4 (Line)

Mounting Holes (Group)
├── Mounting Hole 1 (Circle)
├── Mounting Hole 2 (Circle)
├── Mounting Hole 3 (Circle)
└── Mounting Hole 4 (Circle)

Gear Assembly (Group)
├── Drive Gear (Gear)
└── Driven Gear (Gear)

Mechanism (Group)
├── Spring Arc (Arc)
├── Elliptical Cam (Ellipse)
└── Decorative Bezier (CubicBezier)

Reference Elements (Group)
├── Center Line (Line)
└── Reference Circle (Circle)
```

## File Information

- **Filename**: `complex_test_document.belcad`
- **Format**: ZIP-compressed XML
- **Namespace**: `http://belfrydw.com/xml/BelfryCAD/1.0`
- **Version**: 1.0
- **Units**: mm
- **Precision**: 2 decimal places

## Validation

The document has been validated to ensure:
- All objects load correctly
- Parameters evaluate properly
- Groups maintain their hierarchy
- Object properties are preserved
- Parent-child relationships are intact
- CadExpression system works correctly

This document serves as a comprehensive test case for all BelfryCAD functionality and can be used for development, testing, and demonstration purposes. 