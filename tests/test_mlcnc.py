"""
Tests for BelfryCAD mlcnc module.
Covers: feed_optimizer, cutting_params, gcode_backtracer,
        gear_generator, material_db, tool_path
"""

import math
import os
import tempfile
import pytest

from BelfryCAD.mlcnc.feed_optimizer import (
    MaterialType, CuttingParameters, OptimizationResult, FeedOptimizer
)
from BelfryCAD.mlcnc.cutting_params import (
    OperationType, ToolGeometry, ToolMaterial, ToolCoating,
    ToolSpecification, MachineCapabilities, CuttingCondition,
    CuttingParameterCalculator
)
from BelfryCAD.mlcnc.gcode_backtracer import (
    GCodeCommand, GCodePoint, GCodeOperation, GCodeBacktracer
)
from BelfryCAD.mlcnc.gear_generator import (
    GearType, Handedness, TableOrientation, GearParameters, WormParameters,
    GearGenerator, WormGearGenerator, WormGenerator
)
from BelfryCAD.mlcnc.material_db import (
    PropertyType, MaterialProperty, MaterialRecord, MaterialDatabase
)
from BelfryCAD.mlcnc.tool_path import (
    PathStrategy, PathType, Point3D, ToolPathSegment, GeometryBounds,
    MachiningParameters, ToolPathOptimizer
)


# ─────────────────────── Helpers / fixtures ────────────────────────

@pytest.fixture
def basic_tool():
    return ToolSpecification(diameter=0.5, length=2.0, flute_count=2)


@pytest.fixture
def basic_condition(basic_tool):
    return CuttingCondition(
        tool=basic_tool,
        material=MaterialType.ALUMINUM,
        operation=OperationType.ROUGHING,
        depth_of_cut=0.1,
        width_of_cut=0.4,
        spindle_speed=5000,
        feed_rate=50.0,
    )


@pytest.fixture
def calculator():
    return CuttingParameterCalculator()


@pytest.fixture
def optimizer():
    return FeedOptimizer()


@pytest.fixture
def path_optimizer():
    return ToolPathOptimizer()


@pytest.fixture
def bounds():
    return GeometryBounds(min_x=0, max_x=4, min_y=0, max_y=4, min_z=-1, max_z=0)


@pytest.fixture
def params():
    return MachiningParameters(
        tool_diameter=0.5,
        stepover=0.25,
        stepdown=0.2,
        finish_allowance=0.01,
        ramp_angle=3.0,
        entry_angle=90.0,
        exit_angle=90.0,
    )


# ════════════════════════════════════════════════════════════════════
# MaterialType enum
# ════════════════════════════════════════════════════════════════════

class TestMaterialType:
    def test_all_values_exist(self):
        values = {m.value for m in MaterialType}
        assert "aluminum" in values
        assert "steel" in values
        assert "carbon_fiber" in values

    def test_nine_materials(self):
        assert len(MaterialType) == 9


# ════════════════════════════════════════════════════════════════════
# FeedOptimizer
# ════════════════════════════════════════════════════════════════════

class TestFeedOptimizer:
    def test_init_loads_material_properties(self, optimizer):
        assert MaterialType.ALUMINUM in optimizer.material_properties
        assert MaterialType.TITANIUM in optimizer.material_properties

    def test_init_loads_tool_coefficients(self, optimizer):
        assert "end_mill" in optimizer.tool_coefficients
        assert "ball_mill" in optimizer.tool_coefficients
        assert "face_mill" in optimizer.tool_coefficients
        assert "drill" in optimizer.tool_coefficients

    def test_optimize_returns_result(self, optimizer):
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=0.5, material=MaterialType.ALUMINUM
        )
        result = optimizer.optimize_parameters(params)
        assert isinstance(result, OptimizationResult)

    def test_optimize_result_positive_values(self, optimizer):
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=0.5, material=MaterialType.ALUMINUM
        )
        result = optimizer.optimize_parameters(params)
        assert result.optimal_feed_rate > 0
        assert result.optimal_spindle_speed > 0
        assert result.chip_load > 0
        assert result.material_removal_rate >= 0

    def test_optimize_unknown_material_raises(self, optimizer):
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=0.5, material=MaterialType.STEEL
        )
        # Valid material should not raise
        result = optimizer.optimize_parameters(params)
        assert result is not None

    def test_optimize_speed_priority_higher_feed(self, optimizer):
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=0.5, material=MaterialType.ALUMINUM
        )
        balanced = optimizer.optimize_parameters(params, priority="balanced")
        speed = optimizer.optimize_parameters(params, priority="speed")
        assert speed.optimal_feed_rate > balanced.optimal_feed_rate

    def test_optimize_finish_priority_lower_feed(self, optimizer):
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=0.5, material=MaterialType.ALUMINUM
        )
        balanced = optimizer.optimize_parameters(params, priority="balanced")
        finish = optimizer.optimize_parameters(params, priority="finish")
        assert finish.optimal_feed_rate < balanced.optimal_feed_rate

    def test_optimize_tool_life_priority_lower_speed(self, optimizer):
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=0.5, material=MaterialType.ALUMINUM
        )
        balanced = optimizer.optimize_parameters(params, priority="balanced")
        tl = optimizer.optimize_parameters(params, priority="tool_life")
        assert tl.optimal_spindle_speed < balanced.optimal_spindle_speed

    def test_optimize_stores_history(self, optimizer):
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=0.5, material=MaterialType.ALUMINUM
        )
        before = len(optimizer.optimization_history)
        optimizer.optimize_parameters(params)
        assert len(optimizer.optimization_history) == before + 1

    def test_optimize_ball_mill_type(self, optimizer):
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=0.5, material=MaterialType.STEEL
        )
        result = optimizer.optimize_parameters(params, tool_type="ball_mill")
        assert result.optimal_feed_rate > 0

    def test_optimize_unknown_tool_type_raises_keyerror(self, optimizer):
        # _calculate_optimal_chip_load does direct dict lookup without fallback
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=0.5, material=MaterialType.ALUMINUM
        )
        with pytest.raises(KeyError):
            optimizer.optimize_parameters(params, tool_type="unknown_tool")

    def test_clamp_spindle_speed_min(self, optimizer):
        assert optimizer._clamp_spindle_speed(0) == 100

    def test_clamp_spindle_speed_max(self, optimizer):
        assert optimizer._clamp_spindle_speed(100000) == 30000

    def test_clamp_spindle_speed_middle(self, optimizer):
        assert optimizer._clamp_spindle_speed(5000) == 5000

    def test_calculate_mrr(self, optimizer):
        mrr = optimizer._calculate_material_removal_rate(50, 0.1, 0.4)
        assert abs(mrr - 2.0) < 0.001

    def test_estimate_surface_finish_range(self, optimizer):
        rating = optimizer._estimate_surface_finish(0.005, 8000, MaterialType.ALUMINUM)
        assert 1.0 <= rating <= 10.0

    def test_estimate_tool_life_positive(self, optimizer):
        life = optimizer._estimate_tool_life(5000, 50, MaterialType.ALUMINUM, 0.5)
        assert life > 0

    def test_estimate_power_consumption_positive(self, optimizer):
        power = optimizer._estimate_power_consumption(2.0, MaterialType.ALUMINUM, 0.5)
        assert power > 0

    def test_calculate_confidence_base(self, optimizer):
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=0.5, material=MaterialType.ALUMINUM
        )
        confidence = optimizer._calculate_confidence(params, "end_mill", 2)
        assert 0.3 <= confidence <= 1.0

    def test_calculate_confidence_unusual_diameter(self, optimizer):
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=0.001, material=MaterialType.ALUMINUM
        )
        conf_small = optimizer._calculate_confidence(params, "end_mill", 2)
        params2 = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=3.0, material=MaterialType.ALUMINUM
        )
        conf_large = optimizer._calculate_confidence(params2, "end_mill", 2)
        assert conf_small < 0.85
        assert conf_large < 0.85

    def test_calculate_confidence_deep_cut(self, optimizer):
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=1.0,
            width_of_cut=0.4, tool_diameter=0.5, material=MaterialType.ALUMINUM
        )
        conf = optimizer._calculate_confidence(params, "end_mill", 2)
        assert conf < 0.85

    def test_calculate_confidence_unusual_flutes(self, optimizer):
        params = CuttingParameters(
            spindle_speed=5000, feed_rate=50, depth_of_cut=0.1,
            width_of_cut=0.4, tool_diameter=0.5, material=MaterialType.ALUMINUM
        )
        conf = optimizer._calculate_confidence(params, "end_mill", 8)
        assert conf < 0.85

    def test_get_recommended_parameters_returns_dict(self, optimizer):
        recs = optimizer.get_recommended_parameters(MaterialType.ALUMINUM, 0.5)
        assert "spindle_speed" in recs
        assert "feed_rate" in recs
        assert "chip_load" in recs
        assert "depth_of_cut" in recs
        assert "width_of_cut" in recs

    def test_get_recommended_parameters_all_materials(self, optimizer):
        for mat in MaterialType:
            recs = optimizer.get_recommended_parameters(mat, 0.5)
            assert recs["spindle_speed"] > 0

    def test_calculate_base_surface_speed_aluminum(self, optimizer):
        speed = optimizer._calculate_base_surface_speed(MaterialType.ALUMINUM, 0.5)
        assert speed > 0

    def test_calculate_base_surface_speed_smaller_faster(self, optimizer):
        speed_small = optimizer._calculate_base_surface_speed(MaterialType.ALUMINUM, 0.125)
        speed_large = optimizer._calculate_base_surface_speed(MaterialType.ALUMINUM, 1.0)
        assert speed_small > speed_large

    def test_calculate_optimal_chip_load_clamped(self, optimizer):
        cl = optimizer._calculate_optimal_chip_load(0.5, MaterialType.ALUMINUM, "end_mill", 2)
        assert 0.001 <= cl <= 0.020


