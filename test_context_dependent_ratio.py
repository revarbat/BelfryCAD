#!/usr/bin/env python3
"""
Investigation of context-dependent grid-to-ruler ratio issues.
This test explores scenarios that might cause the 4:3 ratio observed by the user
despite perfect alignment in isolated tests.
"""

import sys
import math
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView
from PySide6.QtCore import QRectF
from PySide6.QtGui import QTransform

from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from BelfryCAD.gui.rulers import RulerWidget

def test_different_scene_transforms():
    """Test grid-ruler ratios with different view transformations"""
    print("Testing different scene transformations...")

    # Test scenarios that might affect ratio calculations
    test_scenarios = [
        {
            "name": "Standard view (1.0x)",
            "scale": 1.0,
            "rotation": 0,
            "scene_rect": (-200, -200, 400, 400),
            "view_matrix": QTransform()
        },
        {
            "name": "Zoomed in view (2.0x)",
            "scale": 2.0,
            "rotation": 0,
            "scene_rect": (-200, -200, 400, 400),
            "view_matrix": QTransform().scale(2.0, 2.0)
        },
        {
            "name": "Zoomed out view (0.5x)",
            "scale": 0.5,
            "rotation": 0,
            "scene_rect": (-400, -400, 800, 800),
            "view_matrix": QTransform().scale(0.5, 0.5)
        },
        {
            "name": "Different aspect ratio",
            "scale": 1.0,
            "rotation": 0,
            "scene_rect": (-300, -150, 600, 300),  # 2:1 aspect ratio
            "view_matrix": QTransform()
        },
        {
            "name": "Fractional zoom (1.33x)",
            "scale": 4.0/3.0,  # This is the 4:3 ratio!
            "rotation": 0,
            "scene_rect": (-200, -200, 400, 400),
            "view_matrix": QTransform().scale(4.0/3.0, 4.0/3.0)
        },
        {
            "name": "Fractional zoom (0.75x)",
            "scale": 0.75,  # 3:4 ratio
            "rotation": 0,
            "scene_rect": (-200, -200, 400, 400),
            "view_matrix": QTransform().scale(0.75, 0.75)
        }
    ]

    for scenario in test_scenarios:
        print(f"\n" + "="*50)
        print(f"Testing: {scenario['name']}")
        print(f"Scale factor: {scenario['scale']}")

        # Create scene and view
        scene = QGraphicsScene()
        view = QGraphicsView(scene)
        scene.setSceneRect(*scenario['scene_rect'])

        # Apply view transformation
        view.setTransform(scenario['view_matrix'])

        # Create drawing context with scenario's scale
        context = DrawingContext(
            scene=scene,
            dpi=96.0,
            scale_factor=scenario['scale'],
            show_grid=True,
            show_origin=True
        )

        # Create drawing manager and ruler
        drawing_manager = DrawingManager(context)
        ruler = RulerWidget(view, "horizontal")

        # Get grid info
        grid_info = ruler.get_grid_info()
        (minorspacing, majorspacing, superspacing, labelspacing,
         divisor, units, formatfunc, conversion) = grid_info

        print(f"Grid spacing: minor={minorspacing}, major={majorspacing}, label={labelspacing}")
        print(f"Conversion factor: {conversion}")

        # Calculate scale multiplier
        scalemult = 96.0 * scenario['scale'] / conversion
        print(f"Scale multiplier: {scalemult}")

        # Draw grid
        scene.clear()
        drawing_manager.redraw_grid()

        # Analyze grid items
        grid_items = scene.items()
        minor_lines = []
        major_lines = []

        for item in grid_items:
            if hasattr(item, 'zValue') and hasattr(item, 'line'):
                line = item.line()
                z = item.zValue()

                # Check vertical lines
                if abs(line.x1() - line.x2()) < 0.001:
                    x_pos = line.x1()
                    if z == -8:  # Minor lines
                        minor_lines.append(x_pos)
                    elif z == -7:  # Major lines
                        major_lines.append(x_pos)

        minor_lines = sorted(list(set(minor_lines)))
        major_lines = sorted(list(set(major_lines)))

        # Calculate expected ruler positions
        scene_rect = scene.sceneRect()
        x_start = scene_rect.left() / scalemult
        x_end = scene_rect.right() / scalemult

        ruler_ticks = []
        x = math.floor(x_start / minorspacing + 1e-6) * minorspacing
        while x <= x_end:
            if abs(math.floor(x / labelspacing + 1e-6) - x / labelspacing) < 1e-3:
                x_scene = x * scalemult
                ruler_ticks.append(x_scene)
            x += minorspacing

        ruler_ticks = sorted(list(set(ruler_ticks)))

        print(f"Grid lines: {len(minor_lines)} minor, {len(major_lines)} major")
        print(f"Expected ruler ticks: {len(ruler_ticks)}")

        # Calculate ratios
        if len(ruler_ticks) > 0:
            minor_ratio = len(minor_lines) / len(ruler_ticks)
            major_ratio = len(major_lines) / len(ruler_ticks)

            print(f"Ratios:")
            print(f"  Minor/Ruler = {minor_ratio:.3f}")
            print(f"  Major/Ruler = {major_ratio:.3f}")

            # Check for 4:3 ratio (≈1.333)
            target_ratio = 4.0/3.0
            if abs(minor_ratio - target_ratio) < 0.1:
                print(f"  ⚠️  FOUND 4:3 RATIO! ({target_ratio:.3f})")
                print(f"  This might be the issue source!")

                # Detailed analysis
                print(f"  Scale factor causing issue: {scenario['scale']}")
                print(f"  Scene bounds: {scenario['scene_rect']}")

                # Check spacing patterns
                if len(minor_lines) >= 8 and len(ruler_ticks) >= 6:
                    print(f"  Sample positions:")
                    print(f"    Minor lines: {[round(x, 1) for x in minor_lines[:8]]}")
                    print(f"    Ruler ticks: {[round(x, 1) for x in ruler_ticks[:6]]}")
            elif abs(major_ratio - target_ratio) < 0.1:
                print(f"  ⚠️  MAJOR LINES show 4:3 ratio!")
            else:
                print(f"  ✓ No 4:3 ratio detected")

        # Check alignment accuracy
        aligned_count = 0
        for ruler_pos in ruler_ticks:
            closest_major = min(major_lines, key=lambda x: abs(x - ruler_pos)) if major_lines else None
            if closest_major and abs(closest_major - ruler_pos) < 0.001:
                aligned_count += 1

        alignment_pct = (aligned_count / len(ruler_ticks) * 100) if ruler_ticks else 0
        print(f"Alignment accuracy: {alignment_pct:.1f}% ({aligned_count}/{len(ruler_ticks)})")

