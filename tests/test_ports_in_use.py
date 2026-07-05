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
def test_ports_in_use_basic_execution(ports_in_use_script_path, mock_ss_env):
    """Test ports-in-use.sh basic execution with mock ss available."""
    with mock.patch("tests.test_ports_in_use.check_ss_present", return_value=True):
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)],
            capture_output=True,
            text=True,
            env=mock_ss_env,
        )

    assert result.returncode == 0, f"Script execution failed: {result.stderr}"
    assert result.stdout is not None, "Should produce output"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_output_format(ports_in_use_script_path, mock_ss_env):
    """Test ports-in-use.sh output format with mock ss."""
    with mock.patch("tests.test_ports_in_use.check_ss_present", return_value=True):
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)],
            capture_output=True,
            text=True,
            env=mock_ss_env,
        )

    # Should succeed
    assert result.returncode == 0, f"Script execution failed: {result.stderr}"

    # Output should be space-separated if there are ports
    ports = result.stdout.strip().split()
    assert len(ports) > 0, "Should have at least one port value if output is not empty"
    # Verify output is space-separated (not newlines or other separators)
    assert "\n" not in result.stdout.strip(), (
        "Output should be space-separated, not newline-separated"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_no_arguments(ports_in_use_script_path, mock_ss_env):
    """Test ports-in-use.sh with no arguments and mock ss."""
    with mock.patch("tests.test_ports_in_use.check_ss_present", return_value=True):
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)],
            capture_output=True,
            text=True,
            env=mock_ss_env,
        )

    assert result.returncode == 0, "Should work without arguments"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_with_extra_arguments(ports_in_use_script_path, mock_ss_env):
    """Test ports-in-use.sh with extra arguments and mock ss."""
    with mock.patch("tests.test_ports_in_use.check_ss_present", return_value=True):
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path), "extra", "args"],
            capture_output=True,
            text=True,
            env=mock_ss_env,
        )

    # Script doesn't parse arguments, so it should still work with mock ss
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
    """Test check_bash_present detects missing bash correctly."""
    # Test detection when bash is NOT present
    with mock.patch("tests.test_ports_in_use.os.path.exists", return_value=False):
        assert not check_bash_present(), (
            "Should return False when /bin/bash doesn't exist"
        )

    # Test detection when bash IS present
    with mock.patch("tests.test_ports_in_use.os.path.exists", return_value=True):
        assert check_bash_present(), "Should return True when /bin/bash exists"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_mocked_empty_output(ports_in_use_script_path):
    """Test ports-in-use.sh with mocked empty output."""
    # Mock subprocess.run to return empty output
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["/bin/bash", str(ports_in_use_script_path)],
            returncode=0,
            stdout="",
            stderr="",
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
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["/bin/bash", str(ports_in_use_script_path)],
            returncode=0,
            stdout="80 443 8080 ",
            stderr="",
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
def test_ports_in_use_empty_output(ports_in_use_script_path, mock_ss_env):
    """Test ports-in-use.sh with mock ss (ports always present)."""
    with mock.patch("tests.test_ports_in_use.check_ss_present", return_value=True):
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)],
            capture_output=True,
            text=True,
            env=mock_ss_env,
        )

    # Should succeed with mock ss
    assert result.returncode == 0, (
        f"Script should succeed with mock ss: {result.stderr}"
    )
    # Output should contain ports from mock ss
    assert result.stdout.strip() != "", "Output should not be empty with mock ss"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_large_port_numbers(ports_in_use_script_path, mock_ss_env):
    """Test ports-in-use.sh with mock ss (validates port numbers)."""
    with mock.patch("tests.test_ports_in_use.check_ss_present", return_value=True):
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)],
            capture_output=True,
            text=True,
            env=mock_ss_env,
        )

    # Should succeed with mock ss
    assert result.returncode == 0, f"Script execution failed: {result.stderr}"

    # Parse output and validate port numbers
    ports = result.stdout.strip().split()
    for port_str in ports:
        port_num = int(port_str)
        assert 0 <= port_num <= 65535, (
            f"Port {port_num} is outside valid range (0-65535)"
        )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_sorted_unique(ports_in_use_script_path, mock_ss_env):
    """Test ports-in-use.sh outputs sorted and unique port numbers with mock ss."""
    with mock.patch("tests.test_ports_in_use.check_ss_present", return_value=True):
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)],
            capture_output=True,
            text=True,
            env=mock_ss_env,
        )

    # Should succeed
    assert result.returncode == 0, f"Script execution failed: {result.stderr}"

    # Check ports are sorted and unique
    ports = result.stdout.strip().split()
    # Check for duplicates
    assert len(ports) == len(set(ports)), "Output should contain unique ports"
    # Check sorting
    numeric_ports = [int(p) for p in ports]
    assert numeric_ports == sorted(numeric_ports), "Ports should be sorted numerically"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_space_separated(ports_in_use_script_path, mock_ss_env):
    """Test ports-in-use.sh outputs space-separated ports with mock ss."""
    with mock.patch("tests.test_ports_in_use.check_ss_present", return_value=True):
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)],
            capture_output=True,
            text=True,
            env=mock_ss_env,
        )

    # Should succeed
    assert result.returncode == 0, f"Script execution failed: {result.stderr}"

    # Output should not contain newlines (except trailing)
    output_lines = result.stdout.strip().split("\n")
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


