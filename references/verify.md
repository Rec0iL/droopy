# Verification checklist (Phase 3)

Run everything from the droplet folder with the skill's tools (`T=~/.claude/skills/droopy/tools`).

1. **Unit tests**: `python3 -m unittest tests.test_core` - all pass, no skipped happy path.
2. **CLI**: `python3 -m <pkg>.core <sample> -o <scratch>/out` - prints `[ok  ]` lines, files exist.
3. **Smoke (offscreen)**: `python3 $T/droplet_check.py . --smoke <sample> [<file without content>]`
   - must end with `droplet_check: OK`, one `done` row, and a `skipped`/`error` row for the bad input
   with a readable message. Samples: make them in the scratchpad (never next to the user's files),
   or copy a real one there.
4. **Screenshots (real display)**: `python3 $T/droplet_check.py . --shot <scratch>/dark.png --theme dark <sample>`
   and `--theme light` without files. Read both images. Check: shader matches the concept, text
   readable on both, header fits at 900 px, job card shows preview/chip, nothing overlaps.
   Fix and repeat once if needed. The offscreen platform cannot render ShaderEffect, so this is the
   only way to see the shader.
5. **Exit cleanliness**: stderr of the smoke run has no `TypeError`/`.qml` lines (font warnings are fine).
6. **Install (only if chosen)**: `./install.sh`; then `desktop-file-validate` hint lines are fine,
   errors are not. The Categories key should name one main category.
7. **Leftovers**: `grep -rn "__[A-Z_]*__\|NotImplementedError\|droopy:feature" <folder>` must only
   show `__init__`, `__name__`, `__file__`-style Python dunders - no placeholders, no feature markers.
