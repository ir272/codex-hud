#!/usr/bin/env python3
from pathlib import Path
import importlib.util

script = Path(__file__).with_name("setup_codex_hud.py")
spec = importlib.util.spec_from_file_location("setup_codex_hud", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # type: ignore[union-attr]

sample = 'model = "gpt-5.5"\n\n[tui.model_availability_nux]\n"gpt-5.5" = 4\n'
patched = mod.patch_tui_table(sample)
values = mod.parse_tui_values(patched)
assert values["status_line"] == mod.STATUS_LINE
assert values["terminal_title"] == mod.TERMINAL_TITLE
assert values["status_line_use_colors"] is True
assert patched.index("[tui]") < patched.index("[tui.model_availability_nux]")
patched_again = mod.patch_tui_table(patched)
assert patched_again == patched
print("setup_codex_hud self-check passed")
