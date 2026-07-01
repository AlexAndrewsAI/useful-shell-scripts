"""Tests for shell script linting using pureshellcheck."""

from pathlib import Path

import pureshellcheck  # type: ignore
import pytest

SHELL_FILES = [
    "setup.sh",
    "bash/bashrc-dev.sh",
    "bash/bashrc-extra.sh",
    "bash/bashrc-files.sh",
    "bash/bashrc-processes.sh",
    "bash/git-copy-bare.sh",
    "bash/git2linksremote.sh",
    "bash/git2markdown.sh",
    "bash/ports-in-use.sh",
    "bash/psfind.sh",
]


@pytest.mark.parametrize("shell_file", SHELL_FILES)
def test_shellcheck(shell_file):
    """Test shell script for common issues using pureshellcheck.

    This test ensures shell scripts have no errors. Warnings and style
    issues are printed for visibility but do not cause test failure.
    """
    path = Path(shell_file)
    if not path.exists():
        pytest.skip(f"{shell_file} not found")

    with open(path) as f:
        content = f.read()

    findings = pureshellcheck.check(content, shell="bash")

    # Print findings for visibility
    if findings:
        print(f"\n{shell_file}:")
        for finding in findings:
            print(
                f"  Line {finding.line}: [{finding.severity}] {finding.code} - {finding.message}"
            )

    # Filter to only errors (not warnings/info/style)
    errors = [f for f in findings if f.severity == "error"]
    assert len(errors) == 0, f"{shell_file} has {len(errors)} errors"
