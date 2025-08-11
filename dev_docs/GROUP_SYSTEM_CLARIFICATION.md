# Group System Clarification

## Overview

BelfryCAD uses a **group-based organization system** rather than layers. This document clarifies the distinction and explains how the group system works.

## Groups vs Layers

### Groups (Current System)
- **Hierarchical organization**: Groups can contain other groups and objects
- **Object ownership**: Objects belong to groups, not layers
- **Visibility inheritance**: Child objects inherit visibility from parent groups
- **Flexible structure**: Groups can be nested and reorganized
- **Object-centric**: Focus on organizing CAD objects themselves

### Layers (Not Used)
- **Flat organization**: Layers are typically flat, non-hierarchical
- **Rendering order**: Layers control drawing order and visibility
- **Style-based**: Layers often control line styles, colors, etc.
- **Traditional CAD**: Common in traditional CAD systems

## Group System Features

### Hierarchical Structure
```
Main Group
├── Subgroup A
│   ├── Line 1
│   └── Circle 1
├── Subgroup B
│   ├── Arc 1
│   └── Ellipse 1
└── Standalone Line 2
```

### Group Properties
- **Name**: Human-readable identifier
- **Color**: Visual color for the group
- **Visibility**: Show/hide the group and all children
- **Locked**: Prevent modifications to group contents
- **Children**: List of contained objects and subgroups

### Object Organization
- Objects can belong to groups or be at the root level
- Groups can contain other groups (nested hierarchy)
- Objects inherit visibility from their parent group
- Groups can be expanded/collapsed in the UI

## XML Representation

Groups are represented in the XML format as:

```xml
<belfry:group id="group1" name="Main Group" color="black" visible="true" locked="false">
    <belfry:line id="line1" name="Base Line">
        <belfry:start_point x="0.0" y="0.0" />
        <belfry:end_point x="10.0" y="0.0" />
    </belfry:line>
    
    <belfry:group id="subgroup1" name="Subgroup A">
        <belfry:circle id="circle1" name="Main Circle">
            <belfry:center_point x="5.0" y="5.0" />
            <belfry:radius value="3.0" />
        </belfry:circle>
    </belfry:group>
</belfry:group>
```

## UI Implementation

### Object Tree Pane
- Displays hierarchical group structure
- Shows groups with folder icons (📁)
- Allows expanding/collapsing groups
- Provides visibility toggles for groups and objects
- Supports drag-and-drop reorganization

### Group Management
- Create new groups
- Rename existing groups
- Move objects between groups
- Delete groups (with confirmation)
- Set group properties (color, visibility, lock)

## Benefits of Group System

1. **Intuitive Organization**: Natural way to organize related objects
2. **Flexible Hierarchy**: Can create complex organizational structures
3. **Inheritance**: Child objects inherit group properties
4. **Bulk Operations**: Apply operations to entire groups
5. **Clear Ownership**: Objects clearly belong to specific groups

## Icon Usage

The system uses icon names that reference "object" (e.g., "object-visible", "object-invisible") for visual indicators of visibility states. These icons represent object visibility, not layers.

## Future Considerations

While the current system uses groups, future enhancements could include:
- Enhanced grouping capabilities
- Group templates and presets
- Advanced group operations
- Group-based constraints
- Group export/import functionality

## Conclusion

BelfryCAD's group system provides a flexible, hierarchical way to organize CAD objects without the complexity of traditional layer systems. This approach is more intuitive for users and provides better organization capabilities for complex drawings. 