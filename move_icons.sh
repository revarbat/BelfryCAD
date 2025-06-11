#!/bin/bash
# Script to move all SVG icons from images dir to BelfryCAD/resources/icons dir

# Create the target directory if it doesn't exist
mkdir -p "/Users/gminette/dev/git-repos/BelfryCAD/BelfryCAD/resources/icons"

# Find and move all SVG files from images directory
find "/Users/gminette/dev/git-repos/BelfryCAD/images" -name "*.svg" -type f -exec mv {} "/Users/gminette/dev/git-repos/BelfryCAD/BelfryCAD/resources/icons/" \;

# Also check for SVG files in any subdirectories of images
find "/Users/gminette/dev/git-repos/BelfryCAD/images" -name "*.svg" -type f -exec mv {} "/Users/gminette/dev/git-repos/BelfryCAD/BelfryCAD/resources/icons/" \;

echo "SVG icons moved to BelfryCAD/resources/icons directory"