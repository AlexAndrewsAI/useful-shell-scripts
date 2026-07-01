#!/usr/bin/env python3
"""Test suite for psfind.sh script."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def psfind_script_path():
    """Path to the psfind.sh script."""
    return Path(__file__).parent.parent / "bash" / "psfind.sh"


def check_bash_present():
    """Check if /bin/bash is present on the system."""
    return os.path.exists("/bin/bash")


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


def test_bash_presence_warning():
    """Test that we warn if bash is not present."""
    if not check_bash_present():
        pytest.warns(UserWarning, match="/bin/bash not found")