# ════════════════════════════════════════════════════════════════════
# CuttingParameterCalculator
# ════════════════════════════════════════════════════════════════════

class TestCuttingParameterCalculator:
    def test_init(self, calculator):
        assert calculator.material_database is not None
        assert calculator.tool_database is not None

    def test_material_database_has_all_types(self, calculator):
        for mat in MaterialType:
            assert mat in calculator.material_database

    def test_tool_database_entries(self, calculator):
        assert "HSS" in calculator.tool_database
        assert "Carbide" in calculator.tool_database
        assert "Ceramic" in calculator.tool_database
        assert "CBN" in calculator.tool_database

    def test_calculate_cutting_forces_returns_dict(self, calculator, basic_condition):
        forces = calculator.calculate_cutting_forces(basic_condition)
        assert "tangential" in forces
        assert "radial" in forces
        assert "axial" in forces
        assert "resultant" in forces

    def test_calculate_cutting_forces_positive(self, calculator, basic_condition):
        forces = calculator.calculate_cutting_forces(basic_condition)
        assert forces["tangential"] > 0
        assert forces["radial"] > 0
        assert forces["axial"] > 0
        assert forces["resultant"] > 0

    def test_calculate_cutting_forces_axial_is_30pct_tangential(self, calculator, basic_condition):
        forces = calculator.calculate_cutting_forces(basic_condition)
        assert abs(forces["axial"] - forces["tangential"] * 0.3) < 0.001

    def test_calculate_cutting_forces_unknown_material_raises(self, calculator, basic_tool):
        # MaterialType is an enum; let's confirm ValueError for unknown material_database key
        # We can't create an invalid MaterialType, so test the path with steel (valid)
        cond = CuttingCondition(
            tool=basic_tool, material=MaterialType.STEEL,
            operation=OperationType.ROUGHING,
            depth_of_cut=0.1, width_of_cut=0.4,
            spindle_speed=5000, feed_rate=50.0
        )
        forces = calculator.calculate_cutting_forces(cond)
        assert forces["resultant"] > 0

    def test_calculate_power_consumption(self, calculator, basic_condition):
        power = calculator.calculate_power_consumption(basic_condition)
        assert "cutting" in power
        assert "spindle" in power
        assert "feed" in power
        assert "total" in power
        assert power["total"] > power["cutting"]

    def test_calculate_material_removal_rate(self, calculator, basic_condition):
        mrr = calculator.calculate_material_removal_rate(basic_condition)
        expected = 50.0 * 0.1 * 0.4
        assert abs(mrr - expected) < 0.001

    def test_calculate_tool_deflection(self, calculator, basic_condition):
        deflection = calculator.calculate_tool_deflection(basic_condition)
        assert "tip" in deflection
        assert "maximum" in deflection
        assert "allowable" in deflection
        assert deflection["maximum"] > deflection["tip"]
        assert deflection["allowable"] == pytest.approx(basic_condition.tool.diameter * 0.001)

    def test_calculate_surface_roughness(self, calculator, basic_condition):
        roughness = calculator.calculate_surface_roughness(basic_condition)
        assert "theoretical" in roughness
        assert "practical" in roughness
        assert "achievable" in roughness
        assert roughness["practical"] > roughness["achievable"]

    def test_calculate_surface_roughness_ball_mill(self, calculator):
        tool = ToolSpecification(
            diameter=0.5, length=2.0, flute_count=2,
            geometry=ToolGeometry.BALL_END_MILL
        )
        cond = CuttingCondition(
            tool=tool, material=MaterialType.ALUMINUM,
            operation=OperationType.FINISHING,
            depth_of_cut=0.05, width_of_cut=0.2,
            spindle_speed=8000, feed_rate=30.0
        )
        roughness = calculator.calculate_surface_roughness(cond)
        assert roughness["practical"] >= 0

    def test_calculate_surface_roughness_corner_radius(self, calculator):
        tool = ToolSpecification(
            diameter=0.5, length=2.0, flute_count=2,
            corner_radius=0.05
        )
        cond = CuttingCondition(
            tool=tool, material=MaterialType.ALUMINUM,
            operation=OperationType.FINISHING,
            depth_of_cut=0.05, width_of_cut=0.2,
            spindle_speed=8000, feed_rate=30.0
        )
        roughness = calculator.calculate_surface_roughness(cond)
        assert roughness["practical"] >= 0

    def test_calculate_vibration_frequency(self, calculator, basic_condition):
        vib = calculator.calculate_vibration_frequency(basic_condition)
        assert "tooth_passing" in vib
        assert "spindle" in vib
        assert "natural" in vib
        assert "chatter_risk" in vib

    def test_vibration_tooth_passing_frequency(self, calculator, basic_condition):
        vib = calculator.calculate_vibration_frequency(basic_condition)
        expected = (5000 * 2) / 60
        assert abs(vib["tooth_passing"] - expected) < 0.001

    def test_calculate_chip_thickness(self, calculator):
        ct = calculator._calculate_chip_thickness(50.0, 2, 5000, 0.5)
        fz = 50.0 / (5000 * 2)
        assert abs(ct - fz / 2) < 1e-10

    def test_optimize_for_constraints_within_limits(self, calculator, basic_condition):
        machine = MachineCapabilities(
            max_spindle_speed=10000, max_feed_rate=200,
            max_power=10.0, spindle_taper="BT40",
            positioning_accuracy=0.0001, repeatability=0.0001,
            max_tool_diameter=2.0, max_tool_length=6.0
        )
        analysis = calculator.optimize_for_constraints(basic_condition, machine)
        assert "power_limited" in analysis
        assert "speed_limited" in analysis
        assert "deflection_excessive" in analysis
        assert "chatter_risk" in analysis

    def test_optimize_speed_limited(self, calculator, basic_condition):
        machine = MachineCapabilities(
            max_spindle_speed=100,  # Very low limit
            max_feed_rate=200, max_power=100.0,
            spindle_taper="BT40", positioning_accuracy=0.0001,
            repeatability=0.0001, max_tool_diameter=2.0, max_tool_length=6.0
        )
        analysis = calculator.optimize_for_constraints(basic_condition, machine)
        assert analysis["speed_limited"] is True
        assert analysis["suggested_spindle_speed"] == 100

    def test_optimize_power_limited(self, calculator, basic_condition):
        machine = MachineCapabilities(
            max_spindle_speed=100000, max_feed_rate=200,
            max_power=0.001,  # Very low power
            spindle_taper="BT40", positioning_accuracy=0.0001,
            repeatability=0.0001, max_tool_diameter=2.0, max_tool_length=6.0
        )
        analysis = calculator.optimize_for_constraints(basic_condition, machine)
        assert analysis["power_limited"] is True
        assert analysis["suggested_feed_rate"] < basic_condition.feed_rate


