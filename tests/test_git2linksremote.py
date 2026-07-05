#!/usr/bin/env python3
"""Test suite for git2linksremote.sh script."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def git2linksremote_script_path():
    """Path to the git2linksremote.sh script."""
    return Path(__file__).parent.parent / "bash" / "git2linksremote.sh"


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

    # Add a remote (required for the script)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/test/repo.git"],
        cwd=temp_dir,
        capture_output=True,
    )

    # Create some test files
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("content")

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


def test_git2linksremote_script_exists(git2linksremote_script_path):
    """Test that git2linksremote.sh script exists."""
    assert git2linksremote_script_path.exists(), (
        f"git2linksremote script not found at {git2linksremote_script_path}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_git2linksremote_no_git_repo(git2linksremote_script_path):
    """Test git2linksremote.sh outside a git repository (should fail)."""
    temp_dir = tempfile.mkdtemp()

    try:
        result = subprocess.run(
            ["/bin/bash", str(git2linksremote_script_path)],
            capture_output=True,
            text=True,
            cwd=temp_dir,
        )

        # Should fail outside git repo
        assert result.returncode != 0, "Should fail outside git repository"
        assert (
            "Not a git repository" in result.stdout or "git" in result.stdout.lower()
        ), "Should show error about not being in a git repository"

    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_git2linksremote_with_git_repo(git2linksremote_script_path, temp_git_repo):
    """Test git2linksremote.sh inside a git repository."""
    result = subprocess.run(
        ["/bin/bash", str(git2linksremote_script_path)],
        capture_output=True,
        text=True,
        cwd=temp_git_repo,
    )

    # Should succeed
    assert result.returncode == 0, f"Script failed in git repo: {result.stderr}"

    # Should contain markdown headers
    assert "## File List" in result.stdout or "File List" in result.stdout, (
        "Should show file list header"
    )

    # Should contain markdown links
    assert "[" in result.stdout and "](" in result.stdout, (
        "Should contain markdown link format"
    )

    # Should contain the test file
    assert "test.txt" in result.stdout, "Should list the test file"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_git2linksremote_ssh_url_conversion(git2linksremote_script_path, temp_git_repo):
    """Test git2linksremote.sh with SSH remote URL."""
    # Change remote to SSH format
    subprocess.run(
        ["git", "remote", "set-url", "origin", "git@github.com:test/repo.git"],
        cwd=temp_git_repo,
        capture_output=True,
    )

    result = subprocess.run(
        ["/bin/bash", str(git2linksremote_script_path)],
        capture_output=True,
        text=True,
        cwd=temp_git_repo,
    )

    # Should succeed
    assert result.returncode == 0, f"SSH URL conversion failed: {result.stderr}"

    # Should convert SSH to HTTPS in output
    assert "https://github.com" in result.stdout, (
        "Should convert SSH URL to HTTPS format"
    )

    # Should not contain SSH format in output
    assert "git@github.com:" not in result.stdout, (
        "Should not contain SSH format in output"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_git2linksremote_branch_detection(git2linksremote_script_path, temp_git_repo):
    """Test git2linksremote.sh branch detection."""
    # Create and checkout a new branch
    subprocess.run(
        ["git", "checkout", "-b", "test-branch"], cwd=temp_git_repo, capture_output=True
    )

    result = subprocess.run(
        ["/bin/bash", str(git2linksremote_script_path)],
        capture_output=True,
        text=True,
        cwd=temp_git_repo,
    )

    # Should succeed
    assert result.returncode == 0, f"Branch detection failed: {result.stderr}"

    # Should contain the branch name
    assert "test-branch" in result.stdout, "Should detect and show branch name"


def test_bash_presence_warning():
    """Test check_bash_present detects missing bash correctly."""
    from unittest import mock

    # Test detection when bash is NOT present
    with mock.patch("tests.test_git2linksremote.os.path.exists", return_value=False):
        assert not check_bash_present(), (
            "Should return False when /bin/bash doesn't exist"
        )

    # Test detection when bash IS present
    with mock.patch("tests.test_git2linksremote.os.path.exists", return_value=True):
        assert check_bash_present(), "Should return True when /bin/bash exists"
