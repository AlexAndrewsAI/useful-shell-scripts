"""Minimal YAML-to-bash variable emitter.

Parses a subset of YAML (mappings, lists, scalars) and emits bash variable
assignments suitable for ``source``.  Used by ``update-system.sh`` and the
test suite.

Usage::

    python3 yaml_parser.py <config.yml>

The parser reads *config.yml* and prints lines like::

    CONFIG_FOO=bar
    CONFIG_LIST=()
    CONFIG_LIST+=(item)

Security note: values are quoted with :func:`shlex.quote` to prevent shell
metacharacter injection when the generated output is sourced.
"""

from __future__ import annotations

import shlex
import sys
from typing import Any


def parse_scalar(s: str) -> str | bool | None:
    """Convert a raw YAML scalar string into a Python value.

    Handles boolean keywords (true/false/yes/no variants), quoted strings,
    and plain strings.

    Args:
        s: The raw scalar text from the YAML source.

    Returns:
        A bool for boolean keywords, the inner text for quoted strings, or
        the stripped string as-is.
    """
    s = s.strip()
    if s in ("true", "True", "yes", "Yes"):
        return True
    if s in ("false", "False", "no", "No"):
        return False
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def parse_mapping(
    lines: list[str], index: int, indent: int
) -> tuple[dict[str, Any], int]:
    """Parse a YAML mapping starting at *index*.

    Args:
        lines: All lines from the YAML source.
        index: Current line index to start parsing from.
        indent: Expected indentation level (-1 for the document root).

    Returns:
        A tuple of (parsed dict, next line index).
    """
    obj: dict[str, Any] = {}
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
                        list_val, index = parse_list(lines, j, nindent)
                        obj[key] = list_val
                        continue
                    map_val, index = parse_mapping(lines, j, nindent)
                    obj[key] = map_val
                    continue
            obj[key] = None
            index = j
        else:
            obj[key] = parse_scalar(val)
            index += 1
    return obj, index


def parse_list(lines: list[str], index: int, indent: int) -> tuple[list[Any], int]:
    """Parse a YAML list starting at *index*.

    Args:
        lines: All lines from the YAML source.
        index: Current line index to start parsing from.
        indent: Expected indentation level of list items.

    Returns:
        A tuple of (parsed list, next line index).
    """
    lst: list[Any] = []
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


def emit(obj: dict[str, Any], prefix: str) -> list[str]:
    """Emit bash variable assignments from a parsed YAML dict.

    Values are quoted with :func:`shlex.quote` (for strings) to produce
    shell-safe output that can be ``source``d without risk of injection.

    Args:
        obj: The parsed YAML mapping.
        prefix: Variable-name prefix (e.g. ``"GIT_"`` for nested keys).

    Returns:
        A list of bash assignment lines.
    """
    out: list[str] = []
    for key, value in obj.items():
        var = "CONFIG_" + prefix + key.upper().replace("-", "_").replace(".", "_")
        if isinstance(value, bool):
            out.append(f"{var}={'true' if value else 'false'}")
        elif isinstance(value, list):
            out.append(f"{var}=()")
            for item in value:
                out.append(f"{var}+=({shlex.quote(str(item))})")
        elif isinstance(value, dict):
            # Special handling for appimage dictionary to emit alias:url pairs
            if key == "appimage":
                for alias, url in value.items():
                    # Convert alias to a valid bash variable name
                    # Replace slashes and other special chars with underscores
                    safe_alias = (
                        alias.replace("/", "_").replace("-", "_").replace(".", "_")
                    )
                    appimage_var = f"CONFIG_APPIMAGE_{safe_alias}"
                    out.append(f"{appimage_var}={shlex.quote(str(url))}")
                    # Also store the original alias for reconstruction
                    out.append(f"{appimage_var}_ALIAS={shlex.quote(str(alias))}")
            # Special handling for shell-exe dictionary to emit name:command pairs
            elif key == "shell-exe":
                for name, command in value.items():
                    # Convert name to a valid bash variable name
                    safe_name = (
                        name.replace("/", "_").replace("-", "_").replace(".", "_")
                    )
                    shell_exe_var = f"CONFIG_SHELL_EXE_{safe_name}"
                    out.append(f"{shell_exe_var}={shlex.quote(str(command))}")
                    # Also store the original name for reconstruction
                    out.append(f"{shell_exe_var}_ALIAS={shlex.quote(str(name))}")
            else:
                out.extend(
                    emit(
                        value,
                        prefix + key.upper().replace("-", "_").replace(".", "_") + "_",
                    )
                )
        elif value is None:
            out.append(f"{var}=")
        else:
            out.append(f"{var}={shlex.quote(str(value))}")
    return out


def parse_and_emit(path: str) -> list[str]:
    """Parse a YAML file and return bash variable assignment lines.

    Args:
        path: Filesystem path to the YAML config file.

    Returns:
        A list of bash assignment lines ready for ``source``.
    """
    with open(path) as fh:
        text = fh.read()
    root, _ = parse_mapping(text.splitlines(), 0, -1)
    return emit(root, "")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <config.yml>", file=sys.stderr)
        sys.exit(1)
    for line in parse_and_emit(sys.argv[1]):
        print(line)