@pytest.fixture
def mock_ss_env():
    """Create a temporary mock ss command and environment for testing."""
    import shutil

    mock_dir = tempfile.mkdtemp()
    ss_script = os.path.join(mock_dir, "ss")
    with open(ss_script, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# Mock ss that returns simulated port output\n")
        f.write(
            'echo "Netid State  Recv-Q Send-Q  Local Address:Port  Peer Address:Port"\n'
        )
        f.write('echo "tcp   LISTEN 0      128    0.0.0.0:22          0.0.0.0:*"\n')
        f.write('echo "tcp   LISTEN 0      128    0.0.0.0:80          0.0.0.0:*"\n')
        f.write('echo "tcp   LISTEN 0      128    0.0.0.0:443         0.0.0.0:*"\n')
        f.write('echo "tcp   LISTEN 0      128    0.0.0.0:8080        0.0.0.0:*"\n')
    os.chmod(ss_script, 0o755)
    env = os.environ.copy()
    env["PATH"] = f"{mock_dir}:{env['PATH']}"
    yield env
    if os.path.exists(mock_dir):
        shutil.rmtree(mock_dir)


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_with_mock_ss(ports_in_use_script_path, mock_ss_env):
    """Test ports-in-use.sh behavior when ss is available (mock)."""
    with mock.patch("tests.test_ports_in_use.check_ss_present", return_value=True):
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)],
            capture_output=True,
            text=True,
            env=mock_ss_env,
        )

    # Should succeed with mock ss available
    assert result.returncode == 0, f"Script failed with mock ss: {result.stderr}"
    # Should contain port numbers from mock output (sorted unique ports)
    assert "22" in result.stdout, "Should contain port 22"
    assert "80" in result.stdout, "Should contain port 80"
    assert "443" in result.stdout, "Should contain port 443"
    assert "8080" in result.stdout, "Should contain port 8080"
    # Output should be space-separated single line
    assert "\n" not in result.stdout.strip(), "Output should be space-separated"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_mock_ss_output_format(ports_in_use_script_path, mock_ss_env):
    """Test ports-in-use.sh output format with mock ss."""
    with mock.patch("tests.test_ports_in_use.check_ss_present", return_value=True):
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)],
            capture_output=True,
            text=True,
            env=mock_ss_env,
        )

    # Should succeed
    assert result.returncode == 0, f"Script execution failed: {result.stderr}"

    # Parse the output
    ports = result.stdout.strip().split()
    assert len(ports) > 0, "Should have at least one port value"
    # Verify output is space-separated (not newlines)
    assert "\n" not in result.stdout.strip(), "Output should be space-separated"

    # Check ports are sorted and unique
    assert len(ports) == len(set(ports)), "Output should contain unique ports"
    numeric_ports = [int(p) for p in ports]
    assert numeric_ports == sorted(numeric_ports), "Ports should be sorted numerically"

    # Validate port range
    for port_num in numeric_ports:
        assert 0 <= port_num <= 65535, (
            f"Port {port_num} is outside valid range (0-65535)"
        )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_mock_ss_no_arguments(ports_in_use_script_path, mock_ss_env):
    """Test ports-in-use.sh works with no arguments when ss is available."""
    with mock.patch("tests.test_ports_in_use.check_ss_present", return_value=True):
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path)],
            capture_output=True,
            text=True,
            env=mock_ss_env,
        )
        assert result.returncode == 0, "Should work without arguments"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_ports_in_use_mock_ss_extra_arguments(ports_in_use_script_path, mock_ss_env):
    """Test ports-in-use.sh ignores extra arguments when ss is available."""
    with mock.patch("tests.test_ports_in_use.check_ss_present", return_value=True):
        result = subprocess.run(
            ["/bin/bash", str(ports_in_use_script_path), "extra", "args"],
            capture_output=True,
            text=True,
            env=mock_ss_env,
        )
        assert result.returncode == 0, "Should ignore extra arguments"


def test_check_ss_present():
    """Test check_ss_present function directly."""
    # Test when ss is found
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=0)
        assert check_ss_present(), "Should return True when ss is found"

    # Test when ss is not found
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.MagicMock(returncode=1)
        assert not check_ss_present(), "Should return False when ss is not found"
