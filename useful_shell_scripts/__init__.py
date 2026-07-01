"""Useful shell scripts - Python utilities for shell script testing and validation.

This package exists primarily for CI/CD compatibility reasons:

1. **Coverage.py compatibility**: The coverage.py tool requires at least one
   importable Python module to avoid "module-not-imported" warnings. Without this
   minimal package, coverage.py would complain about not being able to measure
   coverage for the project.

2. **Project structure consistency**: Having a proper Python package structure
   (even minimal) allows the project to be treated as a standard Python package by
   tooling, which is useful for dependency management with uv and other Python
   package managers.

3. **Future extensibility**: While currently minimal, this package provides a place
   to add Python utilities for shell script testing, validation, and development
   tools as the project evolves.

4. **Single source of version truth**: The `__version__` variable below is the
   single source of truth for the project version. The pyproject.toml is configured
   to read this version dynamically using hatch, ensuring version consistency
   across the project.

The repository's primary focus is shell scripts in the `bash/` directory, with
Python code primarily used for testing those scripts via pytest and pureshellcheck.
"""

__version__ = "0.1.0"
