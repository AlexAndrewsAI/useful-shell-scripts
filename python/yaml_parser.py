"""Minimal YAML-to-bash variable emitter.

Parses a subset of YAML (mappings, lists, scalars) and emits bash variable
assignments suitable for ``source``.  Used by ``update-system.sh`` and the
test suite.

Usage::

    python3 yaml_parser.py <config.yaml>

The parser reads *config.yaml* and prints lines like::

    CONFIG_FOO=bar
    CONFIG_LIST=()
    CONFIG_LIST+=(item)

Security note: values are quoted with :func:`shlex.quote` to prevent shell
metacharacter injection when the generated output is sourced.
"""

from __future__ import annotations

import logging
import shlex
import sys
from typing import Any

log = logging.getLogger(__name__)


def parse_scalar(s: str) -> str | bool | None:
    """Convert a raw YAML scalar string into a Python value.

    Handles quoted strings (single and double), boolean keywords
    (true/false/yes/no variants), and plain strings.  Quoted strings are
    checked *before* booleans so that ``\"true\"`` produces the string
    ``\"true\"``, not a Python ``True``.

    Args:
        s: The raw scalar text from the YAML source.

    Returns:
        The inner text for quoted strings, a bool for boolean keywords, or
        the stripped string as-is.
    """
    s = s.strip()
    # Quoted strings take precedence over booleans so that e.g. ``"true"``
    # is treated as the literal string ``true``, not a boolean.
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    if s in ("true", "True", "yes", "Yes"):
        return True
    if s in ("false", "False", "no", "No"):
        return False
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
            log.warning(
                "Line %d: indent %d exceeds mapping level %d, skipping",
                index + 1,
                cur,
                indent,
            )
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


def _parse_inline_list(s: str) -> list[Any]:
    """Parse an inline YAML list (``[a, b, c]`` syntax).

    Args:
        s: The raw text *including* surrounding brackets, e.g. ``[a, b, c]``.

    Returns:
        A list of parsed values.
    """
    s = s.strip()
    if s in ("[]", "[ ]"):
        return []
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(item.strip()) for item in inner.split(",") if item.strip()]
    return [parse_scalar(s)]


def _parse_list_item_scalar_or_block(
    item_raw: str,
    next_lines: list[str],
    next_start: int,
    cur_indent: int,
) -> tuple[Any, int]:
    """Parse a single ``- `` item that may be a scalar, inline list, mapping,
    or nested sub-block.

    Args:
        item_raw: Text after the ``- `` marker.
        next_lines: Full line list (for look-ahead).
        next_start: Index of the line immediately after the ``- `` line.
        cur_indent: Indentation of the ``- `` line itself.

    Returns:
        A tuple of (parsed value, new line index).
    """
    # --- 1. Inline bracket list ---
    if item_raw.startswith("["):
        return _parse_inline_list(item_raw), next_start

    stripped = item_raw.strip()

    # --- 2. Empty or key-only (ends with ':') — may have a sub-block ---
    is_key_only = (not stripped) or stripped.endswith(":")

    if is_key_only:
        key = stripped.rstrip(":").strip() if stripped else ""
        # Scan forward past blank / comment lines
        j = next_start
        while j < len(next_lines) and (
            not next_lines[j].strip() or next_lines[j].strip().startswith("#")
        ):
            j += 1
        if j < len(next_lines):
            nindent = len(next_lines[j]) - len(next_lines[j].lstrip(" "))
            ncontent = next_lines[j].strip()
            if nindent > cur_indent:
                # Found a sub-block — recurse
                sub_val: Any
                if ncontent.startswith("- ") or ncontent.startswith("-"):
                    sub_val, new_index = parse_list(next_lines, j, nindent)
                else:
                    sub_val, new_index = parse_mapping(next_lines, j, nindent)
                if key:
                    return {key: sub_val}, new_index
                return sub_val, new_index
        # No sub-block found — treat as plain scalar
        return parse_scalar(item_raw), next_start

    # --- 3. Inline key-value (``key: val``) ---
    if ":" in stripped and not stripped.startswith(":"):
        k, _, v = stripped.partition(":")
        k = k.strip()
        v = v.strip()
        if v:
            return {k: parse_scalar(v)}, next_start

    # --- 4. Nested list marker (``- sub1``) ---
    if stripped.startswith("-"):
        # The item itself is a sub-list.  Build synthetic lines:
        #   item_raw         → first line of inner list
        #   next_lines[...]  → continuation lines that belong to this item
        #
        # ``item_raw`` is the text after the outer ``- `` (2 chars), so the
        # inner list marker sits at ``cur_indent + 2 + sub_marker_indent``
        # in the original file.
        sub_marker_indent = len(item_raw) - len(item_raw.lstrip(" "))
        base_indent = cur_indent + 2 + sub_marker_indent

        # First line of inner list (normalised indentation)
        synthetic = [item_raw[sub_marker_indent:]]

        # Collect continuation lines that are more indented than cur_indent
        j = next_start
        while j < len(next_lines):
            nline = next_lines[j]
            nstripped = nline.strip()
            if not nstripped or nstripped.startswith("#"):
                # Preserve blank/comment lines at the correct relative indent
                rel = max(0, len(nline) - len(nline.lstrip(" ")) - base_indent)
                synthetic.append(" " * rel + nstripped)
                j += 1
                continue
            nindent = len(nline) - len(nline.lstrip(" "))
            if nindent > cur_indent:
                # Normalise indentation relative to base_indent
                rel = nindent - base_indent
                synthetic.append(" " * max(0, rel) + nstripped)
                j += 1
            else:
                break

        sub_val, _ = parse_list(synthetic, 0, 0)
        return sub_val, j

    # --- 5. Plain scalar ---
    return parse_scalar(item_raw), next_start


def parse_list(lines: list[str], index: int, indent: int) -> tuple[list[Any], int]:
    """Parse a YAML list starting at *index*.

    Supports:
    * Flat scalars (``- foo``)
    * Inline bracket lists (``- [a, b]``)
    * Nested mappings (``- key: value``, ``- key:`` with indented children)
    * Nested sub-lists (``- - sub``, ``-:\n  - sub``)

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
            item_raw = content[2:]
            val, new_index = _parse_list_item_scalar_or_block(
                item_raw, lines, index + 1, cur
            )
            lst.append(val)
            index = new_index
        elif content.startswith("-["):
            # ``-[a,b]`` — no space after hyphen
            lst.append(_parse_inline_list(content[1:]))
            index += 1
        elif content == "-":
            # Bare ``-`` (empty item), may have a sub-block
            val, new_index = _parse_list_item_scalar_or_block("", lines, index + 1, cur)
            lst.append(val)
            index = new_index
        elif content.startswith("-"):
            # ``-something`` — treat as scalar starting after hyphen
            lst.append(parse_scalar(content[1:]))
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
        print(f"Usage: {sys.argv[0]} <config.yaml>", file=sys.stderr)
        sys.exit(1)
    for line in parse_and_emit(sys.argv[1]):
        print(line)
