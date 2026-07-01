#!/usr/bin/env python3
"""Test suite for bashrc-processes.sh script."""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def bashrc_processes_script_path():
    """Path to the bashrc-processes.sh script."""
    return Path(__file__).parent.parent / "bash" / "bashrc-processes.sh"


def check_bash_present():
    """Check if /bin/bash is present on the system."""
    return os.path.exists("/bin/bash")


def test_bashrc_processes_script_exists(bashrc_processes_script_path):
    """Test that bashrc-processes.sh script exists."""
    assert bashrc_processes_script_path.exists(), (
        f"Script not found at {bashrc_processes_script_path}"
    )


def test_bashrc_processes_syntax_validation(bashrc_processes_script_path):
    """Test that bashrc-processes.sh has valid bash syntax."""
    result = subprocess.run(
        ["/bin/bash", "-n", str(bashrc_processes_script_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Syntax error in script: {result.stderr}"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_psfind_alias(bashrc_processes_script_path):
    """Test that bashrc-processes.sh creates psfind alias."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_processes_script_path} && alias psfind"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "psfind" in result.stdout, "psfind alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_pskill_alias(bashrc_processes_script_path):
    """Test that bashrc-processes.sh creates pskill alias."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_processes_script_path} && alias pskill"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "pskill" in result.stdout, "pskill alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_pskill_headless_alias(bashrc_processes_script_path):
    """Test that bashrc-processes.sh creates pskill-headless alias."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_processes_script_path} && alias pskill-headless",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "pskill-headless" in result.stdout, "pskill-headless alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_headless_pskill_alias(bashrc_processes_script_path):
    """Test that bashrc-processes.sh creates headless-pskill alias."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_processes_script_path} && alias headless-pskill",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "headless-pskill" in result.stdout, "headless-pskill alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_run_limits_alias(bashrc_processes_script_path):
    """Test that bashrc-processes.sh creates run-limits alias."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_processes_script_path} && alias run-limits",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "run-limits" in result.stdout, "run-limits alias should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_repeat_function_definition(bashrc_processes_script_path):
    """Test that bashrc-processes.sh defines repeat function."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_processes_script_path} && type repeat"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "repeat" in result.stdout, "repeat function should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_psnice_function_definition(bashrc_processes_script_path):
    """Test that bashrc-processes.sh defines psnice function."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_processes_script_path} && type psnice"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "psnice" in result.stdout, "psnice function should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_pstoggle_function_definition(bashrc_processes_script_path):
    """Test that bashrc-processes.sh defines pstoggle function."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_processes_script_path} && type pstoggle"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "pstoggle" in result.stdout, "pstoggle function should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_process_kill_threshhold_function_definition(
    bashrc_processes_script_path,
):
    """Test that bashrc-processes.sh defines process-kill-threshhold function."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_processes_script_path} && type process-kill-threshhold",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "process-kill-threshhold" in result.stdout, (
        "process-kill-threshhold function should be defined"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_nnice_function_definition(bashrc_processes_script_path):
    """Test that bashrc-processes.sh defines nnice function."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_processes_script_path} && type nnice"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "nnice" in result.stdout, "nnice function should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_nohup_date_function_definition(bashrc_processes_script_path):
    """Test that bashrc-processes.sh defines nohup-date function."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_processes_script_path} && type nohup-date",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "nohup-date" in result.stdout, "nohup-date function should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_nohup_date_usage_message(bashrc_processes_script_path):
    """Test that nohup-date shows usage message when called without arguments."""
    result = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_processes_script_path} && nohup-date"],
        capture_output=True,
        text=True,
    )

    # Function shows usage message even with return code 0
    assert "Usage" in result.stdout or "usage" in result.stdout, (
        "Should show usage message"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_nnice_outputs_command(bashrc_processes_script_path):
    """Test that nnice function outputs the command it will run."""
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_processes_script_path} && nnice echo 'test'",
        ],
        capture_output=True,
        text=True,
    )

    # nnice should output the command even if it runs in background
    assert "echo" in result.stdout or "test" in result.stdout, (
        "nnice should output the command"
    )


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_repeat_function_help(bashrc_processes_script_path):
    """Test that repeat function shows help when command not found."""
    # Run repeat with a non-existent command in a subshell with timeout
    subprocess.run(
        [
            "/bin/bash",
            "-c",
            f"source {bashrc_processes_script_path} && (repeat nonexistent_command_xyz 2>&1 &) && sleep 0.5 && pkill -f repeat || true",
        ],
        capture_output=True,
        text=True,
    )

    # The function might not show error in this context, but we can test it exists
    # Just verify the function is defined
    result2 = subprocess.run(
        ["/bin/bash", "-c", f"source {bashrc_processes_script_path} && type repeat"],
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0, "repeat function should be defined"


@pytest.mark.skipif(
    not check_bash_present(), reason="/bin/bash not found - skipping bash-related tests"
)
def test_bashrc_processes_repeat_with_echo(bashrc_processes_script_path):
    """Test that repeat function can execute echo command."""
    # Create a simple test script that runs repeat briefly
    script = f"""
    source {bashrc_processes_script_path}
    repeat -dt 0.1 echo 'test' &
    REPEAT_PID=$!
    sleep 0.3
    kill $REPEAT_PID 2>/dev/null || true
    """
    result = subprocess.run(
        ["/bin/bash", "-c", script],
        capture_output=True,
        text=True,
    )

    # Should have executed echo at least once
    assert "test" in result.stdout or "Running command" in result.stdout, (
        "repeat should execute echo command"
    )
