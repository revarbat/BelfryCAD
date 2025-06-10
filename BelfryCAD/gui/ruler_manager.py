class RulerManager:
    def __init__(self):
        # Initialize rulers
        self.horizontal_ruler = Ruler(orientation='horizontal')
        self.vertical_ruler = Ruler(orientation='vertical')

    def update_rulers_on_view_change(self):
        """Update rulers when view position or zoom changes."""
        # Update both rulers to reflect current view position
        self.horizontal_ruler.update()
        self.vertical_ruler.update()
        
        # Also update any grid alignment if needed
        if hasattr(self, 'update_grid_alignment'):
            self.update_grid_alignment()

    # ...existing methods...