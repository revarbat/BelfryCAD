"""
Test template for pyTkCAD

This file serves as a template for creating new tests in the tests directory.
"""

import sys
import os
import unittest

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

# Import modules to test
from BelfryCAD.tools.base import ToolCategory


class TestExample(unittest.TestCase):
    """Example test case for pyTkCAD."""

    def setUp(self):
        """Set up test fixtures."""
        pass
        
    def tearDown(self):
        """Tear down test fixtures."""
        pass
        
    def test_example(self):
        """Example test method."""
        # Example assertion
        self.assertTrue(True)
        
        
if __name__ == '__main__':
    unittest.main()