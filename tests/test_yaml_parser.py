"""Tests for the shared YAML-to-bash parser in python/yaml_parser.py."""

from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from python.yaml_parser import (
    _parse_inline_list,
    emit,
    parse_and_emit,
    parse_list,
    parse_mapping,
    parse_scalar,
)

PARSER = Path(__file__).parent.parent / "python" / "yaml_parser.py"


# ---------------------------------------------------------------------------
# parse_scalar
# ---------------------------------------------------------------------------


class TestParseScalar:
    """Tests for parse_scalar()."""

    def test_true_variants(self) -> None:
        for val in ("true", "True", "yes", "Yes"):
            assert parse_scalar(val) is True

    def test_false_variants(self) -> None:
        for val in ("false", "False", "no", "No"):
            assert parse_scalar(val) is False

    def test_single_quoted_string(self) -> None:
        assert parse_scalar("'hello'") == "hello"

    def test_double_quoted_string(self) -> None:
        assert parse_scalar('"hello"') == "hello"

    def test_plain_string(self) -> None:
        assert parse_scalar("vim") == "vim"

    def test_strips_whitespace(self) -> None:
        assert parse_scalar("  true  ") is True
        assert parse_scalar("  hello  ") == "hello"

    def test_empty_string(self) -> None:
        assert parse_scalar("") == ""

    def test_single_char_not_stripped(self) -> None:
        assert parse_scalar("x") == "x"

    def test_double_quoted_true_is_string(self) -> None:
        assert parse_scalar('"true"') == "true"
        assert isinstance(parse_scalar('"true"'), str)

    def test_double_quoted_false_is_string(self) -> None:
        assert parse_scalar('"false"') == "false"
        assert isinstance(parse_scalar('"false"'), str)

    def test_single_quoted_boolean_is_string(self) -> None:
        assert parse_scalar("'true'") == "true"
        assert isinstance(parse_scalar("'true'"), str)

    def test_yes_no_quoted_strings(self) -> None:
        assert parse_scalar('"yes"') == "yes"
        assert parse_scalar("'no'") == "no"


# ---------------------------------------------------------------------------
# parse_mapping
# ---------------------------------------------------------------------------


class TestParseMapping:
    """Tests for parse_mapping()."""

    def test_flat_mapping(self) -> None:
        lines = ["name: Alice", "age: 30"]
        obj, idx = parse_mapping(lines, 0, -1)
        assert obj == {"name": "Alice", "age": "30"}
        assert idx == 2

    def test_boolean_values(self) -> None:
        lines = ["enabled: true", "debug: false"]
        obj, _ = parse_mapping(lines, 0, -1)
        assert obj["enabled"] is True
        assert obj["debug"] is False

    def test_empty_list_inline(self) -> None:
        lines = ["packages: []"]
        obj, _ = parse_mapping(lines, 0, -1)
        assert obj["packages"] == []

    def test_empty_list_bracket_space(self) -> None:
        lines = ["packages: [ ]"]
        obj, _ = parse_mapping(lines, 0, -1)
        assert obj["packages"] == []

    def test_none_value(self) -> None:
        lines = ["notes:"]
        obj, _ = parse_mapping(lines, 0, -1)
        assert obj["notes"] is None

    def test_nested_mapping(self) -> None:
        lines = ["git:", "  user.name: TestUser", "  user.email: test@x.com"]
        obj, _ = parse_mapping(lines, 0, -1)
        assert obj["git"]["user.name"] == "TestUser"
        assert obj["git"]["user.email"] == "test@x.com"

    def test_nested_list(self) -> None:
        lines = ["pacman:", "  - vim", "  - git"]
        obj, _ = parse_mapping(lines, 0, -1)
        assert obj["pacman"] == ["vim", "git"]

    def test_comments_and_blank_lines(self) -> None:
        lines = ["# comment", "", "key: val", "", "# another"]
        obj, idx = parse_mapping(lines, 0, -1)
        assert obj == {"key": "val"}
        assert idx == 5

    def test_indented_block_treated_as_child(self) -> None:
        lines = ["key: val", "  nested: skip"]
        obj, _idx = parse_mapping(lines, 0, -1)
        assert obj == {"key": "val", "nested": "skip"}

    def test_lesser_indent_breaks(self) -> None:
        lines = ["  a: 1", "b: 2"]
        obj, idx = parse_mapping(lines, 0, 2)
        assert obj == {"a": "1"}
        assert idx == 1

    def test_deeper_indent_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        lines = ["a: 1", "  deeper: skipped", "b: 2"]
        obj, idx = parse_mapping(lines, 0, 0)
        assert obj == {"a": "1", "b": "2"}
        assert idx == 3
        assert "exceeds mapping level" in caplog.text


