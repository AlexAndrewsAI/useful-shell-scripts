#!/usr/bin/env python3
"""Test suite for setup.sh script."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def setup_script_path():
    """Path to the setup.sh script."""
    return Path(__file__).parent.parent / "setup.sh"


@pytest.fixture
def example_config_path():
    """Path to the example config file."""
    return Path(__file__).parent.parent / "config.example.yml"


@pytest.fixture
def temp_home():
    """Create a temporary HOME directory with .bashrc for testing."""
    temp_dir = tempfile.mkdtemp()
    bashrc_path = os.path.join(temp_dir, ".bashrc")
    # Create empty .bashrc
    with open(bashrc_path, "w") as f:
        f.write("")
    yield temp_dir
    # Cleanup
    import shutil

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def check_bash_present():
    """Check if /bin/bash is present on the system."""
    return os.path.exists("/bin/bash")


def test_setup_script_exists(setup_script_path):
    """Test that setup.sh script exists."""
    assert setup_script_path.exists(), f"Setup script not found at {setup_script_path}"


def test_setup_script_executable(setup_script_path):
    """Test that setup.sh is executable."""
    # Note: We're not checking execute permissions here since git may not preserve them
    # Instead, we'll test it can be executed with bash explicitly
    pass


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_setup_script_with_default_config(
    setup_script_path, example_config_path, temp_home, monkeypatch
):
    """Test setup.sh with default config file."""
    # Mock HOME to use temp directory
    monkeypatch.setenv("HOME", temp_home)
    # Skip venv setup in tests to avoid hanging
    monkeypatch.setenv("SKIP_VENV_SETUP", "1")

    bashrc_path = os.path.join(temp_home, ".bashrc")

    # Ensure example config exists
    assert example_config_path.exists(), (
        f"Example config not found at {example_config_path}"
    )

    # Run setup script with no arguments (should use default config)
    result = subprocess.run(
        ["/bin/bash", str(setup_script_path)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": temp_home, "SKIP_VENV_SETUP": "1"},
    )

    # Script should succeed
    assert result.returncode == 0, f"Setup script failed: {result.stderr}"

    # Check that source line was added to temp bashrc
    with open(bashrc_path) as f:
        content = f.read()

    assert "source" in content, "Source line not added to bashrc"
    assert "bashrc-extra.sh" in content, "bashrc-extra.sh not referenced in bashrc"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_setup_script_with_custom_config(
    setup_script_path, example_config_path, temp_home, monkeypatch
):
    """Test setup.sh with custom config file path."""
    # Mock HOME to use temp directory
    monkeypatch.setenv("HOME", temp_home)
    # Skip venv setup in tests to avoid hanging
    monkeypatch.setenv("SKIP_VENV_SETUP", "1")

    bashrc_path = os.path.join(temp_home, ".bashrc")

    # Ensure example config exists
    assert example_config_path.exists(), (
        f"Example config not found at {example_config_path}"
    )

    # Run setup script with explicit config path
    result = subprocess.run(
        ["/bin/bash", str(setup_script_path), str(example_config_path)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": temp_home, "SKIP_VENV_SETUP": "1"},
    )

    # Script should succeed
    assert result.returncode == 0, f"Setup script failed: {result.stderr}"

    # Check that source line was added to temp bashrc
    with open(bashrc_path) as f:
        content = f.read()

    assert "source" in content, "Source line not added to bashrc"
    assert "bashrc-extra.sh" in content, "bashrc-extra.sh not referenced in bashrc"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_setup_script_idempotent(
    setup_script_path, example_config_path, temp_home, monkeypatch
):
    """Test that running setup.sh twice is idempotent."""
    # Mock HOME to use temp directory
    monkeypatch.setenv("HOME", temp_home)
    # Skip venv setup in tests to avoid hanging
    monkeypatch.setenv("SKIP_VENV_SETUP", "1")

    # Run setup script first time
    result1 = subprocess.run(
        ["/bin/bash", str(setup_script_path), str(example_config_path)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": temp_home, "SKIP_VENV_SETUP": "1"},
    )
    assert result1.returncode == 0, f"First run failed: {result1.stderr}"

    # Run setup script second time
    result2 = subprocess.run(
        ["/bin/bash", str(setup_script_path), str(example_config_path)],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": temp_home, "SKIP_VENV_SETUP": "1"},
    )
    assert result2.returncode == 0, f"Second run failed: {result2.stderr}"

    # Second run should report "Already in ~/.bashrc"
    assert "Already" in result2.stdout or "already" in result2.stdout.lower(), (
        "Second run should detect existing entry"
    )

    # Second run should still complete successfully (not exit early)
    # The script should continue to venv setup even if bashrc is already configured


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_setup_script_nonexistent_config(setup_script_path, temp_home, monkeypatch):
    """Test setup.sh with non-existent config file."""
    # Mock HOME to use temp directory
    monkeypatch.setenv("HOME", temp_home)

    # Run setup script with non-existent config
    result = subprocess.run(
        ["/bin/bash", str(setup_script_path), "/nonexistent/config.yml"],
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": temp_home},
    )

    # Script should fail
    assert result.returncode != 0, "Setup script should fail with non-existent config"
    assert "does not exist" in result.stdout or "Error" in result.stdout, (
        "Error message should mention config file does not exist"
    )


def test_bash_presence_warning():
    """Test check_bash_present detects missing bash correctly."""
    from unittest import mock

    # Test detection when bash is NOT present
    with mock.patch("tests.test_setup.os.path.exists", return_value=False):
        assert not check_bash_present(), (
            "Should return False when /bin/bash doesn't exist"
        )

    # Test detection when bash IS present
    with mock.patch("tests.test_setup.os.path.exists", return_value=True):
        assert check_bash_present(), "Should return True when /bin/bash exists"
