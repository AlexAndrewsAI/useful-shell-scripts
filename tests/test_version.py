"""Tests for package version and single source of truth."""

import importlib.metadata


def test_version_attribute() -> None:
    """Test that the package has a __version__ attribute."""
    import useful_shell_scripts

    assert hasattr(useful_shell_scripts, "__version__")
    assert isinstance(useful_shell_scripts.__version__, str)
    assert len(useful_shell_scripts.__version__) > 0


def test_version_metadata() -> None:
    """Test that the version in metadata matches __version__."""
    import useful_shell_scripts

    metadata_version = importlib.metadata.version("useful-shell-scripts")
    assert metadata_version == useful_shell_scripts.__version__


def test_version_format() -> None:
    """Test that the version follows semantic versioning format."""
    import useful_shell_scripts

    version = useful_shell_scripts.__version__
    # Check for basic semantic versioning format (X.Y.Z)
    parts = version.split(".")
    assert len(parts) >= 2, "Version should have at least major.minor"
    assert all(part.isdigit() for part in parts), "Version parts should be numeric"
