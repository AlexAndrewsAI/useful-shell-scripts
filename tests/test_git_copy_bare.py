#!/usr/bin/env python3
"""Test suite for git-copy-bare.sh script."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def git_copy_bare_script_path():
    """Path to the git-copy-bare.sh script."""
    return Path(__file__).parent.parent / "bash" / "git-copy-bare.sh"


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    temp_dir = tempfile.mkdtemp()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_dir,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=temp_dir, capture_output=True
    )

    # Create some test files
    test_file1 = Path(temp_dir) / "test1.txt"
    test_file1.write_text("content1")

    test_dir = Path(temp_dir) / "subdir"
    test_dir.mkdir()
    test_file2 = test_dir / "test2.txt"
    test_file2.write_text("content2")

    # Add and commit files
    subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"], cwd=temp_dir, capture_output=True
    )

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


def check_bash_present():
    """Check if /bin/bash is present on the system."""
    return os.path.exists("/bin/bash")


def test_git_copy_bare_script_exists(git_copy_bare_script_path):
    """Test that git-copy-bare.sh script exists."""
    assert git_copy_bare_script_path.exists(), (
        f"git-copy-bare script not found at {git_copy_bare_script_path}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_git_copy_bare_help(git_copy_bare_script_path):
    """Test git-copy-bare.sh help message."""
    result = subprocess.run(
        ["/bin/bash", str(git_copy_bare_script_path), "-h"],
        capture_output=True,
        text=True,
    )

    # Help should exit successfully
    assert result.returncode == 0, f"Help failed: {result.stderr}"

    # Help should contain description
    assert (
        "Copy all files tracked by git" in result.stdout
        or "copy" in result.stdout.lower()
    ), "Help message should contain description"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_git_copy_bare_no_output(git_copy_bare_script_path):
    """Test git-copy-bare.sh with no output directory (should fail)."""
    result = subprocess.run(
        ["/bin/bash", str(git_copy_bare_script_path)], capture_output=True, text=True
    )

    # Should fail with no output directory
    assert result.returncode != 0, "Should fail with no output directory"
    assert (
        "output directory is required" in result.stderr
        or "output" in result.stderr.lower()
    ), "Should show error about missing output directory"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_git_copy_bare_unknown_option(git_copy_bare_script_path):
    """Test git-copy-bare.sh with unknown option (should fail)."""
    result = subprocess.run(
        ["/bin/bash", str(git_copy_bare_script_path), "-x", "/tmp/output"],
        capture_output=True,
        text=True,
    )

    # Should fail with unknown option
    assert result.returncode != 0, "Should fail with unknown option"
    assert "Unknown option" in result.stderr or "unknown" in result.stderr.lower(), (
        "Should show error for unknown option"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_git_copy_bare_basic_copy(git_copy_bare_script_path, temp_git_repo):
    """Test git-copy-bare.sh basic copy functionality."""
    output_dir = tempfile.mkdtemp()

    try:
        result = subprocess.run(
            [
                "/bin/bash",
                str(git_copy_bare_script_path),
                "-i",
                temp_git_repo,
                output_dir,
            ],
            capture_output=True,
            text=True,
        )

        # Should succeed
        assert result.returncode == 0, f"Basic copy failed: {result.stderr}"

        # Check that files were copied
        assert (Path(output_dir) / "test1.txt").exists(), "test1.txt should be copied"
        assert (Path(output_dir) / "subdir" / "test2.txt").exists(), (
            "subdir/test2.txt should be copied"
        )

        # Check file contents
        assert (Path(output_dir) / "test1.txt").read_text() == "content1", (
            "File content should match"
        )
        assert (Path(output_dir) / "subdir" / "test2.txt").read_text() == "content2", (
            "File content should match"
        )

        # Check output messages
        assert "copied: test1.txt" in result.stdout, "Should show copied message"
        assert "copied: subdir/test2.txt" in result.stdout, "Should show copied message"

    finally:
        shutil.rmtree(output_dir)


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_git_copy_bare_default_input(git_copy_bare_script_path, temp_git_repo):
    """Test git-copy-bare.sh with default input directory (current dir)."""
    output_dir = tempfile.mkdtemp()

    try:
        # Change to temp git repo and run script with default input
        result = subprocess.run(
            ["/bin/bash", str(git_copy_bare_script_path), output_dir],
            capture_output=True,
            text=True,
            cwd=temp_git_repo,
        )

        # Should succeed
        assert result.returncode == 0, f"Default input copy failed: {result.stderr}"

        # Check that files were copied
        assert (Path(output_dir) / "test1.txt").exists(), "test1.txt should be copied"

    finally:
        shutil.rmtree(output_dir)


def test_bash_presence_warning():
    """Test check_bash_present detects missing bash correctly."""
    from unittest import mock

    # Test detection when bash is NOT present
    with mock.patch("tests.test_git_copy_bare.os.path.exists", return_value=False):
        assert not check_bash_present(), (
            "Should return False when /bin/bash doesn't exist"
        )

    # Test detection when bash IS present
    with mock.patch("tests.test_git_copy_bare.os.path.exists", return_value=True):
        assert check_bash_present(), "Should return True when /bin/bash exists"
