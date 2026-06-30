#!/usr/bin/env python3
"""Test suite for ports-in-use.sh script."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def ports_in_use_script_path():
    """Path to the ports-in-use.sh script."""
    return Path(__file__).parent.parent / "bash" / "ports-in-use.sh"


def check_bash_present():
    """Check if /bin/bash is present on the system."""
    return os.path.exists("/bin/bash")


def check_ss_present():
    """Check if ss command is present on the system."""
    result = subprocess.run(["which", "ss"], capture_output=True, text=True)
    return result.returncode == 0


def test_ports_in_use_script_exists(ports_in_use_script_path):
    """Test that ports-in-use.sh script exists."""
    assert ports_in_use_script_path.exists(), (
        f"ports-in-use script not found at {ports_in_use_script_path}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
@pytest.mark.skipif(
    not check_ss_present(), reason="ss command not found - skipping ports-in-use tests"
)
def test_ports_in_use_basic_execution(ports_in_use_script_path):
    """Test ports-in-use.sh basic execution."""
    result = subprocess.run(
        ["/bin/bash", str(ports_in_use_script_path)], capture_output=True, text=True
    )

    # Should succeed
    assert result.returncode == 0, f"Script execution failed: {result.stderr}"

    # Should produce output (ports or empty string)
    # The script just outputs ports, so we check it runs without error
    assert result.stdout is not None, "Should produce output"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
@pytest.mark.skipif(
    not check_ss_present(), reason="ss command not found - skipping ports-in-use tests"
)
def test_ports_in_use_output_format(ports_in_use_script_path):
    """Test ports-in-use.sh output format."""
    result = subprocess.run(
        ["/bin/bash", str(ports_in_use_script_path)], capture_output=True, text=True
    )

    # Should succeed
    assert result.returncode == 0, f"Script execution failed: {result.stderr}"

    # Output should be space-separated if there are ports
    # or empty if no ports are in use
    if result.stdout.strip():
        # If there are ports, they should be space-separated
        # The script may output various formats (numeric ports, addresses, etc.)
        # Just verify we get some output that's space-separated
        ports = result.stdout.strip().split()
        assert len(ports) > 0, (
            "Should have at least one port value if output is not empty"
        )
        # Verify output is space-separated (not newlines or other separators)
        assert "\n" not in result.stdout.strip(), (
            "Output should be space-separated, not newline-separated"
        )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
@pytest.mark.skipif(
    not check_ss_present(), reason="ss command not found - skipping ports-in-use tests"
)
def test_ports_in_use_no_arguments(ports_in_use_script_path):
    """Test ports-in-use.sh with no arguments (should work)."""
    result = subprocess.run(
        ["/bin/bash", str(ports_in_use_script_path)], capture_output=True, text=True
    )

    # Should succeed with no arguments
    assert result.returncode == 0, (
        f"Script should work without arguments: {result.stderr}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
@pytest.mark.skipif(
    not check_ss_present(), reason="ss command not found - skipping ports-in-use tests"
)
def test_ports_in_use_with_extra_arguments(ports_in_use_script_path):
    """Test ports-in-use.sh with extra arguments (should ignore them)."""
    result = subprocess.run(
        ["/bin/bash", str(ports_in_use_script_path), "extra", "args"],
        capture_output=True,
        text=True,
    )

    # Script doesn't parse arguments, so it should still work
    assert result.returncode == 0, (
        f"Script should ignore extra arguments: {result.stderr}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_ss_check(ports_in_use_script_path):
    """Test that ports-in-use.sh checks for ss command availability."""
    # Temporarily hide ss command by modifying PATH
    env = os.environ.copy()
    # Create a temporary directory with a fake ss that fails
    with tempfile.TemporaryDirectory() as tmpdir:
        env["PATH"] = tmpdir
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)],
            capture_output=True,
            text=True,
            env=env,
        )

        # Should fail with appropriate error message
        assert result.returncode != 0, "Should fail when ss is not available"
        assert (
            "ss command not found" in result.stderr or "ss" in result.stderr.lower()
        ), "Should mention ss command in error message"


def test_bash_presence_warning():
    """Test that we warn if bash is not present."""
    if not check_bash_present():
        pytest.warns(UserWarning, match="/bin/bash not found")