# ---------------------------------------------------------------------------
# parse_list
# ---------------------------------------------------------------------------


class TestParseList:
    """Tests for parse_list()."""

    def test_simple_list(self) -> None:
        lines = ["- alpha", "- beta"]
        lst, idx = parse_list(lines, 0, 0)
        assert lst == ["alpha", "beta"]
        assert idx == 2

    def test_list_with_comments(self) -> None:
        lines = ["- alpha", "# comment", "- beta"]
        lst, _ = parse_list(lines, 0, 0)
        assert lst == ["alpha", "beta"]

    def test_indented_list(self) -> None:
        lines = ["  - one", "  - two"]
        lst, idx = parse_list(lines, 0, 2)
        assert lst == ["one", "two"]
        assert idx == 2

    def test_higher_indent_skipped(self) -> None:
        lines = ["- a", "    deep: val"]
        lst, idx = parse_list(lines, 0, 0)
        assert lst == ["a"]
        assert idx == 2

    def test_empty_list(self) -> None:
        lst, idx = parse_list([], 0, 0)
        assert lst == []
        assert idx == 0


class TestParseInlineList:
    """Tests for _parse_inline_list()."""

    def test_empty_brackets(self) -> None:
        assert _parse_inline_list("[]") == []

    def test_empty_brackets_with_space(self) -> None:
        assert _parse_inline_list("[ ]") == []

    def test_single_item(self) -> None:
        assert _parse_inline_list("[a]") == ["a"]

    def test_multiple_items(self) -> None:
        assert _parse_inline_list("[a, b, c]") == ["a", "b", "c"]

    def test_boolean_items(self) -> None:
        assert _parse_inline_list("[true, false]") == [True, False]

    def test_mixed_items(self) -> None:
        assert _parse_inline_list("[foo, 42, true]") == ["foo", "42", True]

    def test_whitespace_handling(self) -> None:
        assert _parse_inline_list("  [ a , b ]  ") == ["a", "b"]


