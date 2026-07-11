#!/usr/bin/env python3
"""Test suite for update-system.sh script."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from tests.test_utils import check_bash_present

SCRIPT_DIR = Path(__file__).parent.parent / "bash"
UPDATE_SYSTEM = SCRIPT_DIR / "update-system.sh"

# The embedded Python YAML parser extracted from update-system.sh so we can
# test config parsing without sourcing the whole script (which runs sudo etc.).
YAML_PARSER = r"""
import sys

def parse_scalar(s):
    s = s.strip()
    if s in ("true", "True", "yes", "Yes"):
        return True
    if s in ("false", "False", "no", "No"):
        return False
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s

def parse_mapping(lines, index, indent):
    obj = {}
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.strip().startswith("#"):
            index += 1
            continue
        cur = len(line) - len(line.lstrip(" "))
        if cur < indent:
            break
        if indent >= 0 and cur > indent:
            index += 1
            continue
        content = line.strip()
        key, _, val = content.partition(":")
        key = key.strip()
        val = val.strip()
        if val in ("[]", "[ ]"):
            obj[key] = []
            index += 1
        elif val == "":
            j = index + 1
            while j < len(lines) and (
                not lines[j].strip() or lines[j].strip().startswith("#")
            ):
                j += 1
            if j < len(lines):
                nindent = len(lines[j]) - len(lines[j].lstrip(" "))
                ncontent = lines[j].strip()
                if nindent > cur:
                    if ncontent.startswith("- "):
                        child, index = parse_list(lines, j, nindent)
                        obj[key] = child
                        continue
                    child, index = parse_mapping(lines, j, nindent)
                    obj[key] = child
                    continue
            obj[key] = None
            index = j
        else:
            obj[key] = parse_scalar(val)
            index += 1
    return obj, index

def parse_list(lines, index, indent):
    lst = []
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.strip().startswith("#"):
            index += 1
            continue
        cur = len(line) - len(line.lstrip(" "))
        if cur < indent:
            break
        if cur > indent:
            index += 1
            continue
        content = line.strip()
        if content.startswith("- "):
            lst.append(parse_scalar(content[2:]))
            index += 1
        else:
            break
    return lst, index

def emit(obj, prefix):
    out = []
    for key, value in obj.items():
        var = "CONFIG_" + prefix + key.upper().replace("-", "_").replace(".", "_")
        if isinstance(value, bool):
            out.append(f'{var}={"true" if value else "false"}')
        elif isinstance(value, list):
            out.append(f'{var}=()')
            for item in value:
                out.append(f'{var}+=({item!r})')
        elif isinstance(value, dict):
            out.extend(emit(value, prefix + key.upper().replace("-", "_").replace(".", "_") + "_"))
        elif value is None:
            out.append(f'{var}=')
        else:
            out.append(f'{var}={value!r}')
    return out

path = sys.argv[1]
with open(path) as fh:
    text = fh.read()

root, _ = parse_mapping(text.splitlines(), 0, -1)
for line in emit(root, ""):
    print(line)
"""


def _parse_yaml_config(config_path: str) -> subprocess.CompletedProcess[str]:
    """Run the embedded YAML parser and return a dict of CONFIG_ vars."""
    script = (
        "CONFIG_TMP_FILES=()\n"
        "load_config() {\n"
        '    local config_file="$1"\n'
        "    local tmp_config\n"
        '    tmp_config="$(mktemp)"\n'
        '    CONFIG_TMP_FILES+=("$tmp_config")\n'
        '    python3 - "$config_file" <<\'PYEOF\' > "$tmp_config"\n'
        + YAML_PARSER
        + "\nPYEOF\n"
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
        'echo "SHORTCUTS_COUNT=${#CONFIG_SHORTCUTS[@]}"\n'
    )
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    return result


def _source_function(func_name: str) -> str:
    """Build a bash script that sources a single function from update-system.sh."""
    return f"source <(sed -n '/^{func_name}()/,/^}}/p' \"{UPDATE_SYSTEM}\")\n"


@pytest.fixture
def update_system_script_path():
    """Path to the update-system.sh script."""
    return UPDATE_SYSTEM


@pytest.fixture
def example_config_path():
    """Path to the example YAML config file."""
    return SCRIPT_DIR / "update-system.example.yml"


@pytest.fixture
def minimal_config():
    """Create a minimal YAML config that disables all optional features."""
    config_content = (
        "steamos: false\n"
        "force_init: false\n"
        "pacman: []\n"
        "aur: []\n"
        "flatpak: []\n"
        "git: []\n"
        "decky: false\n"
        "distrobox: []\n"
        "shortcuts: []\n"
    )
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, prefix="update-system-test-"
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
    """Test that missing config file causes an error."""
    result = subprocess.run(
        [
            "/bin/bash",
            str(update_system_script_path),
            "-c",
            "/nonexistent/path/config.yml",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, "Missing config should cause non-zero exit"
    assert "not found" in result.stdout.lower() or "error" in result.stdout.lower(), (
        "Should print error about missing config"
    )


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
    assert "SHORTCUTS_COUNT=0" in result.stdout


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
        "git:\n"
        "  user.name: TestUser\n"
        "  user.email: test@example.com\n"
        "decky: false\n"
        "distrobox:\n"
        "  image: ubuntu:24.04\n"
        "  name: mybox\n"
        "shortcuts:\n"
        "  - firefox\n"
    )
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, prefix="update-system-pkg-"
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
            '    python3 - "$config_file" <<\'PYEOF\' > "$tmp_config"\n'
            + YAML_PARSER
            + "\nPYEOF\n"
            '    source "$tmp_config"\n'
            "}\n"
            f'load_config "{tmp.name}"\n'
            'echo "STEAMOS=$CONFIG_STEAMOS"\n'
            'echo "FORCE_INIT=$CONFIG_FORCE_INIT"\n'
            'echo "PACMAN_COUNT=${#CONFIG_PACMAN[@]}"\n'
            'echo "AUR_COUNT=${#CONFIG_AUR[@]}"\n'
            'echo "FLATPAK_COUNT=${#CONFIG_FLATPAK[@]}"\n'
            'echo "PACMAN_0=${CONFIG_PACMAN[0]}"\n'
            'echo "PACMAN_1=${CONFIG_PACMAN[1]}"\n'
            'echo "PACMAN_2=${CONFIG_PACMAN[2]}"\n'
            'echo "AUR_0=${CONFIG_AUR[0]}"\n'
            'echo "FLATPAK_0=${CONFIG_FLATPAK[0]}"\n'
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
        mode="w", suffix=".yml", delete=False, prefix="update-system-bool-"
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
def test_update_system_run_flatpak_empty():
    """Test that run_flatpak skips gracefully with no arguments."""
    script = _source_function("run_flatpak") + "run_flatpak\n"
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"run_flatpak should succeed: {result.stderr}"
    assert "No flatpak" in result.stdout or "skipping" in result.stdout.lower()


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_run_pacman_empty():
    """Test that run_pacman skips gracefully with no arguments."""
    script = _source_function("run_pacman") + "run_pacman\n"
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"run_pacman should succeed: {result.stderr}"
    assert "No pacman" in result.stdout or "skipping" in result.stdout.lower()


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_update_system_aur_install_empty():
    """Test that aur_install skips gracefully with no arguments."""
    script = _source_function("aur_install") + "aur_install\n"
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"aur_install should succeed: {result.stderr}"
    assert "No AUR" in result.stdout or "skipping" in result.stdout.lower()


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