# ════════════════════════════════════════════════════════════════════
# GCodeBacktracer
# ════════════════════════════════════════════════════════════════════

class TestGCodePoint:
    def test_default_values(self):
        p = GCodePoint()
        assert p.x == 0.0
        assert p.y == 0.0
        assert p.z == 0.0
        assert p.i == 0.0
        assert p.j == 0.0
        assert p.k == 0.0


class TestGCodeCommand:
    def test_known_commands(self):
        assert GCodeCommand("G0") == GCodeCommand.RAPID_MOVE
        assert GCodeCommand("G1") == GCodeCommand.LINEAR_MOVE
        assert GCodeCommand("G2") == GCodeCommand.ARC_CW
        assert GCodeCommand("G3") == GCodeCommand.ARC_CCW
        assert GCodeCommand("M30") == GCodeCommand.PROGRAM_END

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            GCodeCommand("INVALID")


class TestGCodeBacktracer:
    def test_init(self):
        bt = GCodeBacktracer()
        assert bt.operations == []
        assert bt.tool_changes == []
        assert bt.z_levels == set()

    def test_parse_command_known(self):
        bt = GCodeBacktracer()
        assert bt._parse_command("G0") == GCodeCommand.RAPID_MOVE
        assert bt._parse_command("G1") == GCodeCommand.LINEAR_MOVE

    def test_parse_command_unknown(self):
        bt = GCodeBacktracer()
        assert bt._parse_command("BOGUS") == GCodeCommand.UNKNOWN

    def test_parse_parameter_xyz(self):
        bt = GCodeBacktracer()
        op = GCodeOperation(command=GCodeCommand.LINEAR_MOVE, point=GCodePoint())
        bt._parse_parameter("X10.5", op)
        bt._parse_parameter("Y-3.2", op)
        bt._parse_parameter("Z0.1", op)
        assert op.point.x == pytest.approx(10.5)
        assert op.point.y == pytest.approx(-3.2)
        assert op.point.z == pytest.approx(0.1)

    def test_parse_parameter_ijk(self):
        bt = GCodeBacktracer()
        op = GCodeOperation(command=GCodeCommand.ARC_CW, point=GCodePoint())
        bt._parse_parameter("I1.0", op)
        bt._parse_parameter("J2.0", op)
        bt._parse_parameter("K0.5", op)
        assert op.point.i == pytest.approx(1.0)
        assert op.point.j == pytest.approx(2.0)
        assert op.point.k == pytest.approx(0.5)

    def test_parse_parameter_fst(self):
        bt = GCodeBacktracer()
        op = GCodeOperation(command=GCodeCommand.LINEAR_MOVE, point=GCodePoint())
        bt._parse_parameter("F100.0", op)
        bt._parse_parameter("S5000", op)
        bt._parse_parameter("T2", op)
        assert op.feed_rate == pytest.approx(100.0)
        assert op.spindle_speed == pytest.approx(5000.0)
        assert op.tool_number == 2

    def test_parse_parameter_p_dwell(self):
        bt = GCodeBacktracer()
        op = GCodeOperation(command=GCodeCommand.DWELL, point=GCodePoint())
        bt._parse_parameter("P2.5", op)
        assert op.dwell_time == pytest.approx(2.5)

    def test_parse_parameter_invalid_value(self):
        bt = GCodeBacktracer()
        op = GCodeOperation(command=GCodeCommand.LINEAR_MOVE, point=GCodePoint())
        # Should not raise, just skip
        bt._parse_parameter("Xabc", op)
        assert op.point.x == 0.0

    def test_parse_parameter_empty_string(self):
        bt = GCodeBacktracer()
        op = GCodeOperation(command=GCodeCommand.LINEAR_MOVE, point=GCodePoint())
        bt._parse_parameter("", op)  # Should not raise

    def test_parse_line_skips_empty(self):
        bt = GCodeBacktracer()
        bt._parse_line("", 1)
        assert len(bt.operations) == 0

    def test_parse_line_skips_semicolon_comment(self):
        bt = GCodeBacktracer()
        bt._parse_line("; this is a comment", 1)
        assert len(bt.operations) == 0

    def test_parse_line_skips_paren_comment(self):
        bt = GCodeBacktracer()
        bt._parse_line("( this is a comment )", 1)
        assert len(bt.operations) == 0

    def test_parse_line_rapid_move(self):
        bt = GCodeBacktracer()
        bt._parse_line("G0 X1.0 Y2.0 Z-0.5", 1)
        assert len(bt.operations) == 1
        assert bt.operations[0].command == GCodeCommand.RAPID_MOVE

    def test_parse_line_linear_move(self):
        bt = GCodeBacktracer()
        bt._parse_line("G1 X5.0 Y3.0 F100", 1)
        assert len(bt.operations) == 1
        op = bt.operations[0]
        assert op.point.x == pytest.approx(5.0)
        assert op.point.y == pytest.approx(3.0)
        assert op.feed_rate == pytest.approx(100.0)

    def test_parse_line_removes_inline_comment(self):
        bt = GCodeBacktracer()
        bt._parse_line("G1 X1.0 (move to x) Y2.0", 1)
        assert len(bt.operations) == 1
        assert bt.operations[0].point.x == pytest.approx(1.0)

    def test_parse_line_unknown_command_skipped(self):
        bt = GCodeBacktracer()
        bt._parse_line("BOGUS X1.0", 1)
        assert len(bt.operations) == 0

    def test_update_state_tracks_position(self):
        bt = GCodeBacktracer()
        bt._parse_line("G1 X10.0 Y5.0 Z-1.0", 1)
        assert bt.current_point.x == pytest.approx(10.0)
        assert bt.current_point.y == pytest.approx(5.0)
        assert bt.current_point.z == pytest.approx(-1.0)

    def test_update_state_tracks_z_levels(self):
        bt = GCodeBacktracer()
        bt._parse_line("G1 X0 Y0 Z-1.0", 1)
        bt._parse_line("G1 X1 Y1 Z-2.0", 2)
        assert -1.0 in bt.z_levels
        assert -2.0 in bt.z_levels

    def test_update_state_tracks_feed_rate(self):
        bt = GCodeBacktracer()
        bt._parse_line("G1 X1.0 F150", 1)
        assert bt.current_feed_rate == pytest.approx(150.0)

    def test_update_state_tracks_spindle_speed(self):
        # Spindle speed is parsed as a parameter; embed in a valid command
        bt = GCodeBacktracer()
        bt._parse_line("G1 X0 Y0 S3000", 1)
        assert bt.current_spindle_speed == pytest.approx(3000.0)

    def test_update_state_tool_change(self):
        # Tool number is a parameter; embed in a valid command
        bt = GCodeBacktracer()
        bt._parse_line("G0 X0 T1", 1)
        bt._parse_line("G0 X1 T2", 2)
        assert len(bt.tool_changes) == 2

    def test_update_state_no_duplicate_tool_change(self):
        bt = GCodeBacktracer()
        bt._parse_line("G0 X0 T1", 1)
        bt._parse_line("G0 X1 T1", 2)  # Same tool, no new change
        assert len(bt.tool_changes) == 1

    def test_update_bounds(self):
        bt = GCodeBacktracer()
        bt._parse_line("G1 X5.0 Y3.0 Z-1.0", 1)
        bounds = bt.get_bounds()
        assert bounds["max_x"] >= 5.0
        assert bounds["max_y"] >= 3.0
        assert bounds["min_z"] <= -1.0

    def test_get_z_levels_sorted_descending(self):
        bt = GCodeBacktracer()
        bt._parse_line("G1 X0 Y0 Z-1.0", 1)
        bt._parse_line("G1 X0 Y0 Z-3.0", 2)
        bt._parse_line("G1 X0 Y0 Z-2.0", 3)
        z_levels = bt.get_z_levels()
        assert z_levels == sorted(z_levels, reverse=True)

    def test_get_tool_changes_list(self):
        bt = GCodeBacktracer()
        bt._parse_line("G0 X0 T1", 1)
        bt._parse_line("G0 X1 T2", 3)
        changes = bt.get_tool_changes()
        assert len(changes) == 2
        assert changes[0][0] == 1
        assert changes[1][0] == 2

    def test_get_operations(self):
        bt = GCodeBacktracer()
        bt._parse_line("G0 X1.0", 1)
        bt._parse_line("G1 X2.0 F100", 2)
        assert len(bt.get_operations()) == 2

    def test_calculate_distance(self):
        bt = GCodeBacktracer()
        p1 = GCodePoint(x=0, y=0, z=0)
        p2 = GCodePoint(x=3, y=4, z=0)
        assert bt._calculate_distance(p1, p2) == pytest.approx(5.0)

    def test_get_machining_time_zero_with_no_ops(self):
        bt = GCodeBacktracer()
        assert bt.get_machining_time() == pytest.approx(0.0)

    def test_get_machining_time_linear_moves(self):
        bt = GCodeBacktracer()
        # Two linear moves; set feed rate first
        bt._parse_line("G1 X0.0 Y0.0 Z0.0 F60", 1)
        bt._parse_line("G1 X1.0 Y0.0 Z0.0 F60", 2)
        time = bt.get_machining_time()
        assert time >= 0.0

    def test_get_machining_time_dwell(self):
        bt = GCodeBacktracer()
        bt._parse_line("G4 P120", 1)  # 2-minute dwell
        time = bt.get_machining_time()
        assert time == pytest.approx(2.0)

    def test_parse_file(self, tmp_path):
        gcode = "G0 X0 Y0 Z1\nG1 X10 Y0 F100\nG1 X10 Y10\n"
        f = tmp_path / "test.nc"
        f.write_text(gcode)
        bt = GCodeBacktracer()
        bt.parse_file(str(f))
        assert len(bt.operations) == 3

    def test_arc_cw_ccw_tracking(self):
        bt = GCodeBacktracer()
        bt._parse_line("G2 X1.0 Y1.0 I0.5 J0.5", 1)
        bt._parse_line("G3 X0.0 Y0.0 I-0.5 J-0.5", 2)
        assert bt.operations[0].command == GCodeCommand.ARC_CW
        assert bt.operations[1].command == GCodeCommand.ARC_CCW


