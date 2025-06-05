#!/usr/bin/env python3
"""
Script to move markdown files from the root directory to the dev_docs directory.
Excludes README.md as that should remain in the root.
"""

import os
import shutil
import sys

def move_markdown_files():
    """Move markdown files from root to dev_docs directory"""
    # Files to move (all .md files except README.md)
    markdown_files = [
        'KEYBOARD_SHORTCUTS.md',
        'ARC_TOOL_CONSOLIDATION.md',
        'DIMENSION_TOOL_CONSOLIDATION.md',
        'TEST_ORGANIZATION.md'
    ]
    
    # Ensure dev_docs directory exists
    dev_docs_dir = 'dev_docs'
    if not os.path.exists(dev_docs_dir):
        os.makedirs(dev_docs_dir)
        print(f"Created {dev_docs_dir} directory")
    
    # Move each file
    moved_files = []
    for filename in markdown_files:
        if os.path.exists(filename):
            # Get source and destination paths
            src = filename
            dst = os.path.join(dev_docs_dir, filename)
            
            # Copy file to destination
            shutil.copy2(src, dst)
            print(f"Copied {src} to {dst}")
            
            # Remove original
            os.remove(src)
            print(f"Removed original {src}")
            
            moved_files.append(filename)
        else:
            print(f"File not found: {filename}")
    
    # Print summary
    print(f"\nMoved {len(moved_files)} markdown files to {dev_docs_dir}:")
    for filename in moved_files:
        print(f"  - {filename}")
    
    print("\nREADME.md was kept in the root directory")
    print("\nIn the future, all documentation should be written to the dev_docs directory.")
    
    return True

if __name__ == "__main__":
    success = move_markdown_files()
    sys.exit(0 if success else 1)
