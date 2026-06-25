#!/usr/bin/env python3
"""Dependency-free checks for the Codex HUD plugin repo."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "codex-hud"
SETUP = PLUGIN / "scripts" / "setup_codex_hud.py"


def require(path: Path) -> None:
    assert path.exists(), f"missing {path.relative_to(ROOT)}"


def load_setup():
    spec = importlib.util.spec_from_file_location("setup_codex_hud", SETUP)
    assert spec and spec.loader, "cannot load setup script"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_manifest() -> None:
    manifest_path = PLUGIN / ".codex-plugin" / "plugin.json"
    require(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    assert manifest["name"] == "codex-hud"
    assert manifest["version"] == "0.1.0"
    assert manifest["skills"] == "./skills/"
    assert manifest["interface"]["displayName"] == "Codex HUD"


def test_marketplace() -> None:
    marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text())
    entry = marketplace["plugins"][0]
    assert marketplace["name"] == "codex-hud"
    assert entry["name"] == "codex-hud"
    assert entry["source"]["path"] == "./plugins/codex-hud"
    assert entry["policy"] == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}


def test_skill() -> None:
    skill = PLUGIN / "skills" / "codex-hud" / "SKILL.md"
    require(skill)
    text = skill.read_text()
    assert text.startswith("---\n")
    assert "name: codex-hud" in text.split("---", 2)[1]
    assert "description:" in text.split("---", 2)[1]


def test_setup_script() -> None:
    setup = load_setup()
    cases = [
        'model = "x"\n\n[tui.model_availability_nux]\n"x" = 1\n',
        '[tui]\nnotifications = false\nstatus_line = ["model"]\n\n[history]\npersistence = "save-all"\n',
        '[tui]\n# status_line = ["old"]\nterminal_title = []\n',
    ]
    for text in cases:
        patched = setup.patch_tui_table(text)
        values = setup.parse_tui_values(patched)
        assert values["status_line"] == setup.STATUS_LINE
        assert values["terminal_title"] == setup.TERMINAL_TITLE
        assert values["status_line_use_colors"] is True
        assert setup.patch_tui_table(patched) == patched

    with tempfile.TemporaryDirectory() as tmp:
        cfg = Path(tmp) / "config.toml"
        cfg.write_text('model = "x"\n')
        subprocess.run([sys.executable, str(SETUP), "--config", str(cfg)], check=True, capture_output=True, text=True)
        subprocess.run([sys.executable, str(SETUP), "--config", str(cfg), "--check"], check=True, capture_output=True, text=True)
        assert list(Path(tmp).glob("config.toml.bak-codex-hud-*"))


def main() -> None:
    for check in (test_manifest, test_marketplace, test_skill, test_setup_script):
        check()
    print("codex-hud checks passed")


if __name__ == "__main__":
    main()