class TestParseListEnhanced:
    """Tests for the enhanced parse_list() features (nested & inline)."""

    def test_inline_bracket_list_item(self) -> None:
        """- [a, b, c] should produce a nested list."""
        lines = ["- [a, b, c]"]
        lst, idx = parse_list(lines, 0, 0)
        assert lst == [["a", "b", "c"]]
        assert idx == 1

    def test_inline_bracket_no_space(self) -> None:
        """-[a, b] (no space after hyphen) should also work."""
        lines = ["-[a, b]"]
        lst, idx = parse_list(lines, 0, 0)
        assert lst == [["a", "b"]]
        assert idx == 1

    def test_single_item_inline_bracket(self) -> None:
        lines = ["- [single]"]
        lst, _ = parse_list(lines, 0, 0)
        assert lst == [["single"]]

    def test_nested_list_in_list_item(self) -> None:
        """- - sub should treat the second - as a nested list."""
        lines = ["- - sub1", "  - sub2"]
        lst, idx = parse_list(lines, 0, 0)
        assert lst == [["sub1", "sub2"]]
        assert idx == 2

    def test_nested_mapping_in_list_item(self) -> None:
        """- key: value should produce a dict inside the list."""
        lines = ["- key1: val1", "- key2: val2"]
        lst, idx = parse_list(lines, 0, 0)
        assert lst == [{"key1": "val1"}, {"key2": "val2"}]
        assert idx == 2

    def test_nested_mapping_with_subblock(self) -> None:
        """- apt: with indented children produces {apt: [pkg1, pkg2]}."""
        lines = ["- apt:", "    - pkg1", "    - pkg2"]
        lst, idx = parse_list(lines, 0, 0)
        assert lst == [{"apt": ["pkg1", "pkg2"]}]
        assert idx == 3

    def test_empty_list_item_with_subblock(self) -> None:
        """- (empty) with children below produces just the child value."""
        lines = ["-", "  - sub1", "  - sub2"]
        lst, idx = parse_list(lines, 0, 0)
        assert lst == [["sub1", "sub2"]]
        assert idx == 3

    def test_mixed_items_in_list(self) -> None:
        """Mix of scalars, nested lists, and nested mappings."""
        lines = [
            "- plain",
            "- [a, b]",
            "- nested_key: nested_val",
        ]
        lst, idx = parse_list(lines, 0, 0)
        assert lst == ["plain", ["a", "b"], {"nested_key": "nested_val"}]
        assert idx == 3


# ---------------------------------------------------------------------------
# emit
# ---------------------------------------------------------------------------


class TestEmit:
    """Tests for emit()."""

    def test_boolean_emit(self) -> None:
        out = emit({"flag": True}, "")
        assert out == ["CONFIG_FLAG=true"]

    def test_false_emit(self) -> None:
        out = emit({"flag": False}, "")
        assert out == ["CONFIG_FLAG=false"]

    def test_string_emit(self) -> None:
        out = emit({"name": "alice"}, "")
        assert out == ["CONFIG_NAME=alice"]

    def test_none_emit(self) -> None:
        out = emit({"notes": None}, "")
        assert out == ["CONFIG_NOTES="]

    def test_empty_list_emit(self) -> None:
        out = emit({"pkgs": []}, "")
        assert out == ["CONFIG_PKGS=()"]

    def test_list_emit(self) -> None:
        out = emit({"pkgs": ["vim", "git"]}, "")
        assert "CONFIG_PKGS=()" in out
        assert "CONFIG_PKGS+=(vim)" in out
        assert "CONFIG_PKGS+=(git)" in out

    def test_nested_dict_emit(self) -> None:
        out = emit({"git": {"user.name": "Alice"}}, "")
        assert "CONFIG_GIT_USER_NAME=Alice" in out

    def test_prefix_concatenation(self) -> None:
        out = emit({"name": "val"}, "GIT_")
        assert "CONFIG_GIT_NAME=val" in out

    def test_hyphens_to_underscores(self) -> None:
        out = emit({"my-key": "val"}, "")
        assert "CONFIG_MY_KEY=val" in out

    def test_dots_to_underscores(self) -> None:
        out = emit({"my.key": "val"}, "")
        assert "CONFIG_MY_KEY=val" in out

    def test_shell_metacharacter_quoting(self) -> None:
        evil = "foo'; rm -rf /; echo '"
        out = emit({"name": evil}, "")
        assert len(out) == 1
        assert out[0] == f"CONFIG_NAME={shlex.quote(evil)}"

    def test_appimage_emit(self) -> None:
        out = emit(
            {"appimage": {"firefox": "https://example.com/firefox.AppImage"}}, ""
        )
        assert "CONFIG_APPIMAGE_firefox=https://example.com/firefox.AppImage" in out
        assert "CONFIG_APPIMAGE_firefox_ALIAS=firefox" in out

    def test_appimage_emit_special_chars(self) -> None:
        out = emit(
            {"appimage": {"firefox": "https://example.com/fire fox.AppImage"}}, ""
        )
        assert any(
            "CONFIG_APPIMAGE_firefox=" in line and "fire fox" in line for line in out
        )
        assert "CONFIG_APPIMAGE_firefox_ALIAS=firefox" in out

    def test_shell_exe_emit(self) -> None:
        out = emit({"shell-exe": {"firefox": "flatpak run org.mozilla.firefox $@"}}, "")
        assert "CONFIG_SHELL_EXE_firefox=" in out[0]
        assert "flatpak run org.mozilla.firefox $@" in out[0]
        assert "CONFIG_SHELL_EXE_firefox_ALIAS=firefox" in out

    def test_shell_exe_emit_path_name(self) -> None:
        out = emit(
            {"shell-exe": {"/usr/local/bin/myapp": "flatpak run org.something.app"}},
            "",
        )
        # Path separators become underscores in variable names
        assert "CONFIG_SHELL_EXE__usr_local_bin_myapp=" in out[0]
        assert "CONFIG_SHELL_EXE__usr_local_bin_myapp_ALIAS=/usr/local/bin/myapp" in out