def test_viewport_dependent_ratios():
    """Test if viewport size affects the observed ratios"""
    print("\n" + "="*60)
    print("Testing viewport-dependent ratio effects...")

    # Different viewport sizes that might affect user perception
    viewport_tests = [
        {"name": "Small viewport", "size": (400, 300)},
        {"name": "Medium viewport", "size": (800, 600)},
        {"name": "Large viewport", "size": (1200, 900)},
        {"name": "Wide viewport", "size": (1600, 400)},
        {"name": "Tall viewport", "size": (400, 1200)}
    ]

    for vp_test in viewport_tests:
        print(f"\nTesting {vp_test['name']}: {vp_test['size']}")

        scene = QGraphicsScene()
        view = QGraphicsView(scene)
        view.resize(*vp_test['size'])

        # Set scene to match viewport proportions
        width, height = vp_test['size']
        aspect = width / height
        scene_width = 400
        scene_height = scene_width / aspect
        scene.setSceneRect(-scene_width/2, -scene_height/2, scene_width, scene_height)

        print(f"Scene rect: {scene.sceneRect().width():.1f} x {scene.sceneRect().height():.1f}")

        context = DrawingContext(
            scene=scene,
            dpi=96.0,
            scale_factor=1.0,
            show_grid=True,
            show_origin=True
        )

        drawing_manager = DrawingManager(context)
        ruler = RulerWidget(view, "horizontal")

        # Quick ratio check
        grid_info = ruler.get_grid_info()
        scalemult = 96.0 / grid_info[7]  # conversion

        scene.clear()
        drawing_manager.redraw_grid()

        # Count visible grid elements
        visible_minor = 0
        visible_major = 0

        for item in scene.items():
            if hasattr(item, 'zValue') and hasattr(item, 'line'):
                z = item.zValue()
                if z == -8:
                    visible_minor += 1
                elif z == -7:
                    visible_major += 1

        # Estimate ruler ticks
        scene_rect = scene.sceneRect()
        x_span = scene_rect.width() / scalemult
        estimated_ticks = max(1, int(x_span / grid_info[3]))  # labelspacing

        if estimated_ticks > 0:
            ratio = visible_minor / estimated_ticks
            print(f"  Estimated minor/ruler ratio: {ratio:.2f}")

            if abs(ratio - 4.0/3.0) < 0.2:
                print(f"  ⚠️  Viewport size may contribute to 4:3 perception!")

def test_ruler_widget_variations():
    """Test if different ruler widget configurations affect ratios"""
    print("\n" + "="*60)
    print("Testing ruler widget configuration variations...")

    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    scene.setSceneRect(-200, -200, 400, 400)

    # Test both horizontal and vertical rulers
    ruler_orientations = ["horizontal", "vertical"]

    for orientation in ruler_orientations:
        print(f"\nTesting {orientation} ruler:")

        ruler = RulerWidget(view, orientation)
        grid_info = ruler.get_grid_info()

        print(f"  Grid info: {grid_info}")
        print(f"  Minor spacing: {grid_info[0]}")
        print(f"  Label spacing: {grid_info[3]}")
        print(f"  Conversion: {grid_info[7]}")

        # Check if orientation affects the grid calculation
        ratio = grid_info[0] / grid_info[3]  # minor/label spacing
        print(f"  Built-in minor/label ratio: {ratio:.3f}")

        if abs(ratio - 4.0/3.0) < 0.1:
            print(f"  ⚠️  Built-in ratio close to 4:3!")

if __name__ == "__main__":
    # Create single QApplication instance to avoid singleton issues
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    try:
        test_different_scene_transforms()
        test_viewport_dependent_ratios()
        test_ruler_widget_variations()

        print(f"\n" + "="*60)
        print("CONTEXT-DEPENDENT ANALYSIS COMPLETE")
        print("="*60)
        print("FINDINGS:")
        print("- Tested different scene transformations and scale factors")
        print("- Examined viewport size effects on grid perception")
        print("- Analyzed ruler widget configuration variations")
        print("- Looked for conditions that might produce 4:3 ratio")
        print("")
        print("If no 4:3 ratio was found, the issue may be:")
        print("1. Application-specific (main window context)")
        print("2. User interface state dependent")
        print("3. Hardware/platform specific")
        print("4. Related to actual ruler widget implementation in main app")
        print("="*60)

    except Exception as e:
        print(f"Error in context analysis: {e}")
        import traceback
        traceback.print_exc()
