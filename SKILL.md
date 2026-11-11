---
name: droopy
description: "Turn any script or command-line tool that works on files into a drag & drop desktop droplet (PySide6/Qt Quick app with installer, menu entry, Open-with, settings, job queue, per-app animated background). Trigger: /droopy <script>. Interviews the user with radio questions about which options to expose, where, which extras to add and how it should look. Also /droopy update <folder> to refresh a generated droplet."
---

# /droopy

Make a *droplet* out of a script: a small Linux desktop app you drop files or folders on, in the
style of MangaPacker / IconExtractor. Everything the script can do becomes a setting, the result
is installable (`install.sh`), appears in the app menu and in "Open with", keeps a CLI, and gets
an animated background designed for its purpose.

## Usage

```
/droopy <script.py | command>            # step-by-step interview (default)
/droopy <script> --quick                 # decide everything yourself, ask only about the look
/droopy <script> --plan                  # write the whole proposal as a plan (plan mode), one confirm
/droopy update <droplet folder>          # refresh scaffold from droopy.json, keep hand edits
/droopy --help
```

Ask every question with **AskUserQuestion radio questions** (2-4 options, recommended first).
Never ask in free text when a radio question can carry the choice.

If invoked with `--help`, print the Usage block and stop.

## What you must do when invoked

Skill root: `~/.claude/skills/droopy/`. Tools in `tools/`, template in `template/`, details in
`references/`. Read a reference file when its phase starts; do not skip phases.

### Phase 0 - Inspect (no questions yet)

1. Resolve the script path. Run `python3 tools/analyze.py <script>` and read the script itself
   (for a wrapped tool read its `--help`; if an argument looks like a sample file, run the tool once
   on it to see what it prints, following `references/wrapped.md`).
2. Decide `kind`: `python` (importable, has functions taking paths) or `wrapped` (anything else,
   or Python that only works as a process).
3. **Droppable check.** Needs file or folder inputs via arguments. If it reads stdin interactively,
   is a server, or takes no paths: ask whether to adapt the script first (add a path-taking entry
   point) using a radio question, do that adaptation in the original script if agreed, then continue.
   If declined, explain what would need to change and stop.
4. Draft, internally, the full manifest (see `references/manifest.md`): inputs, outputs, every
   option with a proposed control and placement, extras that fit, two or three look concepts.

### Phase 1 - Interview (skip in `--quick`; in `--plan` present it all as the plan instead)

Follow `references/interview.md`. Rounds, each one AskUserQuestion call with up to 4 questions:

1. **Inputs & outputs** - which extensions/folders, what one job is, where output goes, naming.
2. **Options table** - show the table in the message text (option, type, proposed control,
   proposed placement: header / settings / fixed), then ask: accept as proposed, move more to
   header, move more to fixed, or custom (free text via Other).
3. **Extras** - from the catalogue in `references/interview.md` (history, delete original,
   retry, previews, Open-with MIME types, CLI, custom naming, notifications...). Propose which fit;
   ask multiSelect.
4. **Placement & name** - app name, where the folder goes (sibling of the script is the
   recommended first option), install now or later.
5. **Look** - 2-3 background concepts tied to the purpose (see `references/look.md`), mascot
   style (pixel icon / glyph / kaomoji / none), palette mood. In `--quick` this is the only round.

### Phase 2 - Generate

1. Write `droopy.json` (schema in `references/manifest.md`) in the scratchpad.
2. `python3 tools/scaffold.py --manifest droopy.json --out <folder>`.
3. Hand-write the per-app parts (never leave placeholders or NotImplementedError behind):
   - `<pkg>/core.py` - port the script's logic into `process()` following
     `references/core-contract.md` (Python) or `references/wrapped.md` (subprocess).
   - option rows in `qml/SettingsDialog.qml` between the `droopy:options` markers and header
     quick toggles between `droopy:header` markers, per `references/options-mapping.md`.
   - `shaders/bg.frag` (or `BackgroundSoft.qml` tweaks when no qsb-qt6), the palette region in
     `qml/Theme.qml`, the glyph region in `qml/Background.qml`, `packaging/<id>.svg`, per
     `references/look.md`. Recompile the shader after editing (command in `references/look.md`).
   - `tests/test_core.py` - real cases for the script's behaviour.
   - `README.md` body (what it accepts, what it writes, each setting in one line).
4. Remove any marker comments you no longer need except the protected regions
   (`droopy:options|header|palette|glyphs`), which `update` relies on.

### Phase 3 - Verify (follow `references/verify.md`)

1. `python3 -m unittest tests.test_core` inside the folder.
2. `python3 tools/droplet_check.py <folder> --smoke <sample files>` - must print `OK` and show
   at least one `done` job (make a sample input in the scratchpad if none exists).
3. `python3 tools/droplet_check.py <folder> --shot <scratch>/shot.png --theme dark` and again
   `--theme light`; a window appears for ~4 s. Read both PNGs and fix anything that looks wrong
   (contrast, overlap, shader not matching the concept) before continuing.
4. Install only if the user chose that in round 4, otherwise print the install command.

### Phase 4 - Report

Lead with what was built and where. List: accepted inputs, each exposed option and where it sits,
extras included, the look concept, test/smoke/screenshot results, the install command. Mention
that `droopy.json` enables `/droopy update`.

## `/droopy update <folder>`

1. Read `<folder>/droopy.json`. Ask one radio question: refresh scaffold only, change options,
   change extras, or change look. Collect the changes with further radio questions.
2. Edit the manifest, then `python3 tools/scaffold.py --manifest <folder>/droopy.json --out <folder> --update`.
   Protected files (core.py, shader, icon, README, tests) and protected regions survive; apply
   requested option/look changes by hand in those regions afterwards.
3. Re-run Phase 3.

## Rules

- The deliverable is a working app, not a scaffold: `core.process()` must be implemented and
  tested against the script's real behaviour before you report.
- Never modify the original script unless the user agreed to the adaptation in Phase 0.
- Keep the Qt-free core module importable without PySide6 so tests and the CLI work headless.
- One job = one row. Folder handling is a decision (one job per folder vs search inside), not a default.
- Destructive extras (delete original) are off unless chosen; when on, the trash path is the default.
- Visuals must fit the purpose. Kaomoji only if chosen in the look round.
- Do not install, and do not run the real-display screenshot more than needed; both touch the user's desktop.
