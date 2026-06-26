---
name: codex-hud
description: Configure, repair, or tune Ian's Codex HUD plugin and Claude-HUD-style Codex CLI footer/title. Use when the user asks for codex-hud, a clean Codex status line, context/usage/mode/git/worktree/model visibility in the Codex CLI, or setup/verification of `tui.status_line` and `tui.terminal_title`.
---

# Codex HUD

Use Codex's native TUI footer before building any custom renderer. The presets mirror Claude-HUD's clean at-a-glance shape with native Codex items: model, context usage, usage limits, permission/approval mode, git branch/change state, current worktree, and task progress.

## Setup

Resolve the plugin root as the parent of the `skills/` directory containing this `SKILL.md`, then run:

```bash
python3 <plugin-root>/scripts/setup_codex_hud.py
```

Use `--preset compact`, `--preset balanced`, or `--preset full` when the user asks for a specific density. Default to `balanced`.

Then restart Codex, or open a new thread/session, so the TUI reloads `~/.codex/config.toml`.

## Verify

```bash
python3 <plugin-root>/scripts/setup_codex_hud.py --check
codex debug prompt-input >/tmp/codex-hud-prompt-check.json
```

## Remove or restore

```bash
python3 <plugin-root>/scripts/setup_codex_hud.py --remove
python3 <plugin-root>/scripts/setup_codex_hud.py --restore
```

## Balanced preset

- `tui.status_line`: `model-with-reasoning`, `context-used`, `five-hour-limit`, `weekly-limit`, `permissions`, `approval-mode`, `git-branch`, `branch-changes`, `current-dir`, `task-progress`
- `tui.terminal_title`: `spinner`, `project`, `git-branch`, `model`, `task-progress`
- `tui.status_line_use_colors = true`

Do not port Claude HUD's transcript parser, ship a sidecar, or build a PTY overlay unless the user explicitly asks. Custom bars should wait for a native Codex custom statusline renderer API.
