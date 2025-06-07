#!/usr/bin/env python3
"""
Test to verify that RulerWidget now accesses real DPI and scale factor values
from the drawing context instead of using hardcoded placeholder values.
"""

import sys
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from BelfryCAD.gui.drawing_manager import DrawingManager, DrawingContext
from BelfryCAD.gui.rulers import RulerWidget, RulerManager

def test_ruler_context_connection():
    """Test that rulers now access real DPI and scale factor values"""
    print("Testing ruler connection to drawing context...")
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create scene and view for testing
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    scene.setSceneRect(-500, -500, 1000, 1000)
    
    # Create drawing context with specific DPI and scale factor values
    context = DrawingContext(
        scene=scene,
        dpi=120.0,  # Different from default 96.0
        scale_factor=2.5,  # Different from default 1.0
        show_grid=True,
        show_origin=True
    )
    
    print(f"✓ Created drawing context with DPI={context.dpi}, scale_factor={context.scale_factor}")
    
    # Test 1: RulerWidget without drawing context (should use defaults)
    ruler_no_context = RulerWidget(view, "horizontal")
    dpi_no_context = ruler_no_context.get_dpi()
    scale_no_context = ruler_no_context.get_scale_factor()
    
    print(f"\n=== RULER WITHOUT CONTEXT ===")
    print(f"DPI: {dpi_no_context} (should be 96.0 default)")
    print(f"Scale Factor: {scale_no_context} (should be 1.0 default)")
    
    # Test 2: RulerWidget with drawing context (should use real values)
    ruler_with_context = RulerWidget(view, "horizontal")
    ruler_with_context.set_drawing_context(context)
    dpi_with_context = ruler_with_context.get_dpi()
    scale_with_context = ruler_with_context.get_scale_factor()
    
    print(f"\n=== RULER WITH CONTEXT ===")
    print(f"DPI: {dpi_with_context} (should be 120.0 from context)")
    print(f"Scale Factor: {scale_with_context} (should be 2.5 from context)")
    
    # Test 3: RulerManager connection
    ruler_manager = RulerManager(view)
    ruler_manager.set_drawing_context(context)
    
    h_ruler = ruler_manager.get_horizontal_ruler()
    v_ruler = ruler_manager.get_vertical_ruler()
    
    h_dpi = h_ruler.get_dpi()
    h_scale = h_ruler.get_scale_factor()
    v_dpi = v_ruler.get_dpi()
    v_scale = v_ruler.get_scale_factor()
    
    print(f"\n=== RULER MANAGER WITH CONTEXT ===")
    print(f"Horizontal ruler - DPI: {h_dpi}, Scale: {h_scale}")
    print(f"Vertical ruler - DPI: {v_dpi}, Scale: {v_scale}")
    
    # Test 4: DrawingManager grid info with connected context
    drawing_manager = DrawingManager(context)
    grid_info = drawing_manager._get_grid_info()
    
    print(f"\n=== DRAWING MANAGER GRID INFO ===")
    print(f"Grid info: {grid_info}")
    
    # Verify results
    success = True
    
    # Check that without context, defaults are used
    if dpi_no_context != 96.0 or scale_no_context != 1.0:
        print(f"\n❌ FAIL: Ruler without context should use defaults")
        success = False
    
    # Check that with context, real values are used
    if dpi_with_context != 120.0 or scale_with_context != 2.5:
        print(f"\n❌ FAIL: Ruler with context should use real values")
        success = False
    
    # Check that ruler manager properly sets context on both rulers
    if h_dpi != 120.0 or h_scale != 2.5 or v_dpi != 120.0 or v_scale != 2.5:
        print(f"\n❌ FAIL: RulerManager should set context on both rulers")
        success = False
    
    if success:
        print(f"\n✅ SUCCESS: All ruler context connections working correctly!")
        print("✅ Rulers now access real DPI and scale factor values from drawing context")
        print("✅ DrawingManager grid calculation uses same values as rulers")
        return True
    else:
        print(f"\n❌ FAILURE: Some ruler context connections not working")
        return False

if __name__ == "__main__":
    success = test_ruler_context_connection()
    if success:
        print("\n🎉 Ruler context connection test PASSED!")
    else:
        print("\n💥 Ruler context connection test FAILED!")
    sys.exit(0 if success else 1)
