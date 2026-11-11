# droopy

A [Claude Code](https://claude.com/claude-code) skill that turns any script or command-line tool
that works on files into a Linux desktop *droplet*: a PySide6 / Qt Quick app you drag files onto,
with installer, menu entry, "Open with" MIME types, settings dialog, job queue and a per-app
animated background designed for its purpose.

Named after the comic-strip dog, and a spin on "drop" / "droplet".

## Install

```bash
git clone https://github.com/Rec0iL/droopy ~/.claude/skills/droopy
```

Requirements on the machine that runs the generated apps: Python 3.10+, PySide6 (with Qt Quick),
and optionally `qsb-qt6` for compiled shader backgrounds (a QML-only fallback is used otherwise).

## Usage

```
/droopy <script.py | command>      # step-by-step interview with radio questions
/droopy <script> --quick           # decide everything, ask only about the look
/droopy <script> --plan            # one plan to approve, then build
/droopy update <droplet folder>    # refresh the scaffold, keep hand edits
```

## Layout

| Path | Purpose |
|---|---|
| `SKILL.md` | the skill: phases, rules, modes |
| `references/` | interview rounds, option-to-control mapping, core contract, wrapping non-Python tools, look design, verification, manifest schema |
| `template/` | the droplet scaffold (Python package, QML components, shader, installer) with `droopy:feature` markers and protected regions |
| `tools/scaffold.py` | renders the template from a `droopy.json` manifest, strips unused features, compiles the shader; `--update` mode keeps hand edits |
| `tools/analyze.py` | static look at a script (argparse options, constants, extensions, deps) or a tool's `--help` |
| `tools/droplet_check.py` | offscreen smoke test and real-display screenshot of a generated droplet |

## Generated droplet

```
<AppName>/
  main.py  install.sh  uninstall.sh  README.md  requirements.txt  droopy.json
  <app_id>/   core.py (the ported logic, no Qt)  backend.py  worker.py  settings.py  runner.py  app.py
  qml/        Main, DropZone, JobCard, SettingsDialog, Theme, Background (+ History/Delete dialogs when chosen)
  shaders/    bg.frag + compiled bg.frag.qsb
  packaging/  <app_id>.svg
  tests/      test_core.py
```