# ---------------------------------------------------------------------------
# parse_and_emit  (integration)
# ---------------------------------------------------------------------------


class TestParseAndEmit:
    """Integration tests for parse_and_emit() via a temp file."""

    def test_minimal_config(self, tmp_path: Path) -> None:
        cfg = tmp_path / "test.yaml"
        cfg.write_text("steamos: false\nforce_init: true\n")
        out = parse_and_emit(str(cfg))
        assert "CONFIG_STEAMOS=false" in out
        assert "CONFIG_FORCE_INIT=true" in out

    def test_packages_and_nested(self, tmp_path: Path) -> None:
        cfg = tmp_path / "test.yaml"
        cfg.write_text("pacman:\n  - vim\n  - git\ngit:\n  user.name: TestUser\n")
        out = parse_and_emit(str(cfg))
        assert "CONFIG_PACMAN=()" in out
        assert "CONFIG_PACMAN+=(vim)" in out
        assert "CONFIG_PACMAN+=(git)" in out
        assert "CONFIG_GIT_USER_NAME=TestUser" in out

    def test_shell_exe_config(self, tmp_path: Path) -> None:
        cfg = tmp_path / "test.yaml"
        cfg.write_text("shell-exe:\n  firefox: flatpak run org.mozilla.firefox $@\n")
        out = parse_and_emit(str(cfg))
        assert "CONFIG_SHELL_EXE_firefox=" in out[0]
        assert "flatpak run org.mozilla.firefox $@" in out[0]
        assert "CONFIG_SHELL_EXE_firefox_ALIAS=firefox" in out

    def test_nested_list_in_list_yaml(self, tmp_path: Path) -> None:
        """Integration test: YAML with nested list items like sources list."""
        cfg = tmp_path / "test.yaml"
        cfg.write_text(
            "sources:\n  - apt:\n      - pkg1\n      - pkg2\n  - npm:\n      - pkg3\n"
        )
        out = parse_and_emit(str(cfg))
        # Since emit doesn't handle nested lists-of-dicts natively,
        # we just ensure parsing doesn't crash and produces output
        assert any("CONFIG_SOURCES" in line for line in out)


# ---------------------------------------------------------------------------
# __main__ CLI
# ---------------------------------------------------------------------------


class TestCli:
    """Tests for the __main__ entry point."""

    def test_prints_usage_on_no_args(self) -> None:
        result = subprocess.run(
            [sys.executable, str(PARSER)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Usage:" in result.stderr

    def test_parses_config(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("steamos: true\n")
        result = subprocess.run(
            [sys.executable, str(PARSER), str(cfg)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "CONFIG_STEAMOS=true" in result.stdout

    def test_missing_file(self, tmp_path: Path) -> None:
        result = subprocess.run(
            [sys.executable, str(PARSER), str(tmp_path / "nope.yaml")],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
