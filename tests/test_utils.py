"""Common test utilities for shell script testing."""

import os


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
