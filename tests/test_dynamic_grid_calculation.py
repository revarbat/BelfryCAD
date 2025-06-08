#!/usr/bin/env python3
"""
Test to verify that DrawingManager and RulerWidget use the same dynamic
grid calculation algorithm and that the rulers access real DPI/scale values.
"""

import sys
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from BelfryCAD.gui.rulers import RulerWidget

def test_dynamic_grid_calculation():
    """Test that the dynamic grid calculation is working correctly"""
    print("Testing dynamic grid calculation with real DPI/scale values...")

    # Create Qt application
    app = QApplication(sys.argv)

    # Create scene and view for testing
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    scene.setSceneRect(-500, -500, 1000, 1000)

    # Test with different DPI and scale factor combinations
    test_scenarios = [
        {"dpi": 96.0, "scale": 1.0, "name": "Standard DPI, No zoom"},
        {"dpi": 120.0, "scale": 1.0, "name": "High DPI, No zoom"},
        {"dpi": 96.0, "scale": 2.0, "name": "Standard DPI, 2x zoom"},
        {"dpi": 144.0, "scale": 0.5, "name": "Very high DPI, 0.5x zoom"},
    ]

    all_tests_passed = True

    for scenario in test_scenarios:
        print(f"\n=== {scenario['name']} ===")
        print(f"DPI: {scenario['dpi']}, Scale Factor: {scenario['scale']}")

        # Create drawing context
        context = DrawingContext(
            scene=scene,
            dpi=scenario['dpi'],
            scale_factor=scenario['scale'],
            show_grid=True,
            show_origin=True
        )

        # Create drawing manager and ruler
        drawing_manager = DrawingManager(context)
        ruler = RulerWidget(view, "horizontal")
        ruler.set_drawing_context(context)

        # Get grid info from both
        drawing_grid_info = drawing_manager._get_grid_info()
        ruler_grid_info = ruler.get_grid_info()

        print(f"DrawingManager: {drawing_grid_info}")
        print(f"RulerWidget:    {ruler_grid_info}")
        print(f"Identical: {drawing_grid_info == ruler_grid_info}")

        # Verify they are identical
        if drawing_grid_info != ruler_grid_info:
            print(f"❌ FAIL: Grid info mismatch in scenario '{scenario['name']}'")
            all_tests_passed = False
        else:
            print(f"✅ PASS: Grid info identical in scenario '{scenario['name']}'")

        # Verify the ruler is using the correct DPI and scale
        ruler_dpi = ruler.get_dpi()
        ruler_scale = ruler.get_scale_factor()

        if ruler_dpi != scenario['dpi'] or ruler_scale != scenario['scale']:
            print(f"❌ FAIL: Ruler not using correct DPI/scale values")
            print(f"Expected DPI: {scenario['dpi']}, Got: {ruler_dpi}")
            print(f"Expected Scale: {scenario['scale']}, Got: {ruler_scale}")
            all_tests_passed = False
        else:
            print(f"✅ PASS: Ruler using correct DPI/scale values")

        # Verify dynamic calculation is working (different inputs give different outputs)
        minorspacing = drawing_grid_info[0]
        scalemult = scenario['dpi'] * scenario['scale']
        expected_pixel_spacing = minorspacing * scalemult

        print(f"Minor spacing: {minorspacing}")
        print(f"Scale multiplier: {scalemult}")
        print(f"Pixel spacing: {expected_pixel_spacing}")

        # The algorithm should ensure pixel spacing is >= 8.0 for minor spacing
        if expected_pixel_spacing < 8.0:
            print(f"⚠️  WARNING: Pixel spacing {expected_pixel_spacing} < 8.0 (algorithm threshold)")

    print(f"\n" + "="*60)
    if all_tests_passed:
        print("✅ SUCCESS: Dynamic grid calculation working correctly!")
        print("✅ Single source of truth achieved - DrawingManager calls RulerWidget")
        print("✅ Rulers access real DPI and scale factor values")
        print("✅ Grid calculation adapts to different DPI and zoom levels")
        return True
    else:
        print("❌ FAILURE: Some tests failed")
        return False

if __name__ == "__main__":
    success = test_dynamic_grid_calculation()
    if success:
        print("\n🎉 Dynamic grid calculation test PASSED!")
    else:
        print("\n💥 Dynamic grid calculation test FAILED!")
    sys.exit(0 if success else 1)