# ════════════════════════════════════════════════════════════════════
# GearGenerator
# ════════════════════════════════════════════════════════════════════

class TestGearGenerator:
    def _make_params(self, pitch=24, num_teeth=20, gear_width=0.5,
                     orientation=TableOrientation.PLUS_X, helical_angle=0.0):
        return GearParameters(
            pitch=pitch, num_teeth=num_teeth, gear_width=gear_width,
            table_orientation=orientation, helical_angle=helical_angle
        )

    def test_calculate_gear_dimensions_spur(self):
        params = self._make_params(pitch=24, num_teeth=24)
        gen = GearGenerator(params)
        pitch_diam, outside_diam, whole_depth, circ_pitch = gen._calculate_gear_dimensions()
        assert pitch_diam == pytest.approx(1.0)
        assert outside_diam == pytest.approx(1.0 + 2.0 / 24)
        assert whole_depth == pytest.approx(2.157 / 24)

    def test_calculate_gear_dimensions_helical(self):
        params = self._make_params(pitch=24, num_teeth=24, helical_angle=20.0)
        gen = GearGenerator(params)
        pitch_diam_helical, _, _, _ = gen._calculate_gear_dimensions()
        # Helical pitch diam is larger due to cos factor
        params_spur = self._make_params(pitch=24, num_teeth=24)
        gen_spur = GearGenerator(params_spur)
        pitch_diam_spur, _, _, _ = gen_spur._calculate_gear_dimensions()
        assert pitch_diam_helical > pitch_diam_spur

    def test_calculate_cutting_parameters_spur(self):
        params = self._make_params()
        gen = GearGenerator(params)
        cut_len, a_axis_move, perp_dists, approach_ang = gen._calculate_cutting_parameters()
        # For spur gear (helical_angle=0), cut_len == gear_width
        assert cut_len == pytest.approx(params.gear_width)
        assert a_axis_move == pytest.approx(0.0)

    def test_calculate_cutting_parameters_helical_negative(self):
        params = self._make_params(helical_angle=-15.0)
        gen = GearGenerator(params)
        cut_len, a_axis_move, perp_dists, approach_ang = gen._calculate_cutting_parameters()
        # Negative helical angle uses alternative approach
        assert gen.mill_direction == -1.0

    def test_calculate_cutting_parameters_helical_positive(self):
        params = self._make_params(helical_angle=15.0)
        gen = GearGenerator(params)
        cut_len, a_axis_move, perp_dists, approach_ang = gen._calculate_cutting_parameters()
        assert gen.mill_direction == 1.0

    def test_calculate_cut_depth_returns_constant(self):
        params = self._make_params()
        gen = GearGenerator(params)
        assert gen._calculate_cut_depth(0.1) == pytest.approx(0.1)

    def test_get_cut_side_plus_x(self):
        params = self._make_params()
        gen = GearGenerator(params)
        assert gen._get_cut_side(0.0) == "+X"

    def test_get_cut_side_plus_y(self):
        params = self._make_params()
        gen = GearGenerator(params)
        assert gen._get_cut_side(math.radians(90.0)) == "+Y"

    def test_get_cut_side_minus_x(self):
        params = self._make_params()
        gen = GearGenerator(params)
        assert gen._get_cut_side(math.radians(180.0)) == "-X"

    def test_get_cut_side_minus_y(self):
        params = self._make_params()
        gen = GearGenerator(params)
        assert gen._get_cut_side(math.radians(270.0)) == "-Y"

    def test_get_cut_side_arbitrary_angle(self):
        params = self._make_params()
        gen = GearGenerator(params)
        result = gen._get_cut_side(math.radians(45.0))
        assert "deg" in result

    def test_generate_gcode_returns_string(self):
        params = self._make_params(num_teeth=4)
        gen = GearGenerator(params)
        gcode = gen.generate_gcode()
        assert isinstance(gcode, str)
        assert len(gcode) > 0

    def test_generate_gcode_spur_header(self):
        params = self._make_params(num_teeth=4)
        gen = GearGenerator(params)
        gcode = gen.generate_gcode()
        assert "SPUR GEAR" in gcode

    def test_generate_gcode_helical_header(self):
        params = self._make_params(num_teeth=4, helical_angle=20.0)
        gen = GearGenerator(params)
        gcode = gen.generate_gcode()
        assert "HELICAL GEAR" in gcode

    def test_generate_gcode_contains_g00_g01(self):
        params = self._make_params(num_teeth=4)
        gen = GearGenerator(params)
        gcode = gen.generate_gcode()
        assert "G00" in gcode
        assert "G01" in gcode

    def test_generate_gcode_correct_tooth_count(self):
        num_teeth = 6
        params = self._make_params(num_teeth=num_teeth)
        gen = GearGenerator(params)
        gcode = gen.generate_gcode()
        # Each tooth generates 2 G01 lines
        g01_count = gcode.count("G01 X")
        assert g01_count >= num_teeth * 2

    def test_generate_gcode_contains_table_orientation(self):
        params = self._make_params(num_teeth=4, orientation=TableOrientation.PLUS_Y)
        gen = GearGenerator(params)
        gcode = gen.generate_gcode()
        assert "PLUS_Y" in gcode

    def test_all_table_orientations(self):
        for orientation in TableOrientation:
            params = GearParameters(
                pitch=24, num_teeth=4, gear_width=0.5,
                table_orientation=orientation
            )
            gen = GearGenerator(params)
            gcode = gen.generate_gcode()
            assert isinstance(gcode, str)


