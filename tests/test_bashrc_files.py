#!/usr/bin/env python3
"""Test suite for bashrc-files.sh script."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def bashrc_files_script_path():
    """Path to the bashrc-files.sh script."""
    return Path(__file__).parent.parent / "bash" / "bashrc-files.sh"


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    temp_file = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
    temp_file.write("# Test config file\n")
    temp_file.write("bookmarks:\n")
    temp_file.write('  test1: "/tmp/test1"\n')
    temp_file.write('  test2: "/tmp/test2"\n')
    temp_file.close()
    yield temp_file.name
    # Cleanup
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


@pytest.fixture
def temp_home():
    """Create a temporary HOME directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    import shutil

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def temp_bookmark_dirs():
    """Create temporary directories for bookmark testing."""
    temp_base = tempfile.mkdtemp()
    test1_dir = os.path.join(temp_base, "test1")
    test2_dir = os.path.join(temp_base, "test2")
    os.makedirs(test1_dir)
    os.makedirs(test2_dir)
    yield {"base": temp_base, "test1": test1_dir, "test2": test2_dir}
    # Cleanup
    import shutil

    if os.path.exists(temp_base):
        shutil.rmtree(temp_base)


def check_bash_present():
    """Check if /bin/bash is present on the system."""
    return os.path.exists("/bin/bash")


def test_bashrc_files_script_exists(bashrc_files_script_path):
    """Test that bashrc-files.sh script exists."""
    assert bashrc_files_script_path.exists(), (
        f"Script not found at {bashrc_files_script_path}"
    )


