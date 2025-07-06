#!/usr/bin/env python3
"""
MLCNC Usage Examples

This script demonstrates how to use the MLCNC utilities
for CNC machining parameter optimization.
"""

from . import (
    FeedOptimizer, CuttingParameterCalculator,
    ToolPathOptimizer, MaterialDatabase
)
from .feed_optimizer import (
    MaterialType, CuttingParameters, OptimizationResult
)
from .cutting_params import (
    ToolSpecification, ToolGeometry, MachineCapabilities, CuttingCondition,
    ToolMaterial, ToolCoating, OperationType
)
from .tool_path import (
    GeometryBounds, MachiningParameters, PathStrategy, Point3D
)


def demonstrate_feed_optimizer():
    """Demonstrate feed rate optimization."""
    print("\n=== Feed Rate Optimization Demo ===")

    # Create feed optimizer
    optimizer = FeedOptimizer()

    # Define cutting parameters
    params = CuttingParameters(
        spindle_speed=5000,
        feed_rate=100,
        depth_of_cut=0.125,
        width_of_cut=0.5,
        tool_diameter=0.5,
        material=MaterialType.ALUMINUM
    )

    # Optimize parameters
    result = optimizer.optimize_parameters(
        params, tool_type="end_mill", flute_count=2, priority="balanced"
    )

    print(f"Original Feed Rate: {params.feed_rate} in/min")
    print(f"Optimized Feed Rate: {result.optimal_feed_rate:.1f} in/min")
    print(f"Optimized Spindle Speed: {result.optimal_spindle_speed:.0f} RPM")
    print(f"Chip Load: {result.chip_load:.4f} in/tooth")
    print(f"Material Removal Rate: {result.material_removal_rate:.3f} in³/min")
    print(f"Tool Life Estimate: {result.tool_life_estimate:.1f} hours")
    print(f"Power Consumption: {result.power_consumption:.0f} watts")
    print(f"Confidence: {result.confidence:.1%}")


def demonstrate_cutting_calculator():
    """Demonstrate cutting parameter calculations."""
    print("\n=== Cutting Parameter Calculator Demo ===")

    # Create calculator
    calculator = CuttingParameterCalculator()

    # Define tool specification
    tool = ToolSpecification(
        diameter=0.5,
        length=3.0,
        flute_count=2,
        geometry=ToolGeometry.SQUARE_END_MILL,
        material=ToolMaterial.CARBIDE,
        coating=ToolCoating.TiAlN
    )

    # Define cutting condition
    condition = CuttingCondition(
        tool=tool,
        material=MaterialType.STEEL,
        operation=OperationType.ROUGHING,
        depth_of_cut=0.1,
        width_of_cut=0.4,
        spindle_speed=4000,
        feed_rate=80
    )

    # Calculate forces
    forces = calculator.calculate_cutting_forces(condition)
    print(f"Cutting Forces:")
    print(f"  Tangential: {forces['tangential']:.1f} lbf")
    print(f"  Radial: {forces['radial']:.1f} lbf")
    print(f"  Axial: {forces['axial']:.1f} lbf")
    print(f"  Resultant: {forces['resultant']:.1f} lbf")

    # Calculate power
    power = calculator.calculate_power_consumption(condition)
    print(f"Power Consumption:")
    print(f"  Cutting: {power['cutting']:.2f} HP")
    print(f"  Total: {power['total']:.2f} HP")

    # Calculate tool deflection
    deflection = calculator.calculate_tool_deflection(condition)
    print(f"Tool Deflection:")
    print(f"  At tip: {deflection['tip']:.6f} in")
    print(f"  Allowable: {deflection['allowable']:.6f} in")


def demonstrate_path_optimizer():
    """Demonstrate tool path optimization."""
    print("\n=== Tool Path Optimizer Demo ===")

    # Create optimizer
    optimizer = ToolPathOptimizer()

    # Define geometry bounds
    bounds = GeometryBounds(
        min_x=0, max_x=4,
        min_y=0, max_y=2,
        min_z=-0.5, max_z=0
    )

    # Define machining parameters
    params = MachiningParameters(
        tool_diameter=0.5,
        stepover=0.4,
        stepdown=0.1,
        finish_allowance=0.01,
        ramp_angle=3.0,
        entry_angle=90.0,
        exit_angle=90.0
    )

    # Generate roughing path
    roughing_segments = optimizer.generate_roughing_path(
        bounds, params, PathStrategy.CONVENTIONAL
    )

    print(f"Generated {len(roughing_segments)} roughing segments")

    # Generate finishing path
    finishing_segments = optimizer.generate_finishing_path(
        bounds, params, surface_tolerance=0.001
    )

    print(f"Generated {len(finishing_segments)} finishing segments")

    # Calculate machining time
    all_segments = roughing_segments + finishing_segments
    time_analysis = optimizer.calculate_machining_time(all_segments)

    print(f"Time Analysis:")
    print(f"  Cutting time: {time_analysis['cutting']:.2f} minutes")
    print(f"  Rapid time: {time_analysis['rapid']:.2f} minutes")
    print(f"  Total time: {time_analysis['total']:.2f} minutes")


def demonstrate_material_database():
    """Demonstrate material database functionality."""
    print("\n=== Material Database Demo ===")

    # Create database
    db = MaterialDatabase()

    # List available materials
    materials = db.list_materials()
    print(f"Available materials: {len(materials)}")

    for material in materials[:3]:  # Show first 3
        print(f"  {material.material_id}: {material.name}")

    # Get specific material properties
    al6061 = db.get_material("AL6061")
    if al6061:
        density = db.get_property_value("AL6061", "density")
        tensile = db.get_property_value("AL6061", "tensile_strength")
        machinability = db.get_property_value("AL6061", "machinability_rating")

        print(f"\nAluminum 6061 Properties:")
        print(f"  Density: {density} lb/in³")
        print(f"  Tensile Strength: {tensile} psi")
        print(f"  Machinability Rating: {machinability}")

    # Search for materials
    steel_materials = db.search_materials("steel")
    print(f"\nFound {len(steel_materials)} steel materials")

    # Validate database
    validation = db.validate_database()
    print(f"\nDatabase validation:")
    print(f"  Total materials: {validation['total_materials']}")
    print(f"  Errors: {len(validation['errors'])}")
    print(f"  Warnings: {len(validation['warnings'])}")


def main():
    """Run all demonstrations."""
    print("MLCNC Utilities Demonstration")
    print("=" * 40)

    try:
        demonstrate_feed_optimizer()
        demonstrate_cutting_calculator()
        demonstrate_path_optimizer()
        demonstrate_material_database()

        print("\n=== Demo Complete ===")
        print("All MLCNC modules demonstrated successfully!")

    except Exception as e:
        print(f"Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()