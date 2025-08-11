"""
Test parameters pane tooltip functionality.
"""

import unittest
from PySide6.QtWidgets import QApplication, QTableWidgetItem
from PySide6.QtCore import Qt

from src.BelfryCAD.utils.cad_expression import CadExpression
from src.BelfryCAD.gui.panes.parameters_pane import ParametersPane


class TestParametersPaneTooltip(unittest.TestCase):
    """Test parameters pane tooltip functionality."""

    def setUp(self):
        """Set up test environment."""
        # Create QApplication instance for Qt widgets
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        
        self.cad_expression = CadExpression()
        self.parameters_pane = ParametersPane(self.cad_expression)

    def test_tooltip_shows_expression_and_value(self):
        """Test that tooltip shows both expression and evaluated value."""
        # Add a simple parameter
        self.cad_expression.set_variable("test_param", "2 + 3")
        
        # Refresh the pane to populate the table
        self.parameters_pane.refresh()
        
        # Get the expression item from the table
        expr_item = self.parameters_pane.table.item(0, 1)
        self.assertIsNotNone(expr_item)
        
        # Check the tooltip contains both expression and value
        tooltip = expr_item.toolTip()
        self.assertIn("2 + 3", tooltip)
        self.assertIn("= 5", tooltip)

    def test_no_tooltip_for_simple_numbers(self):
        """Test that no tooltip is set for expressions that are just numbers."""
        # Add parameters that are just numbers
        self.cad_expression.set_variable("simple_number", "5")
        self.cad_expression.set_variable("decimal_number", "3.14")
        self.cad_expression.set_variable("negative_number", "-2.5")
        
        # Refresh the pane to populate the table
        self.parameters_pane.refresh()
        
        # Check that no tooltip is set for simple numbers
        for row in range(3):
            expr_item = self.parameters_pane.table.item(row, 1)
            self.assertIsNotNone(expr_item)
            
            # Simple numbers should not have tooltips
            tooltip = expr_item.toolTip()
            self.assertEqual(tooltip, "")

    def test_tooltip_shows_expression_and_error(self):
        """Test that tooltip shows expression and error when evaluation fails."""
        # Add a parameter with an invalid expression
        self.cad_expression.set_variable("invalid_param", "2 + undefined_var")
        
        # Refresh the pane to populate the table
        self.parameters_pane.refresh()
        
        # Get the expression item from the table
        expr_item = self.parameters_pane.table.item(0, 1)
        self.assertIsNotNone(expr_item)
        
        # Check the tooltip contains both expression and error
        tooltip = expr_item.toolTip()
        self.assertIn("2 + undefined_var", tooltip)
        self.assertIn("Error:", tooltip)

    def test_tooltip_with_complex_expression(self):
        """Test that tooltip works with complex expressions."""
        # Add a parameter with a complex expression
        self.cad_expression.set_variable("complex_param", "sqrt(16) * 2 + 1")
        
        # Refresh the pane to populate the table
        self.parameters_pane.refresh()
        
        # Get the expression item from the table
        expr_item = self.parameters_pane.table.item(0, 1)
        self.assertIsNotNone(expr_item)
        
        # Check the tooltip contains both expression and value
        tooltip = expr_item.toolTip()
        self.assertIn("sqrt(16) * 2 + 1", tooltip)
        self.assertIn("= 9", tooltip)

    def test_tooltip_with_variable_reference(self):
        """Test that tooltip works with expressions that reference other variables."""
        # Add parameters that reference each other
        self.cad_expression.set_variable("base", "10")
        self.cad_expression.set_variable("derived", "$base * 2")
        
        # Refresh the pane to populate the table
        self.parameters_pane.refresh()
        
        # Get the derived parameter expression item
        expr_item = self.parameters_pane.table.item(1, 1)  # derived should be second
        self.assertIsNotNone(expr_item)
        
        # Check the tooltip contains both expression and value
        tooltip = expr_item.toolTip()
        self.assertIn("$base * 2", tooltip)
        self.assertIn("= 20", tooltip)

    def test_multiple_parameters_tooltips(self):
        """Test that multiple parameters all have correct tooltips."""
        # Add multiple parameters (mix of simple numbers and expressions)
        self.cad_expression.set_variable("param1", "5")
        self.cad_expression.set_variable("param2", "10")
        self.cad_expression.set_variable("param3", "$param1 + $param2")
        
        # Refresh the pane to populate the table
        self.parameters_pane.refresh()
        
        # Check all parameters have correct tooltips
        for row in range(3):
            expr_item = self.parameters_pane.table.item(row, 1)
            self.assertIsNotNone(expr_item)
            
            tooltip = expr_item.toolTip()
            
            # Check specific values
            if row == 0:  # param1 (simple number, no tooltip)
                self.assertEqual(tooltip, "")
            elif row == 1:  # param2 (simple number, no tooltip)
                self.assertEqual(tooltip, "")
            elif row == 2:  # param3 (expression, has tooltip)
                self.assertIn("$param1 + $param2", tooltip)
                self.assertIn("= 15", tooltip)


if __name__ == "__main__":
    unittest.main() 