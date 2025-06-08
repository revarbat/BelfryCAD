#!/usr/bin/env python3
"""
Test to verify that the circular import issue is resolved and the complete
system integration works correctly.
"""

import sys
import os

# Add BelfryCAD to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_import_resolution():
    """Test that imports work without circular dependency issues"""
    print("Testing import resolution...")
    
    try:
        # This should work without circular import issues
        from BelfryCAD.gui.cad_scene import CadScene
        print("✅ CadScene import successful")
        
        from BelfryCAD.gui.drawing_manager import DrawingManager
        print("✅ DrawingManager import successful")
        
        # Test that we can create instances
        scene = CadScene()
        print("✅ CadScene instantiation successful")
        
        manager = DrawingManager()
        print("✅ DrawingManager instantiation successful")
        
        # Test the dependency injection pattern works
        manager.set_cad_scene(scene)
        print("✅ Dependency injection successful")
        
        # Test that CadScene's drawing manager is properly connected
        assert scene.drawing_manager is not None
        assert scene.drawing_manager.cad_scene is scene
        print("✅ CadScene-DrawingManager connection verified")
        
        # Test grid functionality
        print("\nTesting grid functionality...")
        
        # Test direct field access
        assert hasattr(scene, 'dpi')
        assert hasattr(scene, 'scale_factor')
        assert hasattr(scene, 'show_grid')
        assert hasattr(scene, 'grid_color')
        print("✅ Direct field access works")
        
        # Test compatibility layer
        context = scene.get_drawing_context()
        assert context.dpi == scene.dpi
        assert context.scale_factor == scene.scale_factor
        assert context.show_grid == scene.show_grid
        print("✅ Backward compatibility layer works")
        
        # Test grid methods
        scene.set_grid_visible(True)
        scene.set_origin_visible(True)
        print("✅ Grid control methods work")
        
        # Test tagging system
        print("\nTesting tagging system...")
        from BelfryCAD.gui.cad_scene import GridTags
        
        # This should not raise errors
        items = scene.getItemsByTags([GridTags.GRID])
        print(f"✅ Grid items found: {len(items)}")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Circular import issue resolved")
        print("✅ Grid functionality working")
        print("✅ Field migration complete")
        print("✅ Backward compatibility maintained")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_completeness():
    """Test that the complete integration works as expected"""
    print("\n" + "="*60)
    print("INTEGRATION COMPLETENESS TEST")
    print("="*60)
    
    try:
        from BelfryCAD.gui.cad_scene import CadScene
        
        # Create scene and verify all components
        scene = CadScene()
        
        # Verify DrawingManager integration
        assert scene.drawing_manager is not None
        assert scene.drawing_manager.cad_scene is scene
        print("✅ DrawingManager properly integrated")
        
        # Verify direct field access replaces DrawingContext
        expected_fields = ['dpi', 'scale_factor', 'show_grid', 'show_origin', 
                          'grid_color', 'origin_color_x', 'origin_color_y']
        
        for field in expected_fields:
            assert hasattr(scene, field), f"Missing field: {field}"
            print(f"✅ Field present: {field}")
        
        # Verify grid functionality is in CadScene
        grid_methods = ['redraw_grid', '_draw_grid_origin', '_draw_grid_lines',
                       '_get_grid_info']
        
        for method in grid_methods:
            assert hasattr(scene, method), f"Missing grid method: {method}"
            print(f"✅ Grid method present: {method}")
        
        # Verify tagging system
        tagging_methods = ['addTags', 'removeTags', 'getItemsByTags', 
                          'removeItemsByTags', 'moveItemsByTags']
        
        for method in tagging_methods:
            assert hasattr(scene, method), f"Missing tagging method: {method}"
            print(f"✅ Tagging method present: {method}")
        
        print("\n🎉 INTEGRATION COMPLETENESS VERIFIED!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("CIRCULAR IMPORT FIX VERIFICATION")
    print("="*50)
    
    success1 = test_import_resolution()
    success2 = test_integration_completeness()
    
    if success1 and success2:
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED - TASK COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("✅ Circular import issue RESOLVED")
        print("✅ Grid logic moved to CadScene")
        print("✅ DrawingContext fields moved to CadScene")
        print("✅ Backward compatibility maintained")
        print("✅ Complete system integration verified")
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ SOME TESTS FAILED")
        print("="*60)
        sys.exit(1)
