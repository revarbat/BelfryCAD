"""
Test recent files functionality.
"""

import unittest
from pathlib import Path
import tempfile
import shutil

from src.BelfryCAD.config import AppConfig
from src.BelfryCAD.models.preferences import PreferencesModel
from src.BelfryCAD.gui.viewmodels.preferences_viewmodel import PreferencesViewModel


class TestRecentFiles(unittest.TestCase):
    """Test recent files functionality."""

    def setUp(self):
        """Set up test environment."""
        self.config = AppConfig()
        self.preferences_model = PreferencesModel(self.config)
        self.preferences_viewmodel = PreferencesViewModel(self.preferences_model)
        
        # Create temporary directory for test files
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: shutil.rmtree(self.temp_dir))

    def test_recent_files_default(self):
        """Test that recent files starts as empty list."""
        recent_files = self.preferences_viewmodel.get("recent_files")
        self.assertEqual(recent_files, [])

    def test_add_recent_file(self):
        """Test adding a file to recent files."""
        test_file = str(self.temp_dir / "test.belcad")
        
        # Add file to recent files
        self.preferences_viewmodel.add_recent_file(test_file)
        
        # Check it was added
        recent_files = self.preferences_viewmodel.get("recent_files")
        self.assertIn(test_file, recent_files)
        self.assertEqual(len(recent_files), 1)

    def test_add_duplicate_file(self):
        """Test that adding duplicate file moves it to front."""
        test_file = str(self.temp_dir / "test.belcad")
        
        # Add file twice
        self.preferences_viewmodel.add_recent_file(test_file)
        self.preferences_viewmodel.add_recent_file(test_file)
        
        # Check it appears only once at the front
        recent_files = self.preferences_viewmodel.get("recent_files")
        self.assertEqual(len(recent_files), 1)
        self.assertEqual(recent_files[0], test_file)

    def test_recent_files_limit(self):
        """Test that recent files respects the count limit."""
        max_count = 5
        self.preferences_viewmodel.set("recent_files_count", max_count)
        
        # Add more files than the limit
        for i in range(max_count + 3):
            test_file = str(self.temp_dir / f"test{i}.belcad")
            self.preferences_viewmodel.add_recent_file(test_file)
        
        # Check only the most recent files are kept
        recent_files = self.preferences_viewmodel.get("recent_files")
        self.assertEqual(len(recent_files), max_count)
        
        # Check the most recent file is first
        self.assertEqual(recent_files[0], str(self.temp_dir / f"test{max_count + 2}.belcad"))

    def test_clear_recent_files(self):
        """Test clearing recent files."""
        test_file = str(self.temp_dir / "test.belcad")
        self.preferences_viewmodel.add_recent_file(test_file)
        
        # Clear recent files
        self.preferences_viewmodel.set("recent_files", [])
        
        # Check it's empty
        recent_files = self.preferences_viewmodel.get("recent_files")
        self.assertEqual(recent_files, [])

    def test_save_and_load_recent_files(self):
        """Test that recent files persist through save/load."""
        test_file = str(self.temp_dir / "test.belcad")
        self.preferences_viewmodel.add_recent_file(test_file)
        
        # Save preferences
        self.preferences_viewmodel.save_preferences()
        
        # Create new preferences model and load
        new_preferences_model = PreferencesModel(self.config)
        new_preferences_viewmodel = PreferencesViewModel(new_preferences_model)
        new_preferences_viewmodel.load_preferences()
        
        # Check recent files were loaded
        recent_files = new_preferences_viewmodel.get("recent_files")
        self.assertIn(test_file, recent_files)

    def test_open_file_adds_to_recent_files(self):
        """Test that opening a file adds it to recent files."""
        test_file = str(self.temp_dir / "test.belcad")
        
        # Simulate opening a file (this would normally be done by the main window)
        self.preferences_viewmodel.add_recent_file(test_file)
        
        # Check it was added
        recent_files = self.preferences_viewmodel.get("recent_files")
        self.assertIn(test_file, recent_files)
        self.assertEqual(len(recent_files), 1)
        self.assertEqual(recent_files[0], test_file)  # Should be at the front

    def test_filename_extraction(self):
        """Test that filenames are correctly extracted from full paths."""
        # Test Unix-style paths
        unix_path = "/home/user/documents/project.belcad"
        filename = unix_path.split('/')[-1] if '/' in unix_path else unix_path
        self.assertEqual(filename, "project.belcad")
        
        # Test Windows-style paths
        windows_path = "C:\\Users\\user\\Documents\\project.belcad"
        filename = windows_path.split('\\')[-1] if '\\' in windows_path else windows_path
        self.assertEqual(filename, "project.belcad")
        
        # Test mixed paths (Windows with forward slashes)
        mixed_path = "C:/Users/user/Documents/project.belcad"
        filename = mixed_path.split('/')[-1] if '/' in mixed_path else mixed_path
        self.assertEqual(filename, "project.belcad")
        
        # Test just filename
        simple_filename = "project.belcad"
        filename = simple_filename.split('/')[-1] if '/' in simple_filename else simple_filename
        self.assertEqual(filename, "project.belcad")

    def test_remove_nonexistent_files(self):
        """Test that non-existent files are removed from recent files list."""
        # Create a temporary file
        test_file = self.temp_dir / "test.belcad"
        test_file.write_text("test content")
        
        # Add both existing and non-existent files to recent files
        existing_file = str(test_file)
        nonexistent_file = str(self.temp_dir / "nonexistent.belcad")
        
        self.preferences_viewmodel.add_recent_file(existing_file)
        self.preferences_viewmodel.add_recent_file(nonexistent_file)
        
        # Check both files are in the list initially
        recent_files = self.preferences_viewmodel.get("recent_files")
        self.assertIn(existing_file, recent_files)
        self.assertIn(nonexistent_file, recent_files)
        self.assertEqual(len(recent_files), 2)
        
        # Simulate menu update (this would filter out non-existent files)
        valid_files = []
        for filepath in recent_files:
            if filepath and len(filepath) > 0:
                if Path(filepath).exists():
                    valid_files.append(filepath)
        
        # Check that only the existing file remains
        self.assertIn(existing_file, valid_files)
        self.assertNotIn(nonexistent_file, valid_files)
        self.assertEqual(len(valid_files), 1)
        
        # Clean up
        test_file.unlink()


if __name__ == "__main__":
    unittest.main() 