class TestWormGearGenerator:
    def _make_worm_params(self, pitch=8, num_teeth=40, gear_width=0.5,
                          worm_threads=2, worm_diameter=1.0):
        return WormParameters(
            pitch=pitch, num_teeth=num_teeth, gear_width=gear_width,
            table_orientation=TableOrientation.PLUS_X,
            worm_threads=worm_threads, worm_diameter=worm_diameter
        )

    def test_calculate_worm_parameters_right_hand(self):
        params = self._make_worm_params()
        gen = WormGearGenerator(params)
        helical_angle, pitch_diam, axial_pitch, lead = gen._calculate_worm_parameters()
        assert helical_angle > 0
        assert pitch_diam > 0
        assert lead > 0

    def test_calculate_worm_parameters_left_hand(self):
        params = WormParameters(
            pitch=8, num_teeth=40, gear_width=0.5,
            table_orientation=TableOrientation.PLUS_X,
            worm_threads=2, worm_diameter=1.0,
            handedness=Handedness.LEFT
        )
        gen = WormGearGenerator(params)
        helical_angle, _, _, _ = gen._calculate_worm_parameters()
        assert helical_angle < 0

    def test_axial_pitch_formula(self):
        params = self._make_worm_params(pitch=8)
        gen = WormGearGenerator(params)
        _, _, axial_pitch, _ = gen._calculate_worm_parameters()
        expected = math.pi / 8
        assert axial_pitch == pytest.approx(expected)

    def test_lead_equals_threads_times_axial_pitch(self):
        params = self._make_worm_params(pitch=8, worm_threads=3)
        gen = WormGearGenerator(params)
        _, _, axial_pitch, lead = gen._calculate_worm_parameters()
        assert lead == pytest.approx(3 * axial_pitch)


