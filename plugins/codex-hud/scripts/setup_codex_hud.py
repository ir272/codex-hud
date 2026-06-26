#!/usr/bin/env python3
"""Apply the Codex HUD footer/title preset."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

PRESETS: dict[str, dict[str, Any]] = {
    "compact": {
        "status_line": [
            "model-with-reasoning",
            "context-used",
            "five-hour-limit",
            "git-branch",
            "branch-changes",
        ],
        "status_line_use_colors": True,
        "terminal_title": ["spinner", "project", "git-branch"],
    },
    "balanced": {
        "status_line": [
            "model-with-reasoning",
            "context-used",
            "five-hour-limit",
            "weekly-limit",
            "permissions",
            "approval-mode",
            "git-branch",
            "branch-changes",
            "current-dir",
            "task-progress",
        ],
        "status_line_use_colors": True,
        "terminal_title": ["spinner", "project", "git-branch", "model", "task-progress"],
    },
    "full": {
        "status_line": [
            "model-with-reasoning",
            "context-used",
            "context-remaining",
            "context-window-size",
            "five-hour-limit",
            "weekly-limit",
            "permissions",
            "approval-mode",
            "git-branch",
            "branch-changes",
            "current-dir",
            "task-progress",
            "used-tokens",
        ],
        "status_line_use_colors": True,
        "terminal_title": ["spinner", "project", "git-branch", "model", "task-progress"],
    },
}

KEYS = {"status_line", "status_line_use_colors", "terminal_title"}
TABLE_RE = re.compile(r"^\s*\[\[?[^\]]+\]\]?\s*(?:#.*)?$")
TUI_RE = re.compile(r"^\s*\[tui\]\s*(?:#.*)?$")
TUI_CHILD_RE = re.compile(r"^\s*\[\[?tui\." )


def config_path(raw: str | None) -> Path:
    if raw:
        return Path(raw).expanduser()
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "config.toml"


def toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(json.dumps(item) for item in value) + "]"
    return json.dumps(value)


def hud_lines(values: dict[str, Any]) -> list[str]:
    return [f"{key} = {toml_value(value)}" for key, value in values.items()]


def line_sets_key(line: str) -> bool:
    stripped = line.lstrip()
    if stripped.startswith("#"):
        return False
    return any(re.match(rf"{re.escape(key)}\s*=", stripped) for key in KEYS)


def filter_tui_lines(lines: list[str]) -> list[str]:
    kept: list[str] = []
    skip_depth = 0
    for line in lines:
        if skip_depth:
            skip_depth += line.count("[") - line.count("]")
            if skip_depth <= 0:
                skip_depth = 0
            continue
        if line_sets_key(line):
            _, raw = line.split("=", 1)
            skip_depth = raw.count("[") - raw.count("]")
            if skip_depth < 0:
                skip_depth = 0
            continue
        kept.append(line)
    return kept


def patch_tui_table(text: str, values: dict[str, Any]) -> str:
    lines = text.splitlines()
    block = hud_lines(values)

    for idx, line in enumerate(lines):
        if TUI_RE.match(line):
            end = idx + 1
            while end < len(lines) and not TABLE_RE.match(lines[end]):
                end += 1
            kept = filter_tui_lines(lines[idx + 1 : end])
            while kept and not kept[0].strip():
                kept.pop(0)
            new_section = [lines[idx], *block]
            if kept:
                new_section += ["", *kept]
            elif end < len(lines):
                new_section.append("")
            return "\n".join(lines[:idx] + new_section + lines[end:]) + "\n"

    insert_at = next((i for i, line in enumerate(lines) if TUI_CHILD_RE.match(line)), len(lines))
    new_table = ["[tui]", *block, ""]
    before = lines[:insert_at]
    after = lines[insert_at:]
    if before and before[-1].strip():
        before.append("")
    return "\n".join(before + new_table + after) + "\n"


def parse_tui_values(text: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if not TUI_RE.match(line):
            continue
        for body in lines[idx + 1 :]:
            if TABLE_RE.match(body):
                break
            stripped = body.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, raw = [part.strip() for part in stripped.split("=", 1)]
            if key not in KEYS:
                continue
            raw = raw.split("#", 1)[0].strip()
            if raw in {"true", "false"}:
                values[key] = raw == "true"
            elif raw.startswith("["):
                try:
                    values[key] = json.loads(raw)
                except json.JSONDecodeError:
                    values[key] = None
            else:
                try:
                    values[key] = json.loads(raw)
                except json.JSONDecodeError:
                    values[key] = raw.strip('"')
        break
    return values


def matches(path: Path, values: dict[str, Any]) -> bool:
    if not path.exists():
        return False
    return all(parse_tui_values(path.read_text(encoding="utf-8")).get(k) == v for k, v in values.items())


def backup_config(path: Path) -> Path:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S%f")
    backup = path.with_name(f"{path.name}.bak-codex-hud-{stamp}")
    shutil.copy2(path, backup)
    return backup


def latest_backup(path: Path) -> Path | None:
    backups = sorted(path.parent.glob(f"{path.name}.bak-codex-hud-*"))
    return backups[-1] if backups else None


def remove_tui_values(text: str) -> str:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if TUI_RE.match(line):
            end = idx + 1
            while end < len(lines) and not TABLE_RE.match(lines[end]):
                end += 1
            kept = filter_tui_lines(lines[idx + 1 : end])
            return "\n".join(lines[: idx + 1] + kept + lines[end:]) + "\n"
    return text


def apply(path: Path, values: dict[str, Any], preset: str, *, dry_run: bool) -> int:
    existed = path.exists()
    original = path.read_text(encoding="utf-8") if existed else ""
    updated = patch_tui_table(original, values)
    if not all(parse_tui_values(updated).get(k) == v for k, v in values.items()):
        raise SystemExit("Internal error: patched TOML does not contain HUD values.")
    if updated == original:
        print(f"codex-hud already configured: {path}")
        return 0
    if dry_run:
        print(updated)
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if existed:
        backup = backup_config(path)
    path.write_text(updated, encoding="utf-8")
    if not matches(path, values):
        raise SystemExit("Wrote config, but HUD values did not verify.")
    print(f"codex-hud configured ({preset}): {path}")
    if backup is not None:
        print(f"backup: {backup}")
    print("status_line: " + " | ".join(values["status_line"]))
    print("terminal_title: " + " | ".join(values["terminal_title"]))
    return 0


def remove(path: Path, *, dry_run: bool) -> int:
    if not path.exists():
        print(f"codex-hud not configured: {path}")
        return 0
    original = path.read_text(encoding="utf-8")
    updated = remove_tui_values(original)
    if updated == original:
        print(f"codex-hud not configured: {path}")
        return 0
    if dry_run:
        print(updated)
        return 0
    backup = backup_config(path)
    path.write_text(updated, encoding="utf-8")
    print(f"codex-hud removed: {path}")
    print(f"backup: {backup}")
    return 0


def restore(path: Path) -> int:
    backup = latest_backup(path)
    if backup is None:
        print(f"codex-hud restore failed: no backup found for {path}")
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, path)
    print(f"codex-hud restored: {path}")
    print(f"restored_from: {backup}")
    return 0


def check(path: Path, values: dict[str, Any], preset: str) -> int:
    try:
        ok = matches(path, values)
    except Exception as exc:  # noqa: BLE001 - print concise CLI diagnostics.
        print(f"codex-hud check failed: {exc}")
        return 2
    if ok:
        print(f"codex-hud check passed ({preset}): {path}")
        return 0
    print(f"codex-hud check failed: {path}")
    print(f"Run: python3 {Path(__file__).resolve()} --preset {preset}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the Codex HUD TUI preset.")
    parser.add_argument("--config", help="Path to config.toml; defaults to $CODEX_HOME/config.toml or ~/.codex/config.toml")
    parser.add_argument("--preset", choices=PRESETS, default="balanced", help="HUD preset to apply or check")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="Verify the preset is already applied")
    action.add_argument("--remove", action="store_true", help="Remove codex-hud TUI keys from config.toml")
    action.add_argument("--restore", action="store_true", help="Restore the most recent codex-hud backup")
    parser.add_argument("--dry-run", action="store_true", help="Print patched TOML instead of writing")
    args = parser.parse_args()
    path = config_path(args.config)
    values = PRESETS[args.preset]
    if args.check:
        return check(path, values, args.preset)
    if args.remove:
        return remove(path, dry_run=args.dry_run)
    if args.restore:
        return restore(path)
    return apply(path, values, args.preset, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
