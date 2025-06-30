Selection
---------
Start with a state of nothing selected.
Clicking on a CadItem will individually select that CadItem.
If the Shift key is held down, clicking on another CadItem will select it as well.
Clicking on an already selected CadItem while Shift is held down will do nothing.
If the Command key is held down, clicking on an unselected CadItem will select it.
If the Command key is held down, clicking on a selected CadItem will deselect it.


Control Points
--------------
When exactly one CadItem is selected, the ControlPoints for that CadItem are shown.
ControlPoints should show at the same view size, no matter what the scale of the View.
Clicking and dragging a ControlPoint will call the pos_setter callback with the CadItem coordinates of the mouse moves.
Clicking and dragging a ControlPoint will not affect the selection of the CadItem.
The pos_setter callback will have safeguards to prevent recursive calling.


Control Datums
--------------
When exactly one CadItem is selected, the ControlDatums for that CadItem are shown.
ControlDatums should show at the same view size, no matter what the scale of the View.
Clicking on a ControlDatum will pop up a datum editor window to edit the value.
Clicking on a ControlDatum will not affect the selection of the CadItem.
The data_setter callback will have safeguards to prevent recursive calling.


Datum Editor Window
-------------------
The datum editor window has:
1. An editor widget, populated with the data returned from the data_getter callback.
2. A cancel button, which dismisses the window, discarding any changes.
3. A Set button, which dismisses the window, and calls the data_setter callback with the edited value.

The editor widget should only accept digits, '-' and '.'.
The Set button will only be enabled when the editor widgets contains a valid floating point value.


Controls Life Cycle
-------------------
CadItems will each provide the following calls:
1. createControls() - to create all of the ControlPoints and ControlDatums necessary, remembering them in instance variables.  The positions and values are initialized at creation.  This is called just after a CadItem is instantiated. It returns a list of ControlsPoints/ControlDatums.
2. updateControls() - to calculate and update the position of each ControlPoint, and the position and value of each ControlDatum.  This should be called after any pos_setter or data_setter callback has been invoked.
3. hideControls() - Makes all ControlPoints/ControlDatums for this CadItem hidden via setVisible().This is called when a CadItem is deselected, or more than one CadItem becomes selected. ControlsPoints/ControlDatums are hidden by default.
4. showControls() - Makes all ControlPoints/ControlDatums for this CadItem visible via setVisible().  This is called when a CadItem becomes single selected.