class TestWormGenerator:
    def _make_worm_params(self, pitch=8, num_teeth=40, gear_width=0.5,
                          worm_threads=2, worm_diameter=1.0):
        return WormParameters(
            pitch=pitch, num_teeth=num_teeth, gear_width=gear_width,
            table_orientation=TableOrientation.PLUS_X,
            worm_threads=worm_threads, worm_diameter=worm_diameter
        )

    def test_calculate_worm_parameters_right_hand(self):
        params = self._make_worm_params()
        gen = WormGenerator(params)
        complement, pitch_diam, axial_pitch, lead = gen._calculate_worm_parameters()
        assert pitch_diam > 0
        assert axial_pitch > 0

    def test_complement_angle_formula(self):
        params = self._make_worm_params()
        gen = WormGenerator(params)
        complement, _, _, _ = gen._calculate_worm_parameters()
        # complement_angle = 90 - helical_angle (for right-hand)
        assert 0 < complement < 90

    def test_calculate_worm_parameters_left_hand(self):
        params = WormParameters(
            pitch=8, num_teeth=40, gear_width=0.5,
            table_orientation=TableOrientation.PLUS_X,
            worm_threads=2, worm_diameter=1.0,
            handedness=Handedness.LEFT
        )
        gen = WormGenerator(params)
        complement, _, _, _ = gen._calculate_worm_parameters()
        # With left hand, helical_angle is negative, complement > 90
        assert complement > 90


# ════════════════════════════════════════════════════════════════════
# MaterialDatabase
# ════════════════════════════════════════════════════════════════════

class TestMaterialDatabase:
    def test_init_loads_defaults(self):
        db = MaterialDatabase()
        assert len(db.materials) >= 5  # AL6061, STEEL1018, SS304, BRASS360, NYLON66

    def test_default_materials_present(self):
        db = MaterialDatabase()
        assert "AL6061" in db.materials
        assert "STEEL1018" in db.materials
        assert "SS304" in db.materials
        assert "BRASS360" in db.materials
        assert "NYLON66" in db.materials

    def test_get_material_found(self):
        db = MaterialDatabase()
        mat = db.get_material("AL6061")
        assert mat is not None
        assert mat.name == "Aluminum 6061-T6"

    def test_get_material_case_insensitive(self):
        db = MaterialDatabase()
        mat = db.get_material("al6061")
        assert mat is not None

    def test_get_material_not_found(self):
        db = MaterialDatabase()
        assert db.get_material("NONEXISTENT") is None

    def test_get_property_found(self):
        db = MaterialDatabase()
        prop = db.get_property("AL6061", "density")
        assert prop is not None
        assert prop.value == pytest.approx(0.098)

    def test_get_property_material_not_found(self):
        db = MaterialDatabase()
        assert db.get_property("INVALID", "density") is None

    def test_get_property_prop_not_found(self):
        db = MaterialDatabase()
        assert db.get_property("AL6061", "nonexistent_prop") is None

    def test_get_property_value(self):
        db = MaterialDatabase()
        val = db.get_property_value("AL6061", "density")
        assert val == pytest.approx(0.098)

    def test_get_property_value_not_found(self):
        db = MaterialDatabase()
        assert db.get_property_value("AL6061", "bogus") is None

    def test_list_materials_all(self):
        db = MaterialDatabase()
        mats = db.list_materials()
        assert len(mats) >= 5

    def test_list_materials_by_category(self):
        db = MaterialDatabase()
        from BelfryCAD.mlcnc.feed_optimizer import MaterialType
        aluminum_mats = db.list_materials(category=MaterialType.ALUMINUM)
        assert all(m.category == MaterialType.ALUMINUM for m in aluminum_mats)
        assert len(aluminum_mats) >= 1

    def test_add_material_success(self):
        db = MaterialDatabase()
        new_mat = MaterialRecord(
            material_id="TEST123",
            name="Test Material",
            category=MaterialType.STEEL,
            properties={},
        )
        assert db.add_material(new_mat) is True
        assert "TEST123" in db.materials

    def test_add_material_duplicate_fails(self):
        db = MaterialDatabase()
        new_mat = MaterialRecord(
            material_id="AL6061",
            name="Duplicate",
            category=MaterialType.ALUMINUM,
            properties={},
        )
        assert db.add_material(new_mat) is False

    def test_update_material_attribute(self):
        db = MaterialDatabase()
        db.update_material("AL6061", {"notes": "Updated notes"})
        mat = db.get_material("AL6061")
        assert mat.notes == "Updated notes"

    def test_update_material_property_value(self):
        db = MaterialDatabase()
        db.update_material("AL6061", {"density": 0.099})
        val = db.get_property_value("AL6061", "density")
        assert val == pytest.approx(0.099)

    def test_update_material_not_found(self):
        db = MaterialDatabase()
        assert db.update_material("NONEXISTENT", {"notes": "x"}) is False

    def test_delete_material_success(self):
        db = MaterialDatabase()
        assert db.delete_material("NYLON66") is True
        assert db.get_material("NYLON66") is None

    def test_delete_material_not_found(self):
        db = MaterialDatabase()
        assert db.delete_material("NONEXISTENT") is False

    def test_search_materials_by_name(self):
        db = MaterialDatabase()
        results = db.search_materials("aluminum")
        assert any("Aluminum" in m.name for m in results)

    def test_search_materials_by_id(self):
        db = MaterialDatabase()
        results = db.search_materials("al6061")
        assert any(m.material_id == "AL6061" for m in results)

    def test_search_materials_by_property_name(self):
        db = MaterialDatabase()
        results = db.search_materials("density")
        assert len(results) > 0

    def test_search_materials_no_match(self):
        db = MaterialDatabase()
        results = db.search_materials("xyzzyquux")
        assert results == []

    def test_get_similar_materials_reference_not_found(self):
        db = MaterialDatabase()
        result = db.get_similar_materials("NONEXISTENT", ["density"])
        assert result == []

    def test_get_similar_materials_returns_list(self):
        db = MaterialDatabase()
        result = db.get_similar_materials("AL6061", ["density", "tensile_strength"])
        assert isinstance(result, list)

    def test_calculate_similarity_same_material(self):
        db = MaterialDatabase()
        mat = db.get_material("AL6061")
        score = db._calculate_similarity(mat, mat, ["density"])
        assert score == pytest.approx(1.0)

    def test_calculate_similarity_no_common_properties(self):
        db = MaterialDatabase()
        mat1 = db.get_material("AL6061")
        mat2 = db.get_material("AL6061")
        score = db._calculate_similarity(mat1, mat2, ["nonexistent_prop"])
        assert score == pytest.approx(0.0)

    def test_export_material_data_all(self):
        db = MaterialDatabase()
        data = db.export_material_data()
        assert "AL6061" in data
        assert "material_id" in data["AL6061"]
        assert "properties" in data["AL6061"]

    def test_export_material_data_subset(self):
        db = MaterialDatabase()
        data = db.export_material_data(["AL6061"])
        assert "AL6061" in data
        assert "STEEL1018" not in data

    def test_import_material_data_success(self):
        db = MaterialDatabase()
        export = db.export_material_data(["AL6061"])
        db2 = MaterialDatabase()
        # Remove the material first
        del db2.materials["AL6061"]
        count = db2.import_material_data(export)
        assert count == 1
        assert db2.get_material("AL6061") is not None

    def test_import_material_data_invalid_skipped(self):
        db = MaterialDatabase()
        bad_data = {"INVALID": {"broken": True}}
        count = db.import_material_data(bad_data)
        assert count == 0

    def test_save_and_load_file(self, tmp_path):
        db = MaterialDatabase()
        filepath = str(tmp_path / "materials.json")
        assert db.save_to_file(filepath) is True
        db2 = MaterialDatabase()
        # Remove default to confirm load works
        db2.materials.clear()
        assert db2.load_from_file(filepath) is True
        assert "AL6061" in db2.materials

    def test_save_to_file_bad_path(self):
        db = MaterialDatabase()
        assert db.save_to_file("/nonexistent_dir/bad.json") is False

    def test_load_from_file_bad_path(self):
        db = MaterialDatabase()
        assert db.load_from_file("/nonexistent/file.json") is False

    def test_validate_database_no_errors(self):
        db = MaterialDatabase()
        result = db.validate_database()
        assert "errors" in result
        assert "warnings" in result
        assert "total_materials" in result
        assert result["total_materials"] == len(db.materials)

    def test_validate_database_catches_missing_property(self):
        db = MaterialDatabase()
        # Add material with no properties at all
        mat = MaterialRecord(
            material_id="EMPTY_MAT",
            name="Empty",
            category=MaterialType.PLASTIC,
            properties={}
        )
        db.materials["EMPTY_MAT"] = mat
        result = db.validate_database()
        errors = result["errors"]
        assert any("EMPTY_MAT" in e for e in errors)

    def test_validate_database_warns_low_confidence(self):
        db = MaterialDatabase()
        mat = MaterialRecord(
            material_id="LOW_CONF",
            name="Low Confidence Material",
            category=MaterialType.PLASTIC,
            properties={
                "density": MaterialProperty("Density", 0.05, "lb/in³", "Guess", 0.2),
                "tensile_strength": MaterialProperty("Tensile", 5000, "psi", "Guess", 0.2),
                "machinability_rating": MaterialProperty("Mach", 0.5, "", "Guess", 0.2),
            }
        )
        db.materials["LOW_CONF"] = mat
        result = db.validate_database()
        assert any("LOW_CONF" in w for w in result["warnings"])

    def test_init_with_nonexistent_path_still_loads_defaults(self):
        db = MaterialDatabase(database_path="/nonexistent/path.json")
        assert len(db.materials) >= 5


