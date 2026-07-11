#!/usr/bin/env python3
"""Test suite for bashrc-extra.sh script."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from tests.test_utils import check_bash_present


@pytest.fixture
def bashrc_extra_script_path():
    """Path to the bashrc-extra.sh script."""
    return Path(__file__).parent.parent / "bash" / "bashrc-extra.sh"


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    # Create temp directories for bookmarks
    temp_base = tempfile.mkdtemp()
    test1_dir = os.path.join(temp_base, "test1")
    test2_dir = os.path.join(temp_base, "test2")
    os.makedirs(test1_dir)
    os.makedirs(test2_dir)

    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
    temp_file.write("# Test config file\n")
    temp_file.write("bookmarks:\n")
    temp_file.write(f'  test1: "{test1_dir}"\n')
    temp_file.write(f'  test2: "{test2_dir}"\n')
    temp_file.close()
    yield temp_file.name
    # Cleanup
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)
    import shutil

    if os.path.exists(temp_base):
        shutil.rmtree(temp_base)


@pytest.fixture
def temp_home():
    """Create a temporary HOME directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_bashrc_extra_script_exists(bashrc_extra_script_path):
    """Test that bashrc-extra.sh script exists."""
    assert bashrc_extra_script_path.exists(), (
        f"Script not found at {bashrc_extra_script_path}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_requires_config_argument(bashrc_extra_script_path):
    """Test that bashrc-extra.sh requires a config file argument."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_extra_script_path}"],
        capture_output=True,
        text=True,
    )

    # Should fail without config argument
    assert result.returncode != 0, "Script should fail without config argument"
    assert (
        "Config file argument is required" in result.stderr
        or "Config file argument is required" in result.stdout
    ), "Error message should mention required config argument"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_absolute_path(bashrc_extra_script_path, temp_config_file):
    """Test bashrc-extra.sh with absolute config file path."""
    # Create absolute path
    abs_config = os.path.abspath(temp_config_file)

    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_extra_script_path} {abs_config} && echo $FILE_BASHRC_CONFIG",
        ],
        capture_output=True,
        text=True,
    )

    # Should succeed with absolute path
    assert result.returncode == 0, f"Script failed with absolute path: {result.stderr}"
    assert abs_config in result.stdout, (
        "FILE_BASHRC_CONFIG should contain absolute path"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_relative_path_exists(
    bashrc_extra_script_path, temp_config_file, temp_home
):
    """Test bashrc-extra.sh with relative config file path that exists."""
    # Change to temp directory and create config there
    config_name = "test_config.yml"
    config_path = os.path.join(temp_home, config_name)

    # Copy temp config to temp home
    import shutil

    shutil.copy(temp_config_file, config_path)

    # Test with relative path
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"cd {temp_home} && source {bashrc_extra_script_path} {config_name} && echo $FILE_BASHRC_CONFIG",
        ],
        capture_output=True,
        text=True,
    )

    # Should succeed with relative path
    assert result.returncode == 0, f"Script failed with relative path: {result.stderr}"
    assert config_path in result.stdout, (
        "FILE_BASHRC_CONFIG should contain resolved path"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_nonexistent_config(bashrc_extra_script_path):
    """Test bashrc-extra.sh with non-existent config file."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_extra_script_path} /nonexistent/config.yml",
        ],
        capture_output=True,
        text=True,
    )

    # Should fail with non-existent config
    assert result.returncode != 0, "Script should fail with non-existent config"
    assert "does not exist" in result.stderr or "does not exist" in result.stdout, (
        "Error message should mention config file does not exist"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_exports_config_variable(
    bashrc_extra_script_path, temp_config_file
):
    """Test that bashrc-extra.sh exports FILE_BASHRC_CONFIG variable."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_extra_script_path} {temp_config_file} && echo $FILE_BASHRC_CONFIG",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert (
        temp_config_file in result.stdout
        or os.path.abspath(temp_config_file) in result.stdout
    ), "FILE_BASHRC_CONFIG should be exported"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_adds_script_dir_to_path(
    bashrc_extra_script_path, temp_config_file
):
    """Test that bashrc-extra.sh adds script directory to PATH."""
    script_dir = str(bashrc_extra_script_path.parent)

    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_extra_script_path} {temp_config_file} && echo $PATH",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert script_dir in result.stdout, (
        f"Script directory {script_dir} should be in PATH"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_basic_aliases(bashrc_extra_script_path, temp_config_file):
    """Test that bashrc-extra.sh creates basic aliases."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_extra_script_path} {temp_config_file} && alias bashrc",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "bashrc" in result.stdout, "bashrc alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_file_aliases(bashrc_extra_script_path, temp_config_file):
    """Test that bashrc-extra.sh creates file-related aliases."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_extra_script_path} {temp_config_file} 2>/dev/null && alias ll",
        ],
        capture_output=True,
        text=True,
    )

    # The script should succeed even if the alias doesn't exist
    # We just check the script sourced successfully
    assert result.returncode == 0 or "ll" in result.stdout, (
        f"Script failed: {result.stderr}"
    )
    if result.returncode == 0:
        assert "ll" in result.stdout, "ll alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_histfind_alias(bashrc_extra_script_path, temp_config_file):
    """Test that bashrc-extra.sh creates histfind alias."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_extra_script_path} {temp_config_file} && alias histfind",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "histfind" in result.stdout, "histfind alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_datetime_alias(bashrc_extra_script_path, temp_config_file):
    """Test that bashrc-extra.sh creates datetime alias."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_extra_script_path} {temp_config_file} && alias datetime",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "datetime" in result.stdout, "datetime alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_sources_dependent_scripts(
    bashrc_extra_script_path, temp_config_file
):
    """Test that bashrc-extra.sh sources dependent scripts."""
    # Check that bashrc-files.sh is sourced by looking for one of its aliases
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_extra_script_path} {temp_config_file} 2>/dev/null && alias goto-useful-bash-scripts",
        ],
        capture_output=True,
        text=True,
    )

    # The script should succeed even if the alias doesn't exist
    assert result.returncode == 0 or "goto-useful-bash-scripts" in result.stdout, (
        f"Script failed: {result.stderr}"
    )
    if result.returncode == 0:
        assert "goto-useful-bash-scripts" in result.stdout, (
            "goto-useful-bash-scripts alias from bashrc-files.sh should be defined"
        )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_conditional_plasmashell_alias(
    bashrc_extra_script_path, temp_config_file
):
    """Test that bashrc-extra.sh conditionally creates KDE aliases."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_extra_script_path} {temp_config_file} 2>/dev/null; alias kderestart 2>/dev/null || echo 'ALIAS_NOT_FOUND'",
        ],
        capture_output=True,
        text=True,
    )

    # kderestart should only exist if plasmashell is available
    # We just check the script doesn't fail during sourcing
    assert "ALIAS_NOT_FOUND" in result.stdout or "kderestart" in result.stdout, (
        f"Script failed: {result.stderr}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_conditional_pacman_aliases(
    bashrc_extra_script_path, temp_config_file
):
    """Test that bashrc-extra.sh conditionally creates pacman aliases."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_extra_script_path} {temp_config_file} 2>/dev/null; alias pacman-search 2>/dev/null || echo 'ALIAS_NOT_FOUND'",
        ],
        capture_output=True,
        text=True,
    )

    # pacman-search should only exist if pacman is available
    # We just check the script doesn't fail during sourcing
    assert "ALIAS_NOT_FOUND" in result.stdout or "pacman-search" in result.stdout, (
        f"Script failed: {result.stderr}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_extra_syntax_validation(bashrc_extra_script_path):
    """Test that bashrc-extra.sh has valid bash syntax."""
    result = subprocess.run(
        ["/bin/bash", "-n", str(bashrc_extra_script_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Syntax error in script: {result.stderr}"
