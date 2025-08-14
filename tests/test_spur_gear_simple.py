#!/usr/bin/env python3
"""
Simple test for spur gear functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from BelfryCAD.cad_geometry import Point2D
from BelfryCAD.cad_geometry.spur_gear import SpurGear


def test_spur_gear():
    """Test the SpurGear class functionality."""
    print("Testing SpurGear...")
    
    # Create a spur gear
    spur_gear = SpurGear(
        num_teeth=20,
        pitch_diameter=10.0,  # Increased from 2.0 to 10.0
        pressure_angle=20.0
    )
    
    # Test properties
    print(f"Number of teeth: {spur_gear.num_teeth}")
    print(f"Pitch diameter: {spur_gear.pitch_diameter}")
    print(f"Pressure angle: {spur_gear.pressure_angle}")
    print(f"Pitch radius: {spur_gear.pitch_radius}")
    print(f"Module: {spur_gear.module}")
    print(f"Circular pitch: {spur_gear.circular_pitch}")
    print(f"Diametral pitch: {spur_gear.diametral_pitch}")
    print(f"Addendum radius: {spur_gear.addendum_radius}")
    print(f"Base radius: {spur_gear.base_radius}")
    print(f"Root radius: {spur_gear.root_radius}")
    print(f"Safety radius: {spur_gear.safety_radius}")
    
    # Test gear path generation
    print("\nGenerating gear path...")
    gear_points = spur_gear.generate_gear_path()
    print(f"Gear path has {len(gear_points)} points")
    if gear_points:
        print(f"First point: {gear_points[0]}")
        print(f"Last point: {gear_points[-1]}")
    
    # Test pitch circle generation
    print("\nGenerating pitch circle...")
    pitch_points = spur_gear.get_pitch_circle_points()
    print(f"Pitch circle has {len(pitch_points)} points")
    if pitch_points:
        print(f"First point: {pitch_points[0]}")
        print(f"Last point: {pitch_points[-1]}")
    
    # Test tooth profile generation
    print("\nGenerating tooth profile...")
    tooth_points = spur_gear.generate_tooth_profile()
    print(f"Tooth profile has {len(tooth_points)} points")
    if tooth_points:
        print(f"First point: {tooth_points[0]}")
        print(f"Last point: {tooth_points[-1]}")
    
    print("\nSpurGear test completed successfully!")


if __name__ == "__main__":
    test_spur_gear() 