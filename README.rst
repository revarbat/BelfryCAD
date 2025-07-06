BelfryCAD
=========

A 2.5D CAD/CAM application built with Python and PySide6, ported from the
original TkCAD TCL/Tk implementation.

.. image:: https://img.shields.io/badge/Python-3.8+-blue.svg
   :target: https://python.org
.. image:: https://img.shields.io/badge/PySide6-6.0+-green.svg
   :target: https://pyside.org
.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: LICENSE

Features
--------

* **2.5D CAD Design**: Create precise 2D drawings with support for lines, arcs,
   circles, bezier curves, and more
* **Layer Management**: Organize your designs with multiple layers, each with
   independent visibility and properties
* **Snap System**: Precise positioning with comprehensive snap options (grid,
   endpoints, midpoints, intersections, etc.)
* **Tool Palette**: Extensive set of drawing tools including geometric shapes,
   text, dimensions, and specialized tools
* **CAM Integration**: Generate G-code for CNC machining with cutting parameter
   optimization
* **Modern GUI**: Clean, responsive interface built with PySide6
* **Cross-platform**: Runs on Windows, macOS, and Linux

Installation
------------

Prerequisites
~~~~~~~~~~~~~

* Python 3.8 or higher
* PySide6 6.0 or higher

From Source
~~~~~~~~~~~

1. Clone the repository:
   .. code-block:: bash

      git clone https://github.com/revarbat/BelfryCAD.git
      cd BelfryCAD

2. Create a virtual environment:
   .. code-block:: bash

      python -m venv venv
      source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies:
   .. code-block:: bash

      pip install -r requirements.txt

4. Run the application:
   .. code-block:: bash

      python main.py


Development Setup
~~~~~~~~~~~~~~~~~

For development, you can use the provided development script:

.. code-block:: bash

   ./dev.sh setup    # Set up virtual environment and install dependencies
   ./dev.sh run      # Run the application
   ./dev.sh install  # Update dependencies

Usage
-----

Basic Drawing
~~~~~~~~~~~~~

1. **Start the Application**: Run `python main.py` from the project directory
2. **Select a Tool**: Use the tool palette on the left to select drawing tools
3. **Draw Objects**: Click to place points, drag to create shapes
4. **Use Snaps**: Enable snap options for precise positioning
5. **Manage Layers**: Use the layer panel to organize your drawing

Tool Categories
~~~~~~~~~~~~~~~

* **Basic Shapes**: Lines, circles, rectangles, polygons
* **Curves**: Arcs, bezier curves, ellipses, conic sections
* **Text & Dimensions**: Text objects, linear and angular dimensions
* **Specialized Tools**: Screw holes, gears, image import
* **Transforms**: Move, rotate, scale, mirror operations
* **Duplicators**: Copy, array, offset tools

Keyboard Shortcuts
~~~~~~~~~~~~~~~~~~

* **Escape**: Cancel current operation
* **Delete**: Remove selected objects
* **Ctrl+Z**: Undo
* **Ctrl+Y**: Redo
* **Ctrl+A**: Select all
* **Ctrl+C**: Copy selection
* **Ctrl+V**: Paste

Project Structure
-----------------

.. code-block:: text

   BelfryCAD/
   ├── src/BelfryCAD/           # Main application package
   │   ├── app.py              # Application entry point
   │   ├── config.py           # Configuration management
   │   ├── core/               # Core CAD functionality
   │   │   ├── cad_objects.py  # CAD object definitions
   │   │   ├── document.py     # Document management
   │   │   ├── layers.py       # Layer system
   │   │   └── undo_redo.py    # Undo/redo system
   │   ├── gui/                # User interface components
   │   │   ├── main_window.py  # Main application window
   │   │   ├── dialogs/        # Dialog windows
   │   │   ├── graphics_items/ # Drawing objects
   │   │   ├── panes/          # Side panels
   │   │   └── widgets/        # Custom widgets
   │   ├── tools/              # Drawing tools
   │   │   ├── base.py         # Tool base classes
   │   │   ├── line.py         # Line drawing tool
   │   │   ├── circle.py       # Circle drawing tool
   │   │   └── ...             # Other tools
   │   ├── mlcnc/              # CAM/G-code functionality
   │   │   ├── cutting_params.py
   │   │   ├── feed_optimizer.py
   │   │   └── tool_path.py
   │   ├── utils/              # Utility functions
   │   └── resources/          # Application resources
   │       └── icons/          # SVG icons
   ├── tests/                  # Unit tests
   ├── dev_docs/              # Development documentation
   ├── main.py                # Application launcher
   ├── requirements.txt       # Python dependencies
   └── pyproject.toml        # Project configuration

Development
-----------

Contributing
~~~~~~~~~~~~

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes following the coding standards
4. Add tests for new functionality
5. Submit a pull request

Coding Standards
~~~~~~~~~~~~~~~~

* Follow PEP 8 for Python code style
* Use type hints where appropriate
* Add docstrings to all functions and classes
* Write unit tests for new functionality
* Use relative imports within the package

Architecture Guidelines
~~~~~~~~~~~~~~~~~~~~~~~

* **GUI Separation**: Keep GUI and business logic separate using the MVVM
   design pattern.
* **Signals and Slots**: Use PySide6 signals for component communication
* **Tool Structure**: All tools inherit from the base `Tool` class
* **Resource Management**: Use `importlib.resources` for package resources
* **Layer System**: All objects belong to layers with independent properties

Testing
~~~~~~~

Run the test suite:

.. code-block:: bash

   python -m pytest tests/

Building
~~~~~~~~

To build a distributable package:

.. code-block:: bash

   python -m build

This will create source and wheel distributions in the `dist/` directory.

Dependencies
------------

Core Dependencies
~~~~~~~~~~~~~~~~~

* **PySide6**: Qt-based GUI framework
* **Pillow**: Image processing (for image import functionality)
* **NumPy**: Numerical computations
* **PyClipper**: Clipper library for boolean geometry operations

Development Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

* **pytest**: Testing framework
* **setuptools**: Package building
* **wheel**: Wheel distribution format

License
-------

This project is licensed under the MIT License - see the `LICENSE` file for
details.

Authors
-------

* **Revar Desmera** - *Initial work* - revarbat@gmail.com

Acknowledgments
---------------

* Original TkCAD TCL/Tk implementation
* PySide6 community for Qt bindings
* Contributors and testers

Support
-------

* **Issues**: Report bugs and feature requests on GitHub
* **Documentation**: See `dev_docs/` for development documentation
* **Wiki**: Additional documentation and tutorials

Roadmap
-------

* CadObjects are the Model, CadItems are the View.
* Implement ViewModels for CadObjects, linking with CadItems.
* Get Tools to generate new CadObjects, using CadItems for display.
* More CAM toolpath strategies
* Plugin system for custom tools
* Cloud storage integration
* Mobile companion app

.. _GitHub: https://github.com/revarbat/BelfryCAD
.. _Issues: https://github.com/revarbat/BelfryCAD/issues
.. _Releases: https://github.com/revarbat/BelfryCAD/releases

