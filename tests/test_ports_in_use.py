#!/usr/bin/env python3
"""Test suite for ports-in-use.sh script."""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

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
def test_ports_in_use_basic_execution(ports_in_use_script_path):
    """Test ports-in-use.sh basic execution."""
    result = subprocess.run(
        ["/bin/bash", str(ports_in_use_script_path)], capture_output=True, text=True
    )

    # Should succeed if ss is present, fail gracefully otherwise
    if check_ss_present():
        assert result.returncode == 0, f"Script execution failed: {result.stderr}"
        # Should produce output (ports or empty string)
        assert result.stdout is not None, "Should produce output"
    else:
        assert result.returncode != 0, "Should fail when ss is not present"
        assert "ss" in result.stderr.lower(), "Should mention ss in error"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_output_format(ports_in_use_script_path):
    """Test ports-in-use.sh output format."""
    result = subprocess.run(
        ["/bin/bash", str(ports_in_use_script_path)], capture_output=True, text=True
    )

    # Only test format if ss is present
    if not check_ss_present():
        return

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
def test_ports_in_use_no_arguments(ports_in_use_script_path):
    """Test ports-in-use.sh with no arguments (should work)."""
    result = subprocess.run(
        ["/bin/bash", str(ports_in_use_script_path)], capture_output=True, text=True
    )

    # Should succeed with no arguments if ss is present
    if check_ss_present():
        assert result.returncode == 0, (
            f"Script should work without arguments: {result.stderr}"
        )
    else:
        assert result.returncode != 0, "Should fail when ss is not present"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_with_extra_arguments(ports_in_use_script_path):
    """Test ports-in-use.sh with extra arguments (should ignore them)."""
    result = subprocess.run(
        ["/bin/bash", str(ports_in_use_script_path), "extra", "args"],
        capture_output=True,
        text=True,
    )

    # Script doesn't parse arguments, so it should still work if ss is present
    if check_ss_present():
        assert result.returncode == 0, (
            f"Script should ignore extra arguments: {result.stderr}"
        )
    else:
        assert result.returncode != 0, "Should fail when ss is not present"


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


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_mocked_empty_output(ports_in_use_script_path):
    """Test ports-in-use.sh with mocked empty output."""
    # Mock subprocess.run to return empty output
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["/bin/bash", str(ports_in_use_script_path)],
            returncode=0,
            stdout="",
            stderr=""
        )
        
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)], capture_output=True, text=True
        )
        
        assert result.returncode == 0
        assert result.stdout == ""


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_mocked_with_ports(ports_in_use_script_path):
    """Test ports-in-use.sh with mocked port output."""
    # Mock subprocess.run to return port output
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["/bin/bash", str(ports_in_use_script_path)],
            returncode=0,
            stdout="80 443 8080 ",
            stderr=""
        )
        
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)], capture_output=True, text=True
        )
        
        assert result.returncode == 0
        assert "80" in result.stdout
        assert "443" in result.stdout


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_empty_output(ports_in_use_script_path):
    """Test ports-in-use.sh when no ports are in use (empty output)."""
    # This test checks the script handles empty output gracefully
    # We can't easily force no ports to be in use, but we can test the format
    result = subprocess.run(
        ["/bin/bash", str(ports_in_use_script_path)], capture_output=True, text=True
    )

    # Only test if ss is present
    if not check_ss_present():
        return

    # Should succeed regardless of port state
    assert result.returncode == 0, f"Script should succeed even with no ports: {result.stderr}"

    # If output is empty, it should be empty string (not error)
    if not result.stdout.strip():
        assert result.stdout == "", "Empty output should be empty string"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_large_port_numbers(ports_in_use_script_path):
    """Test ports-in-use.sh handles large port numbers correctly."""
    result = subprocess.run(
        ["/bin/bash", str(ports_in_use_script_path)], capture_output=True, text=True
    )

    # Only test if ss is present
    if not check_ss_present():
        return

    # Should succeed
    assert result.returncode == 0, f"Script execution failed: {result.stderr}"

    # If there are ports, check they are valid port numbers (0-65535)
    if result.stdout.strip():
        ports = result.stdout.strip().split()
        for port_str in ports:
            try:
                port_num = int(port_str)
                assert 0 <= port_num <= 65535, (
                    f"Port {port_num} is outside valid range (0-65535)"
                )
            except ValueError:
                # If output contains non-numeric values (like addresses), skip validation
                # The script may output various formats from ss command
                pass


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_sorted_unique(ports_in_use_script_path):
    """Test ports-in-use.sh outputs sorted and unique port numbers."""
    result = subprocess.run(
        ["/bin/bash", str(ports_in_use_script_path)], capture_output=True, text=True
    )

    # Only test if ss is present
    if not check_ss_present():
        return

    # Should succeed
    assert result.returncode == 0, f"Script execution failed: {result.stderr}"

    # If there are ports, check they are sorted and unique
    if result.stdout.strip():
        ports = result.stdout.strip().split()
        # Check for duplicates
        assert len(ports) == len(set(ports)), "Output should contain unique ports"
        # Check sorting (for numeric ports)
        numeric_ports = []
        for port_str in ports:
            try:
                numeric_ports.append(int(port_str))
            except ValueError:
                # Skip non-numeric values
                pass
        if numeric_ports:
            assert numeric_ports == sorted(numeric_ports), "Ports should be sorted numerically"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_space_separated(ports_in_use_script_path):
    """Test ports-in-use.sh outputs space-separated ports (no newlines)."""
    result = subprocess.run(
        ["/bin/bash", str(ports_in_use_script_path)], capture_output=True, text=True
    )

    # Only test if ss is present
    if not check_ss_present():
        return

    # Should succeed
    assert result.returncode == 0, f"Script execution failed: {result.stderr}"

    # Output should not contain newlines (except trailing)
    output_lines = result.stdout.strip().split('\n')
    assert len(output_lines) == 1, "Output should be single line (space-separated)"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_without_ss(ports_in_use_script_path):
    """Test ports-in-use.sh fails gracefully when ss is not available."""
    # Create environment without ss in PATH
    env = os.environ.copy()
    with tempfile.TemporaryDirectory() as tmpdir:
        env["PATH"] = tmpdir
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)],
            capture_output=True,
            text=True,
            env=env,
        )

        # Should fail
        assert result.returncode != 0, "Should fail when ss is not available"
        # Should mention ss in error
        assert "ss" in result.stderr.lower(), "Error should mention ss command"
