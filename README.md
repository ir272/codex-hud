# Codex HUD

Clean native Codex CLI footer for model, context usage, limits, permissions, git, worktree, and progress.

## Install

```bash
codex plugin marketplace add ir272/codex-hud
codex plugin add codex-hud@codex-hud
```

Restart Codex, then ask:

```text
Use codex-hud to apply the footer.
```

Default preset: `balanced`.

## Presets

Ask Codex:

```text
Use codex-hud to apply the compact preset.
Use codex-hud to apply the balanced preset.
Use codex-hud to apply the full preset.
```

Or run directly:

```bash
python3 plugins/codex-hud/scripts/setup_codex_hud.py --preset compact
python3 plugins/codex-hud/scripts/setup_codex_hud.py --preset balanced
python3 plugins/codex-hud/scripts/setup_codex_hud.py --preset full
```

## Pin a release

```bash
codex plugin marketplace add ir272/codex-hud --ref v0.2.0
codex plugin add codex-hud@codex-hud
```

## Update

```bash
codex plugin marketplace upgrade codex-hud
codex plugin add codex-hud@codex-hud
```

## Check

```text
Use codex-hud to check my setup.
```

## Remove or restore

```bash
python3 plugins/codex-hud/scripts/setup_codex_hud.py --remove
python3 plugins/codex-hud/scripts/setup_codex_hud.py --restore
```

Codex HUD uses Codex's built-in footer items. Custom progress bars are not part of Codex's native footer API yet.

## Uninstall

```bash
codex plugin remove codex-hud@codex-hud
codex plugin marketplace remove codex-hud
```
