"""Common test utilities for shell script testing."""

import os
import shutil
from unittest import mock


def get_bash_path() -> str | None:
    """Get the path to bash on the system.

    Returns:
        Path to bash executable if found, None otherwise.
    """
    if os.path.exists("/bin/bash"):
        return "/bin/bash"
    elif os.path.exists("/usr/bin/bash"):
        return "/usr/bin/bash"
    else:
        return None


def check_bash_present() -> bool:
    """Check if bash is present on the system.

    Returns:
        True if bash is found, False otherwise.
    """
    return get_bash_path() is not None


def check_command_present(command: str) -> bool:
    """Check if a command is present on the system.

    Args:
        command: Command name to check for.

    Returns:
        True if command is found in PATH, False otherwise.
    """
    return shutil.which(command) is not None


def test_get_bash_path():
    """Test get_bash_path function with actual system state."""
    result = get_bash_path()
    if result:
        assert isinstance(result, str), "Should return string when bash is found"
        assert os.path.exists(result), "Returned path should exist"


def test_get_bash_path_none_case():
    """Test get_bash_path returns None when bash is not found."""
    # Force the None case by mocking
    with mock.patch("tests.test_utils.os.path.exists", return_value=False):
        result = get_bash_path()
        assert result is None, "Should return None when bash is not found"


def test_get_bash_path_usr_bin_fallback():
    """Test get_bash_path fallback to /usr/bin/bash."""

    # Mock /bin/bash not existing, /usr/bin/bash existing
    def mock_exists(path):
        return path == "/usr/bin/bash"

    with mock.patch("tests.test_utils.os.path.exists", side_effect=mock_exists):
        result = get_bash_path()
        assert result == "/usr/bin/bash", "Should fallback to /usr/bin/bash"


def test_get_bash_path_priority():
    """Test that get_bash_path prioritizes /bin/bash over /usr/bin/bash."""

    # Mock both paths existing to test priority
    def mock_exists_both(path):
        return path in ["/bin/bash", "/usr/bin/bash"]

    with mock.patch("tests.test_utils.os.path.exists", side_effect=mock_exists_both):
        result = get_bash_path()
        assert result == "/bin/bash", "Should prefer /bin/bash over /usr/bin/bash"


def test_check_bash_present():
    """Test check_bash_present function."""
    result = check_bash_present()
    assert isinstance(result, bool), "Should return boolean"
    if result:
        assert get_bash_path() is not None, "Should be consistent with get_bash_path"


def test_check_bash_present_mocked():
    """Test check_bash_present with mocked get_bash_path."""
    # Test when bash is present
    with mock.patch("tests.test_utils.get_bash_path", return_value="/bin/bash"):
        assert check_bash_present() is True, "Should return True when bash is found"

    # Test when bash is not present
    with mock.patch("tests.test_utils.get_bash_path", return_value=None):
        assert check_bash_present() is False, (
            "Should return False when bash is not found"
        )


def test_check_command_present():
    """Test check_command_present function."""
    # Test with a command that should exist (like 'ls')
    assert check_command_present("ls") is True, "Should find common command 'ls'"

    # Test with a command that likely doesn't exist
    assert check_command_present("nonexistent_command_12345") is False, (
        "Should return False for nonexistent command"
    )

    # Test with bash if present
    if check_bash_present():
        assert check_command_present("bash") is True, "Should find bash if present"


def test_check_command_present_edge_cases():
    """Test check_command_present with edge cases."""
    # Empty string
    assert check_command_present("") is False, "Should return False for empty string"

    # Command with spaces (should fail)
    assert check_command_present("command with spaces") is False, (
        "Should return False for command with spaces"
    )

    # Command with path separators (should work if absolute path exists)
    # We can't easily test this without knowing the system, but the function should handle it


def test_check_command_present_mocked():
    """Test check_command_present with mocked shutil.which."""
    # Test when command is found
    with mock.patch("tests.test_utils.shutil.which", return_value="/usr/bin/ls"):
        assert check_command_present("ls") is True, (
            "Should return True when command is found"
        )

    # Test when command is not found
    with mock.patch("tests.test_utils.shutil.which", return_value=None):
        assert check_command_present("nonexistent") is False, (
            "Should return False when command is not found"
        )
