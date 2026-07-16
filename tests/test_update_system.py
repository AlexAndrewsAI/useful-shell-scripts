#!/usr/bin/env python3
"""Test suite for update-system.sh script."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from tests.test_utils import check_bash_present

SCRIPT_DIR = Path(__file__).parent.parent / "bash"
UPDATE_SYSTEM = SCRIPT_DIR / "update-system.sh"
YAML_PARSER_SCRIPT = SCRIPT_DIR.parent / "python" / "yaml_parser.py"


def _parse_yaml_config(config_path: str) -> subprocess.CompletedProcess[str]:
    """Run the shared YAML parser and return a dict of CONFIG_ vars."""
    script = (
        "CONFIG_TMP_FILES=()\n"
        "load_config() {\n"
        '    local config_file="$1"\n'
        "    local tmp_config\n"
        '    tmp_config="$(mktemp)"\n'
        '    CONFIG_TMP_FILES+=("$tmp_config")\n'
        f'    python3 "{YAML_PARSER_SCRIPT}" "$config_file" > "$tmp_config"\n'
        '    source "$tmp_config"\n'
        "}\n"
        f'load_config "{config_path}"\n'
        # Print all CONFIG_ variables for assertion
        'echo "STEAMOS=$CONFIG_STEAMOS"\n'
        'echo "FORCE_INIT=$CONFIG_FORCE_INIT"\n'
        'echo "DECKY=$CONFIG_DECKY"\n'
        'echo "PACMAN_COUNT=${#CONFIG_PACMAN[@]}"\n'
        'echo "AUR_COUNT=${#CONFIG_AUR[@]}"\n'
        'echo "FLATPAK_COUNT=${#CONFIG_FLATPAK[@]}"\n'
        'echo "NPM_COUNT=${#CONFIG_NPM[@]}"\n'
        'echo "SNAP_COUNT=${#CONFIG_SNAP[@]}"\n'
        'echo "APT_COUNT=${#CONFIG_APT[@]}"\n'
        'echo "DNF_COUNT=${#CONFIG_DNF[@]}"\n'
        'echo "BREW_COUNT=${#CONFIG_BREW[@]}"\n'
        'echo "NIX_COUNT=${#CONFIG_NIX[@]}"\n'
        'echo "CARGO_COUNT=${#CONFIG_CARGO[@]}"\n'
        'echo "GO_COUNT=${#CONFIG_GO[@]}"\n'
    )
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    return result


def _source_function(func_name: str) -> str:
    """Build a bash script that sources a single function from update-system.sh."""
    return f'_SOURCE_ONLY=true; source "{UPDATE_SYSTEM}"; declare -f {func_name}\n'


@pytest.fixture
def update_system_script_path():
    """Path to the update-system.sh script."""
    return UPDATE_SYSTEM


@pytest.fixture
def example_config_path():
    """Path to the example YAML config file."""
    return SCRIPT_DIR.parent / "config.example.yaml"


@pytest.fixture
def minimal_config():
    """Create a minimal YAML config that disables all optional features."""
    config_content = (
        "steamos: false\n"
        "force_init: false\n"
        "pacman: []\n"
        "aur: []\n"
        "flatpak: []\n"
        "npm: []\n"
        "snap: []\n"
        "apt: []\n"
        "dnf: []\n"
        "brew: []\n"
        "nix: []\n"
        "cargo: []\n"
        "go: []\n"
        "git: {}\n"
        "decky: false\n"
        "distrobox: {}\n"
    )
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, prefix="update-system-test-"
    )
    tmp.write(config_content)
    tmp.close()
    yield tmp.name
    os.unlink(tmp.name)


# ---------------------------------------------------------------------------
# Basic script tests
# ---------------------------------------------------------------------------


def test_update_system_script_exists(update_system_script_path):
    """Test that update-system.sh script exists."""
    assert update_system_script_path.exists(), (
        f"Script not found at {update_system_script_path}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_syntax_validation(update_system_script_path):
    """Test that update-system.sh has valid bash syntax."""
    result = subprocess.run(
        ["/bin/bash", "-n", str(update_system_script_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax error in script: {result.stderr}"


# ---------------------------------------------------------------------------
# Argument parsing tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_help_long_flag(update_system_script_path):
    """Test that --help prints usage and exits successfully."""
    result = subprocess.run(
        ["/bin/bash", str(update_system_script_path), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"--help should exit 0: {result.stderr}"
    assert "USAGE" in result.stdout or "Usage" in result.stdout, (
        "Help output should contain USAGE section"
    )
    assert "OPTIONS" in result.stdout or "options" in result.stdout.lower(), (
        "Help output should contain OPTIONS section"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_help_short_flag(update_system_script_path):
    """Test that -h also works."""
    result = subprocess.run(
        ["/bin/bash", str(update_system_script_path), "-h"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"-h should exit 0: {result.stderr}"
    assert "SteamDeck" in result.stdout, "Help should mention SteamDeck"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_unknown_option(update_system_script_path):
    """Test that unknown options cause an error."""
    result = subprocess.run(
        ["/bin/bash", str(update_system_script_path), "--bogus-flag"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Unknown option should cause non-zero exit"
    assert "Unknown" in result.stdout or "unknown" in result.stdout.lower(), (
        "Should print error about unknown option"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_config_not_found(update_system_script_path):
    """Test that missing .config-location.dat causes an error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        script_copy = os.path.join(tmpdir, "bash", "update-system.sh")
        os.makedirs(os.path.dirname(script_copy))
        shutil.copy2(update_system_script_path, script_copy)
        result = subprocess.run(
            ["/bin/bash", script_copy],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0, (
            "Missing .config-location.dat should cause non-zero exit"
        )
        assert (
            ".config-location.dat" in result.stdout
            or "setup.sh" in result.stdout.lower()
        ), "Error message should mention .config-location.dat and setup.sh"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_config_dat_points_nowhere(update_system_script_path):
    """Test that a .config-location.dat pointing to a missing file causes an error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dat_path = os.path.join(tmpdir, ".config-location.dat")
        with open(dat_path, "w") as f:
            f.write("/nonexistent/config.yaml")
        result = subprocess.run(
            ["/bin/bash", str(update_system_script_path)],
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
        assert result.returncode != 0, (
            "Config file not found should cause non-zero exit"
        )
        assert (
            "not found" in result.stdout.lower() or "error" in result.stdout.lower()
        ), "Error message should mention config file not found"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_init_flag_parsing(minimal_config):
    """Test that --init flag sets FORCE_INIT correctly."""
    script = (
        "POSITIONAL_ARGS=()\n"
        "FORCE_INIT=FALSE\n"
        'CONFIG_FILE=""\n'
        "\n"
        "while [[ $# -gt 0 ]]; do\n"
        "    case $1 in\n"
        "        -i|--init)\n"
        '            FORCE_INIT="TRUE"\n'
        "            shift\n"
        "            ;;\n"
        "        -c|--config)\n"
        '            CONFIG_FILE="$2"\n'
        "            shift 2\n"
        "            ;;\n"
        "        *)\n"
        '            POSITIONAL_ARGS+=("$1")\n'
        "            shift\n"
        "            ;;\n"
        "    esac\n"
        "done\n"
        "\n"
        'set -- "${POSITIONAL_ARGS[@]}"\n'
        "\n"
        'echo "FORCE_INIT=$FORCE_INIT"\n'
        'echo "CONFIG_FILE=$CONFIG_FILE"\n'
    )
    result = subprocess.run(
        ["/bin/bash", "-c", script, "bash", "--init", "-c", minimal_config],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Argument parsing failed: {result.stderr}"
    assert "FORCE_INIT=TRUE" in result.stdout, "--init should set FORCE_INIT=TRUE"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_config_force_init_from_yaml():
    """Test that force_init: true in config sets FORCE_INIT."""
    script = (
        "CONFIG_FORCE_INIT=true\n"
        "FORCE_INIT=FALSE\n"
        "\n"
        'if [ "${CONFIG_FORCE_INIT:-false}" = "true" ]; then\n'
        '    FORCE_INIT="TRUE"\n'
        "fi\n"
        "\n"
        'echo "FORCE_INIT=$FORCE_INIT"\n'
    )
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Config force_init parsing failed: {result.stderr}"
    assert "FORCE_INIT=TRUE" in result.stdout, (
        "force_init: true should set FORCE_INIT=TRUE"
    )


# ---------------------------------------------------------------------------
# YAML config parsing tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_config_parsing_minimal(minimal_config):
    """Test that the embedded YAML parser produces correct bash variables for minimal config."""
    result = _parse_yaml_config(minimal_config)
    assert result.returncode == 0, f"Config parsing failed: {result.stderr}"
    assert "STEAMOS=false" in result.stdout
    assert "FORCE_INIT=false" in result.stdout
    assert "DECKY=false" in result.stdout
    assert "PACMAN_COUNT=0" in result.stdout
    assert "AUR_COUNT=0" in result.stdout
    assert "FLATPAK_COUNT=0" in result.stdout
    assert "NPM_COUNT=0" in result.stdout
    assert "SNAP_COUNT=0" in result.stdout
    assert "APT_COUNT=0" in result.stdout
    assert "DNF_COUNT=0" in result.stdout
    assert "BREW_COUNT=0" in result.stdout
    assert "NIX_COUNT=0" in result.stdout
    assert "CARGO_COUNT=0" in result.stdout
    assert "GO_COUNT=0" in result.stdout


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_config_parsing_with_packages():
    """Test YAML parsing with non-empty package lists and nested values."""
    config_content = (
        "steamos: true\n"
        "force_init: true\n"
        "pacman:\n"
        "  - vim\n"
        "  - git\n"
        "  - curl\n"
        "aur:\n"
        "  - visual-studio-code-bin\n"
        "flatpak:\n"
        "  - org.mozilla.firefox\n"
        "npm:\n"
        "  - typescript\n"
        "  - eslint\n"
        "snap:\n"
        "  - vscode\n"
        "apt:\n"
        "  - build-essential\n"
        "dnf:\n"
        "  - neovim\n"
        "brew:\n"
        "  - htop\n"
        "nix:\n"
        "  - ripgrep\n"
        "cargo:\n"
        "  - bat\n"
        "go:\n"
        "  - github.com/cli/cli/v2/cmd/gh\n"
        "git:\n"
        "  user.name: TestUser\n"
        "  user.email: test@example.com\n"
        "decky: false\n"
        "distrobox:\n"
        "  image: ubuntu:24.04\n"
        "  name: mybox\n"
    )
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, prefix="update-system-pkg-"
    )
    tmp.write(config_content)
    tmp.close()

    try:
        script = (
            "CONFIG_TMP_FILES=()\n"
            "load_config() {\n"
            '    local config_file="$1"\n'
            "    local tmp_config\n"
            '    tmp_config="$(mktemp)"\n'
            '    CONFIG_TMP_FILES+=("$tmp_config")\n'
            f'    python3 "{YAML_PARSER_SCRIPT}" "$config_file" > "$tmp_config"\n'
            '    source "$tmp_config"\n'
            "}\n"
            f'load_config "{tmp.name}"\n'
            'echo "STEAMOS=$CONFIG_STEAMOS"\n'
            'echo "FORCE_INIT=$CONFIG_FORCE_INIT"\n'
            'echo "PACMAN_COUNT=${#CONFIG_PACMAN[@]}"\n'
            'echo "AUR_COUNT=${#CONFIG_AUR[@]}"\n'
            'echo "FLATPAK_COUNT=${#CONFIG_FLATPAK[@]}"\n'
            'echo "NPM_COUNT=${#CONFIG_NPM[@]}"\n'
            'echo "SNAP_COUNT=${#CONFIG_SNAP[@]}"\n'
            'echo "APT_COUNT=${#CONFIG_APT[@]}"\n'
            'echo "DNF_COUNT=${#CONFIG_DNF[@]}"\n'
            'echo "BREW_COUNT=${#CONFIG_BREW[@]}"\n'
            'echo "NIX_COUNT=${#CONFIG_NIX[@]}"\n'
            'echo "CARGO_COUNT=${#CONFIG_CARGO[@]}"\n'
            'echo "GO_COUNT=${#CONFIG_GO[@]}"\n'
            'echo "PACMAN_0=${CONFIG_PACMAN[0]}"\n'
            'echo "PACMAN_1=${CONFIG_PACMAN[1]}"\n'
            'echo "PACMAN_2=${CONFIG_PACMAN[2]}"\n'
            'echo "AUR_0=${CONFIG_AUR[0]}"\n'
            'echo "FLATPAK_0=${CONFIG_FLATPAK[0]}"\n'
            'echo "NPM_0=${CONFIG_NPM[0]}"\n'
            'echo "NPM_1=${CONFIG_NPM[1]}"\n'
            'echo "SNAP_0=${CONFIG_SNAP[0]}"\n'
            'echo "APT_0=${CONFIG_APT[0]}"\n'
            'echo "DNF_0=${CONFIG_DNF[0]}"\n'
            'echo "BREW_0=${CONFIG_BREW[0]}"\n'
            'echo "NIX_0=${CONFIG_NIX[0]}"\n'
            'echo "CARGO_0=${CONFIG_CARGO[0]}"\n'
            'echo "GO_0=${CONFIG_GO[0]}"\n'
            'echo "GIT_USER_NAME=$CONFIG_GIT_USER_NAME"\n'
            'echo "GIT_USER_EMAIL=$CONFIG_GIT_USER_EMAIL"\n'
            'echo "DISTROBOX_IMAGE=$CONFIG_DISTROBOX_IMAGE"\n'
            'echo "DISTROBOX_NAME=$CONFIG_DISTROBOX_NAME"\n'
        )
        result = subprocess.run(
            ["/bin/bash", "-c", script],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Config parsing failed: {result.stderr}"
        assert "STEAMOS=true" in result.stdout
        assert "FORCE_INIT=true" in result.stdout
        assert "PACMAN_COUNT=3" in result.stdout
        assert "PACMAN_0=vim" in result.stdout
        assert "PACMAN_1=git" in result.stdout
        assert "PACMAN_2=curl" in result.stdout
        assert "AUR_COUNT=1" in result.stdout
        assert "AUR_0=visual-studio-code-bin" in result.stdout
        assert "FLATPAK_COUNT=1" in result.stdout
        assert "FLATPAK_0=org.mozilla.firefox" in result.stdout
        assert "NPM_COUNT=2" in result.stdout
        assert "NPM_0=typescript" in result.stdout
        assert "NPM_1=eslint" in result.stdout
        assert "SNAP_COUNT=1" in result.stdout
        assert "SNAP_0=vscode" in result.stdout
        assert "APT_COUNT=1" in result.stdout
        assert "APT_0=build-essential" in result.stdout
        assert "DNF_COUNT=1" in result.stdout
        assert "DNF_0=neovim" in result.stdout
        assert "BREW_COUNT=1" in result.stdout
        assert "BREW_0=htop" in result.stdout
        assert "NIX_COUNT=1" in result.stdout
        assert "NIX_0=ripgrep" in result.stdout
        assert "CARGO_COUNT=1" in result.stdout
        assert "CARGO_0=bat" in result.stdout
        assert "GO_COUNT=1" in result.stdout
        assert "GO_0=github.com/cli/cli/v2/cmd/gh" in result.stdout
        assert "GIT_USER_NAME=TestUser" in result.stdout
        assert "GIT_USER_EMAIL=test@example.com" in result.stdout
        assert "DISTROBOX_IMAGE=ubuntu:24.04" in result.stdout
        assert "DISTROBOX_NAME=mybox" in result.stdout
    finally:
        os.unlink(tmp.name)


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_config_parsing_booleans():
    """Test YAML boolean parsing (true/false variants)."""
    config_content = "steamos: true\nforce_init: false\ndecky: false\n"
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, prefix="update-system-bool-"
    )
    tmp.write(config_content)
    tmp.close()

    try:
        result = _parse_yaml_config(tmp.name)
        assert result.returncode == 0, f"Boolean parsing failed: {result.stderr}"
        assert "STEAMOS=true" in result.stdout
        assert "FORCE_INIT=false" in result.stdout
        assert "DECKY=false" in result.stdout
    finally:
        os.unlink(tmp.name)


# ---------------------------------------------------------------------------
# Utility function tests (sourced individually)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
@pytest.mark.parametrize(
    "func_name, expected_substrings",
    [
        ("run_flatpak", ["No flatpak", "skipping"]),
        ("run_pacman", ["No pacman", "skipping"]),
        ("aur_install", ["No AUR", "skipping"]),
        ("run_npm", ["No npm", "skipping"]),
        ("run_snap", ["No snap", "skipping"]),
        ("run_apt", ["No apt", "skipping"]),
        ("run_dnf", ["No dnf", "skipping"]),
        ("run_brew", ["No brew", "skipping"]),
        ("run_nix", ["No nix", "skipping"]),
        ("run_cargo", ["No cargo", "skipping"]),
        ("run_go", ["No go", "skipping"]),
    ],
)
def test_update_system_empty_run(
    func_name: str, expected_substrings: list[str]
) -> None:
    """Test that a run_* function skips gracefully with no arguments."""
    script = _source_function(func_name) + f"{func_name}\n"
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"{func_name} should succeed: {result.stderr}"
    assert any(
        s in result.stdout or s in result.stdout.lower() for s in expected_substrings
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_configure_git_empty():
    """Test that configure_git skips gracefully with no config."""
    script = (
        "unset CONFIG_GIT_USER_NAME CONFIG_GIT_USER_EMAIL\n"
        + _source_function("configure_git")
        + "configure_git\n"
    )
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"configure_git should succeed: {result.stderr}"
    assert "No git" in result.stdout or "skipping" in result.stdout.lower()


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_setup_distrobox_empty():
    """Test that setup_distrobox skips gracefully when not configured."""
    script = (
        "unset CONFIG_DISTROBOX_IMAGE CONFIG_DISTROBOX_NAME\n"
        + _source_function("setup_distrobox")
        + "setup_distrobox\n"
    )
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"setup_distrobox should succeed: {result.stderr}"
    assert "Distrobox" in result.stdout or "skipping" in result.stdout.lower()


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_run_snap_snapd_healthy():
    """Test run_snap when snapd is already responsive."""
    script = (
        # Mock check_command to succeed
        "check_command() { return 0; }\n"
        # Mock snap to succeed (snapd responsive)
        'snap() { [[ "$1" == "list" ]] && return 0; }\n'
        # Source the run_snap function
        + _source_function("run_snap")
        # Call with a test package
        + 'run_snap "test-pkg"\n'
    )
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"run_snap should succeed: {result.stderr}"
    assert "Installing snap packages" in result.stdout, (
        f"Should proceed with installation. Got: {result.stdout}"
    )
    assert "test-pkg" in result.stdout, (
        f"Should mention the package. Got: {result.stdout}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_run_snap_snapd_starts_successfully():
    """Test run_snap when snapd starts after being manually started."""
    script = (
        # Mock check_command to succeed
        "check_command() { return 0; }\n"
        # Mock snap: first call fails, second succeeds
        "SNAP_CALL_COUNT=0\n"
        "snap() {\n"
        "  SNAP_CALL_COUNT=$((SNAP_CALL_COUNT + 1))\n"
        '  if [[ "$SNAP_CALL_COUNT" -eq 1 ]]; then\n'
        "    return 1  # First call (health check) fails\n"
        "  fi\n"
        "  return 0  # Second call (retry) succeeds\n"
        "}\n"
        # Mock systemctl to succeed
        'systemctl() { [[ "$1" == "start" && "$2" == "snapd" ]] && return 0; }\n'
        # Mock sleep to be a no-op
        "sleep() { true; }\n"
        # Mock sudo to passthrough
        'sudo() { "$@"; }\n'
        # Source the run_snap function
        + _source_function("run_snap")
        # Call with a test package
        + 'run_snap "test-pkg"\n'
    )
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"run_snap should succeed: {result.stderr}"
    assert "snapd daemon not responding" in result.stdout, (
        f"Should detect snapd is down. Got: {result.stdout}"
    )
    assert "snapd daemon started successfully" in result.stdout, (
        f"Should report successful start. Got: {result.stdout}"
    )
    assert "test-pkg" in result.stdout, (
        f"Should install the package after starting snapd. Got: {result.stdout}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_run_snap_snapd_unrecoverable():
    """Test run_snap when snapd cannot be started."""
    script = (
        # Mock check_command to succeed
        "check_command() { return 0; }\n"
        # Mock snap to always fail
        "snap() { return 1; }\n"
        # Mock sleep to be a no-op
        "sleep() { true; }\n"
        # Source the run_snap function (no systemctl or service available)
        + _source_function("run_snap")
        # Call with a test package
        + 'run_snap "test-pkg"\n'
    )
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, f"run_snap should fail: {result.stdout}"
    assert "snapd daemon could not be started" in result.stdout, (
        f"Should report failure to start snapd. Got: {result.stdout}"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_check_command_missing():
    """Test that check_command returns 1 for missing commands."""
    script = (
        _source_function("check_command")
        + "check_command nonexistent_command_xyz123 npm\n"
    )
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, "check_command should return 1 for missing command"
    assert "not found" in result.stdout.lower() or "skipping" in result.stdout.lower()
