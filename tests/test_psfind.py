#!/usr/bin/env python3
"""Test suite for psfind.sh script."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from tests.test_utils import check_bash_present


@pytest.fixture
def psfind_script_path():
    """Path to the psfind.sh script."""
    return Path(__file__).parent.parent / "bash" / "psfind.sh"


@pytest.fixture
def mock_ps_env():
    """Create a temporary mock ps command and environment for testing."""
    mock_dir = tempfile.mkdtemp()
    ps_script = os.path.join(mock_dir, "ps")
    with open(ps_script, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("# Mock ps that returns simulated process output\n")
        f.write('echo "PID TTY          TIME CMD"\n')
        f.write('echo "1234 pts/0    00:00:01 bash"\n')
        f.write('echo "5678 pts/0    00:00:02 python"\n')
        f.write('echo "9012 pts/0    00:00:03 grep"\n')
    os.chmod(ps_script, 0o755)
    env = os.environ.copy()
    env["PATH"] = f"{mock_dir}:{env['PATH']}"
    yield env
    if os.path.exists(mock_dir):
        shutil.rmtree(mock_dir)


def test_psfind_script_exists(psfind_script_path):
    """Test that psfind.sh script exists."""
    assert psfind_script_path.exists(), (
        f"psfind script not found at {psfind_script_path}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_psfind_help(psfind_script_path):
    """Test psfind.sh help message."""
    result = subprocess.run(
        ["/bin/bash", str(psfind_script_path), "-h"], capture_output=True, text=True
    )

    # Help should exit successfully
    assert result.returncode == 0, f"Help failed: {result.stderr}"

    # Help should contain description
    assert (
        "DESCRIPTION" in result.stdout or "Find or kill processes" in result.stdout
    ), "Help message should contain description"

    # Help should contain usage
    assert "USAGE" in result.stdout or "Usage" in result.stdout, (
        "Help message should contain usage"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_psfind_no_arguments(psfind_script_path):
    """Test psfind.sh with no arguments (should fail)."""
    result = subprocess.run(
        ["/bin/bash", str(psfind_script_path)], capture_output=True, text=True
    )

    # Should fail with no arguments
    assert result.returncode != 0, "Should fail with no arguments"
    assert "Usage" in result.stdout or "usage" in result.stdout.lower(), (
        "Should show usage when no arguments provided"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_psfind_unknown_option(psfind_script_path):
    """Test psfind.sh with unknown option (should fail)."""
    result = subprocess.run(
        ["/bin/bash", str(psfind_script_path), "-x", "test"],
        capture_output=True,
        text=True,
    )

    # Should fail with unknown option
    assert result.returncode != 0, "Should fail with unknown option"
    assert "Unknown option" in result.stdout or "unknown" in result.stdout.lower(), (
        "Should show error for unknown option"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_psfind_basic_search(psfind_script_path):
    """Test psfind.sh basic search functionality."""
    # Search for a common process that's likely to be running
    # Using 'bash' or 'python' as they're likely to exist
    result = subprocess.run(
        ["/bin/bash", str(psfind_script_path), "bash"], capture_output=True, text=True
    )

    # Should succeed
    assert result.returncode == 0, f"Basic search failed: {result.stderr}"

    # Should show "Finding" in output
    assert "Finding" in result.stdout, "Should show 'Finding' in output"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_psfind_with_refine_pattern(psfind_script_path):
    """Test psfind.sh with refine pattern."""
    result = subprocess.run(
        ["/bin/bash", str(psfind_script_path), "bash", "."],
        capture_output=True,
        text=True,
    )

    # Should succeed
    assert result.returncode == 0, f"Search with refine pattern failed: {result.stderr}"

    # Should show "Finding" in output
    assert "Finding" in result.stdout, "Should show 'Finding' in output"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_psfind_word_regexp(psfind_script_path):
    """Test psfind.sh with word regexp option."""
    result = subprocess.run(
        ["/bin/bash", str(psfind_script_path), "-w", "bash"],
        capture_output=True,
        text=True,
    )

    # Should succeed
    assert result.returncode == 0, f"Word regexp search failed: {result.stderr}"

    # Should show "Finding" in output
    assert "Finding" in result.stdout, "Should show 'Finding' in output"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_psfind_not_pattern(psfind_script_path):
    """Test psfind.sh with not pattern option."""
    result = subprocess.run(
        ["/bin/bash", str(psfind_script_path), "-n", "grep", "bash"],
        capture_output=True,
        text=True,
    )

    # Should succeed
    assert result.returncode == 0, f"Not pattern search failed: {result.stderr}"

    # Should show "Finding" in output
    assert "Finding" in result.stdout, "Should show 'Finding' in output"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_psfind_kill_mode(psfind_script_path):
    """Test psfind.sh in kill mode (without actually killing)."""
    # Use a search term that's unlikely to match anything to be safe
    result = subprocess.run(
        ["/bin/bash", str(psfind_script_path), "-k", "nonexistent_process_xyz123"],
        capture_output=True,
        text=True,
    )

    # Should succeed even if no processes found
    assert result.returncode == 0, f"Kill mode failed: {result.stderr}"

    # Should show "Killing" in output
    assert "Killing" in result.stdout, "Should show 'Killing' in output"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_psfind_combined_options(psfind_script_path):
    """Test psfind.sh with combined options."""
    result = subprocess.run(
        ["/bin/bash", str(psfind_script_path), "-w", "-n", "grep", "bash"],
        capture_output=True,
        text=True,
    )

    # Should succeed
    assert result.returncode == 0, f"Combined options failed: {result.stderr}"

    # Should show "Finding" in output
    assert "Finding" in result.stdout, "Should show 'Finding' in output"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_psfind_with_mock_ps(psfind_script_path, mock_ps_env):
    """Test psfind.sh behavior when ps is available (mock)."""
    result = subprocess.run(
        ["/bin/bash", str(psfind_script_path), "bash"],
        capture_output=True,
        text=True,
        env=mock_ps_env,
    )

    # Should succeed with mock ps available
    assert result.returncode == 0, f"Script failed with mock ps: {result.stderr}"
    # Should show "Finding" in output
    assert "Finding" in result.stdout, "Should show 'Finding' in output"