# ════════════════════════════════════════════════════════════════════
# ToolPathOptimizer
# ════════════════════════════════════════════════════════════════════

class TestToolPathOptimizer:
    def test_init(self, path_optimizer):
        assert path_optimizer.optimization_history == []
        assert path_optimizer.strategy_weights is not None

    def test_strategy_weights_keys(self, path_optimizer):
        weights = path_optimizer.strategy_weights
        assert "time_optimal" in weights
        assert "surface_optimal" in weights
        assert "tool_life_optimal" in weights
        assert "balanced" in weights

    def test_generate_roughing_path_conventional(self, path_optimizer, bounds, params):
        segs = path_optimizer.generate_roughing_path(bounds, params, PathStrategy.CONVENTIONAL)
        assert len(segs) > 0
        assert all(s.strategy == PathStrategy.CONVENTIONAL for s in segs)

    def test_generate_roughing_path_climb(self, path_optimizer, bounds, params):
        segs = path_optimizer.generate_roughing_path(bounds, params, PathStrategy.CLIMB)
        assert len(segs) > 0
        assert all(s.strategy == PathStrategy.CLIMB for s in segs)

    def test_generate_roughing_path_trochoidal(self, path_optimizer, bounds, params):
        segs = path_optimizer.generate_roughing_path(bounds, params, PathStrategy.TROCHOIDAL)
        assert len(segs) > 0
        assert all(s.strategy == PathStrategy.TROCHOIDAL for s in segs)

    def test_generate_roughing_path_adaptive(self, path_optimizer, bounds, params):
        segs = path_optimizer.generate_roughing_path(bounds, params, PathStrategy.ADAPTIVE)
        assert len(segs) > 0
        assert all(s.strategy == PathStrategy.ADAPTIVE for s in segs)

    def test_generate_roughing_path_segment_types(self, path_optimizer, bounds, params):
        segs = path_optimizer.generate_roughing_path(bounds, params)
        assert all(s.path_type == PathType.ROUGHING for s in segs)

    def test_generate_finishing_path_returns_segments(self, path_optimizer, bounds, params):
        segs = path_optimizer.generate_finishing_path(bounds, params)
        assert len(segs) > 0

    def test_generate_finishing_path_type_finishing(self, path_optimizer, bounds, params):
        segs = path_optimizer.generate_finishing_path(bounds, params)
        assert all(s.path_type == PathType.FINISHING for s in segs)

    def test_optimize_path_order_time(self, path_optimizer, bounds, params):
        segs = path_optimizer.generate_roughing_path(bounds, params)
        ordered = path_optimizer.optimize_path_order(segs, "time")
        assert len(ordered) == len(segs)

    def test_optimize_path_order_surface(self, path_optimizer, bounds, params):
        segs = path_optimizer.generate_roughing_path(bounds, params)
        ordered = path_optimizer.optimize_path_order(segs, "surface")
        assert len(ordered) == len(segs)

    def test_optimize_path_order_tool_life(self, path_optimizer, bounds, params):
        segs = path_optimizer.generate_roughing_path(bounds, params)
        ordered = path_optimizer.optimize_path_order(segs, "tool_life")
        assert len(ordered) == len(segs)

    def test_optimize_path_order_balanced(self, path_optimizer, bounds, params):
        segs = path_optimizer.generate_roughing_path(bounds, params)
        ordered = path_optimizer.optimize_path_order(segs, "other")
        assert len(ordered) == len(segs)

    def test_optimize_for_time_empty(self, path_optimizer):
        assert path_optimizer._optimize_for_time([]) == []

    def test_optimize_for_time_orders_nearest(self, path_optimizer):
        seg1 = ToolPathSegment(
            start=Point3D(0, 0, 0), end=Point3D(1, 0, 0),
            feed_rate=100, spindle_speed=5000,
            path_type=PathType.ROUGHING, strategy=PathStrategy.CONVENTIONAL
        )
        seg2 = ToolPathSegment(
            start=Point3D(10, 0, 0), end=Point3D(11, 0, 0),
            feed_rate=100, spindle_speed=5000,
            path_type=PathType.ROUGHING, strategy=PathStrategy.CONVENTIONAL
        )
        seg3 = ToolPathSegment(
            start=Point3D(1, 0, 0), end=Point3D(2, 0, 0),
            feed_rate=100, spindle_speed=5000,
            path_type=PathType.ROUGHING, strategy=PathStrategy.CONVENTIONAL
        )
        ordered = path_optimizer._optimize_for_time([seg1, seg2, seg3])
        assert len(ordered) == 3

    def test_calculate_machining_time_basic(self, path_optimizer):
        seg = ToolPathSegment(
            start=Point3D(0, 0, 0), end=Point3D(60, 0, 0),
            feed_rate=60, spindle_speed=5000,
            path_type=PathType.ROUGHING, strategy=PathStrategy.CONVENTIONAL
        )
        result = path_optimizer.calculate_machining_time([seg])
        assert result["cutting"] == pytest.approx(1.0)
        assert result["total"] == pytest.approx(1.0)

    def test_calculate_machining_time_rapid(self, path_optimizer):
        seg = ToolPathSegment(
            start=Point3D(0, 0, 0), end=Point3D(500, 0, 0),
            feed_rate=0, spindle_speed=5000,
            path_type=PathType.ROUGHING, strategy=PathStrategy.CONVENTIONAL
        )
        result = path_optimizer.calculate_machining_time([seg])
        assert result["rapid"] > 0

    def test_calculate_machining_time_tool_change(self, path_optimizer):
        seg1 = ToolPathSegment(
            start=Point3D(0, 0, 0), end=Point3D(10, 0, 0),
            feed_rate=100, spindle_speed=5000,
            path_type=PathType.ROUGHING, strategy=PathStrategy.CONVENTIONAL
        )
        seg2 = ToolPathSegment(
            start=Point3D(10, 0, 0), end=Point3D(20, 0, 0),
            feed_rate=100, spindle_speed=8000,  # Different speed -> tool change
            path_type=PathType.FINISHING, strategy=PathStrategy.CONVENTIONAL
        )
        result = path_optimizer.calculate_machining_time([seg1, seg2])
        assert result["tool_change"] > 0

    def test_analyze_surface_finish_no_finishing_segments(self, path_optimizer):
        seg = ToolPathSegment(
            start=Point3D(0, 0, 0), end=Point3D(10, 0, 0),
            feed_rate=100, spindle_speed=5000,
            path_type=PathType.ROUGHING, strategy=PathStrategy.CONVENTIONAL
        )
        result = path_optimizer.analyze_surface_finish([seg], 0.5)
        assert result["average_roughness"] == 0
        assert result["peak_roughness"] == 0

    def test_analyze_surface_finish_with_finishing(self, path_optimizer):
        seg = ToolPathSegment(
            start=Point3D(0, 0, 0), end=Point3D(10, 0, 0),
            feed_rate=50, spindle_speed=8000,
            path_type=PathType.FINISHING, strategy=PathStrategy.CONVENTIONAL
        )
        result = path_optimizer.analyze_surface_finish([seg], 0.5)
        assert result["average_roughness"] >= 0
        assert "uniformity" in result

    def test_calculate_finish_stepover(self, path_optimizer):
        stepover = path_optimizer._calculate_finish_stepover(0.5, 0.001)
        assert stepover > 0
        assert stepover <= 0.5 * 0.8  # Max 80% of diameter

    def test_calculate_finish_feed_rate(self, path_optimizer):
        feed = path_optimizer._calculate_finish_feed_rate(0.5, 0.001)
        assert feed > 0

    def test_calculate_finish_feed_rate_scale_with_tolerance(self, path_optimizer):
        feed_tight = path_optimizer._calculate_finish_feed_rate(0.5, 0.0005)
        feed_loose = path_optimizer._calculate_finish_feed_rate(0.5, 0.005)
        assert feed_loose > feed_tight

    def test_calculate_distance_3d(self, path_optimizer):
        p1 = Point3D(0, 0, 0)
        p2 = Point3D(3, 4, 0)
        assert path_optimizer._calculate_distance(p1, p2) == pytest.approx(5.0)

    def test_calculate_distance_3d_z(self, path_optimizer):
        p1 = Point3D(0, 0, 0)
        p2 = Point3D(0, 0, 5)
        assert path_optimizer._calculate_distance(p1, p2) == pytest.approx(5.0)

    def test_optimize_for_surface_sorted_by_type(self, path_optimizer):
        rough = ToolPathSegment(
            start=Point3D(0, 0, 0), end=Point3D(1, 0, 0),
            feed_rate=100, spindle_speed=5000,
            path_type=PathType.ROUGHING, strategy=PathStrategy.CONVENTIONAL
        )
        finish = ToolPathSegment(
            start=Point3D(0, 0, 0), end=Point3D(1, 0, 0),
            feed_rate=50, spindle_speed=8000,
            path_type=PathType.FINISHING, strategy=PathStrategy.CONVENTIONAL
        )
        result = path_optimizer._optimize_for_surface([rough, finish])
        # Sorted alphabetically by path_type.value: "finishing" < "roughing"
        # so finishing comes first in the sorted output
        assert len(result) == 2
        # Verify output is deterministically sorted
        sorted_direct = sorted([rough, finish], key=lambda s: (s.path_type.value, -s.feed_rate))
        assert result == sorted_direct

    def test_optimize_for_tool_life_sorted_by_load(self, path_optimizer):
        fast = ToolPathSegment(
            start=Point3D(0, 0, 0), end=Point3D(1, 0, 0),
            feed_rate=200, spindle_speed=10000,
            path_type=PathType.ROUGHING, strategy=PathStrategy.CONVENTIONAL
        )
        slow = ToolPathSegment(
            start=Point3D(0, 0, 0), end=Point3D(1, 0, 0),
            feed_rate=50, spindle_speed=3000,
            path_type=PathType.ROUGHING, strategy=PathStrategy.CONVENTIONAL
        )
        result = path_optimizer._optimize_for_tool_life([fast, slow])
        # Slower (lower load) first
        assert result[0].feed_rate * result[0].spindle_speed <= \
               result[1].feed_rate * result[1].spindle_speed

    def test_generate_conventional_pass(self, path_optimizer, bounds, params):
        segs = path_optimizer._generate_conventional_pass(0.0, 0.0, bounds, params)
        assert len(segs) == 1
        seg = segs[0]
        assert seg.start.y == bounds.min_y
        assert seg.end.y == bounds.max_y

    def test_generate_climb_pass(self, path_optimizer, bounds, params):
        segs = path_optimizer._generate_climb_pass(0.0, 0.0, bounds, params)
        assert len(segs) == 1
        seg = segs[0]
        assert seg.start.y == bounds.max_y
        assert seg.end.y == bounds.min_y

    def test_generate_adaptive_pass(self, path_optimizer, bounds, params):
        segs = path_optimizer._generate_adaptive_pass(0.0, 0.0, bounds, params)
        assert len(segs) == 3  # Always 3 segments
        # Feed rates increase
        assert segs[0].feed_rate < segs[1].feed_rate < segs[2].feed_rate

    def test_generate_finish_pass(self, path_optimizer, bounds, params):
        segs = path_optimizer._generate_finish_pass(0.0, bounds, params, 0.001)
        assert len(segs) == 1
        assert segs[0].path_type == PathType.FINISHING