def test_bashrc_files_syntax_validation(bashrc_files_script_path):
    """Test that bashrc-files.sh has valid bash syntax."""
    result = subprocess.run(
        ["/bin/bash", "-n", str(bashrc_files_script_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Syntax error in script: {result.stderr}"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_basic_aliases(bashrc_files_script_path):
    """Test that bashrc-files.sh creates basic file aliases."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_files_script_path} && alias ll"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "ll" in result.stdout, "ll alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_la_alias(bashrc_files_script_path):
    """Test that bashrc-files.sh creates la alias."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_files_script_path} && alias la"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "la" in result.stdout, "la alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_lt_alias(bashrc_files_script_path):
    """Test that bashrc-files.sh creates lt alias."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_files_script_path} && alias lt"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "lt" in result.stdout, "lt alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_grep_alias(bashrc_files_script_path):
    """Test that bashrc-files.sh creates g alias."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_files_script_path} && alias g"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "g" in result.stdout, "g alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_tail_alias(bashrc_files_script_path):
    """Test that bashrc-files.sh creates t alias."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_files_script_path} && alias t"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "t" in result.stdout, "t alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_less_alias(bashrc_files_script_path):
    """Test that bashrc-files.sh creates l alias."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_files_script_path} && alias l"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "l" in result.stdout, "l alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_goto_useful_bash_scripts_alias(bashrc_files_script_path):
    """Test that bashrc-files.sh creates goto-useful-bash-scripts alias."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_files_script_path} && alias goto-useful-bash-scripts",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "goto-useful-bash-scripts" in result.stdout, (
        "goto-useful-bash-scripts alias should be defined"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_devnull_redirect_function(bashrc_files_script_path):
    """Test that bashrc-files.sh defines devnull-redirect function."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_files_script_path} && type devnull-redirect",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "devnull-redirect" in result.stdout, (
        "devnull-redirect function should be defined"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_findgrep_function(bashrc_files_script_path):
    """Test that bashrc-files.sh defines findgrep function."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_files_script_path} && type findgrep"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "findgrep" in result.stdout, "findgrep function should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_cdd_function(bashrc_files_script_path):
    """Test that bashrc-files.sh defines cdd function."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_files_script_path} && type cdd"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "cdd" in result.stdout, "cdd function should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_basenames_function(bashrc_files_script_path):
    """Test that bashrc-files.sh defines basenames function."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_files_script_path} && type basenames"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "basenames" in result.stdout, "basenames function should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_mv_ln_function(bashrc_files_script_path):
    """Test that bashrc-files.sh defines mv-ln function."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_files_script_path} && type mv-ln"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "mv-ln" in result.stdout, "mv-ln function should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_chmod_recursive_give_access_function(bashrc_files_script_path):
    """Test that bashrc-files.sh defines chmod-recursive-give-access function."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_files_script_path} && type chmod-recursive-give-access",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "chmod-recursive-give-access" in result.stdout, (
        "chmod-recursive-give-access function should be defined"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_chmod_recursive_locked_user_only_function(
    bashrc_files_script_path,
):
    """Test that bashrc-files.sh defines chmod-recursive-locked-user-only function."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_files_script_path} && type chmod-recursive-locked-user-only",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "chmod-recursive-locked-user-only" in result.stdout, (
        "chmod-recursive-locked-user-only function should be defined"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_grepfind_alias(bashrc_files_script_path):
    """Test that bashrc-files.sh creates grepfind alias."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_files_script_path} && alias grepfind"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "grepfind" in result.stdout, "grepfind alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_md5sum_recursive_alias(bashrc_files_script_path):
    """Test that bashrc-files.sh creates md5sum-recursive alias."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_files_script_path} && alias md5sum-recursive",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "md5sum-recursive" in result.stdout, (
        "md5sum-recursive alias should be defined"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_no_bookmarks_without_yq(bashrc_files_script_path):
    """Test that bashrc-files.sh doesn't create bookmark aliases without yq."""
    # Set FILE_BASHRC_CONFIG but don't have yq
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"FILE_BASHRC_CONFIG=/tmp/test.yml source {bashrc_files_script_path} && alias goto-test 2>/dev/null || echo 'ALIAS_NOT_FOUND'",
        ],
        capture_output=True,
        text=True,
    )

    # Should not fail, but bookmark alias should not exist
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    # goto-test should not be in output (alias not found)
    assert "ALIAS_NOT_FOUND" in result.stdout, (
        "Bookmark alias should not be created without yq"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_no_bookmarks_without_config(bashrc_files_script_path):
    """Test that bashrc-files.sh doesn't create bookmark aliases without config."""
    # Don't set FILE_BASHRC_CONFIG
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_files_script_path} && alias goto-test 2>/dev/null || echo 'ALIAS_NOT_FOUND'",
        ],
        capture_output=True,
        text=True,
    )

    # Should not fail, but bookmark alias should not exist
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    # goto-test should not be in output (alias not found)
    assert "ALIAS_NOT_FOUND" in result.stdout, (
        "Bookmark alias should not be created without config"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_cdd_function_with_temp_file(bashrc_files_script_path, temp_home):
    """Test cdd function with a temporary file."""
    # Create a temporary file
    test_file = os.path.join(temp_home, "test.txt")
    with open(test_file, "w") as f:
        f.write("test content")

    # Test cdd function
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_files_script_path} && cdd {test_file} && pwd",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"cdd function failed: {result.stderr}"
    assert temp_home in result.stdout, "Should change to file's directory"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_mv_ln_function_with_test_files(
    bashrc_files_script_path, temp_home
):
    """Test mv-ln function with temporary files."""
    # Create source file and target directory
    source_file = os.path.join(temp_home, "source.txt")
    target_dir = os.path.join(temp_home, "target")
    os.makedirs(target_dir)

    with open(source_file, "w") as f:
        f.write("test content")

    # Test mv-ln function
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"cd {temp_home} && source {bashrc_files_script_path} && mv-ln source.txt target",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"mv-ln function failed: {result.stderr}"

    # Check that file was moved
    moved_file = os.path.join(target_dir, "source.txt")
    assert os.path.exists(moved_file), "File should be moved to target directory"

    # Check that symlink was created
    symlink = os.path.join(temp_home, "source.txt")
    assert os.path.islink(symlink), "Symlink should be created in original location"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_mv_ln_function_error_nonexistent_dir(
    bashrc_files_script_path, temp_home
):
    """Test mv-ln function with non-existent target directory."""
    # Create source file
    source_file = os.path.join(temp_home, "source.txt")
    with open(source_file, "w") as f:
        f.write("test content")

    # Test mv-ln function with non-existent directory
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"cd {temp_home} && source {bashrc_files_script_path} && mv-ln source.txt nonexistent",
        ],
        capture_output=True,
        text=True,
    )

    # Should fail
    assert result.returncode != 0, "mv-ln should fail with non-existent directory"
    assert "ERROR" in result.stdout or "ERROR" in result.stderr, (
        "Should output error message"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_basenames_function_with_files(
    bashrc_files_script_path, temp_home
):
    """Test basenames function with test files."""
    # Create test files
    test_file1 = os.path.join(temp_home, "file1.txt")
    test_file2 = os.path.join(temp_home, "file2.txt")

    with open(test_file1, "w") as f:
        f.write("test1")
    with open(test_file2, "w") as f:
        f.write("test2")

    # Test basenames function
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"cd {temp_home} && source {bashrc_files_script_path} && basenames file1.txt file2.txt",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"basenames function failed: {result.stderr}"
    assert "file1.txt" in result.stdout, "Should output file1.txt"
    assert "file2.txt" in result.stdout, "Should output file2.txt"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_devnull_redirect_function_execution(bashrc_files_script_path):
    """Test devnull-redirect function."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_files_script_path} && devnull-redirect echo 'test'",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"devnull-redirect function failed: {result.stderr}"
    assert "test" in result.stdout, "Should output the command being run"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_bookmark_env_var(bashrc_files_script_path, temp_bookmark_dirs):
    """Test that bookmarks create environment variables with DIR_ prefix."""
    # Create a temporary config file
    temp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
    temp_config.write("# Test config file\n")
    temp_config.write("bookmarks:\n")
    temp_config.write(f'  test1: "{temp_bookmark_dirs["test1"]}"\n')
    temp_config.write(f'  test2: "{temp_bookmark_dirs["test2"]}"\n')
    temp_config.close()

    try:
        # Test that environment variables are created
        result = subprocess.run(
            [
                "/bin/bash",
                "-c",
                f"FILE_BASHRC_CONFIG={temp_config.name} source {bashrc_files_script_path} && echo $DIR_TEST1",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert temp_bookmark_dirs["test1"] in result.stdout, (
            "DIR_TEST1 environment variable should be set"
        )

        # Test second bookmark
        result = subprocess.run(
            [
                "/bin/bash",
                "-c",
                f"FILE_BASHRC_CONFIG={temp_config.name} source {bashrc_files_script_path} && echo $DIR_TEST2",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert temp_bookmark_dirs["test2"] in result.stdout, (
            "DIR_TEST2 environment variable should be set"
        )
    finally:
        if os.path.exists(temp_config.name):
            os.unlink(temp_config.name)


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_bookmark_env_var_naming_convention(
    bashrc_files_script_path, temp_bookmark_dirs
):
    """Test that bookmark names with hyphens create env vars with underscores."""
    # Create a temporary config file with hyphenated bookmark name
    temp_config = tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False)
    temp_config.write("# Test config file\n")
    temp_config.write("bookmarks:\n")
    temp_config.write(f'  my-special-folder: "{temp_bookmark_dirs["test1"]}"\n')
    temp_config.close()

    try:
        # Test that environment variable name is converted correctly
        result = subprocess.run(
            [
                "/bin/bash",
                "-c",
                f"FILE_BASHRC_CONFIG={temp_config.name} source {bashrc_files_script_path} && echo $DIR_MY_SPECIAL_FOLDER",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert temp_bookmark_dirs["test1"] in result.stdout, (
            "DIR_MY_SPECIAL_FOLDER environment variable should be set for my-special-folder"
        )
    finally:
        if os.path.exists(temp_config.name):
            os.unlink(temp_config.name)


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_files_goto_useful_bash_scripts_env_var(bashrc_files_script_path):
    """Test that goto-useful-bash-scripts also exports DIR_USEFUL_BASH_SCRIPTS."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_files_script_path} && echo $DIR_USEFUL_BASH_SCRIPTS",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    # The env var should be set and contain a path
    assert result.stdout.strip() != "", (
        "DIR_USEFUL_BASH_SCRIPTS environment variable should be set"
    )
