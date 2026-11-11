# Interview rounds

Every round is one `AskUserQuestion` call. Options: 2-4, recommended first with "(Recommended)".
Put tables and explanations in the assistant message before the call, keep question text short.
Users can always pick "Other" for free text; honour it.

## Round 1 - Inputs & outputs
Derive candidates from analyze.py (`extensions`, `positionals`) and the script body.

- Q "Which inputs should the droplet accept?" - proposed extension set / "any file" / folders as one job / folders searched recursively.
- Q "What is one job?" - one file = one job (Recommended for converters) / one folder = one job / each dropped item as given.
- Q "Where should output go by default?" - next to the source (Recommended) / fixed custom folder (ask once, settable) / in place (script modifies the source; enables `in_place` results).
- Q "Output naming" - script's own naming / `<stem>.<newext>` / ask (Other).

## Round 2 - Options table
Build the table from analyze.py `options` + `constants` + literals you spotted (sizes, quality, formats,
thresholds, flags). For each: name, type, default, proposed control (see options-mapping.md),
proposed placement.

| Option | Type | Default | Control | Placement |
|---|---|---|---|---|
| quality | int 1-100 | 85 | slider | settings |
| format | enum png/webp | png | segmented | header |
| keep_metadata | bool | true | switch | settings |
| threads | int | 4 | fixed | (not exposed) |

Placement rules: header gets at most 2 controls, only enums with <=4 values or a single switch
the user flips every run. Everything else goes to settings. Internal knobs (threads, buffer sizes,
debug) are fixed unless the user asks.

- Q "Accept the options table as proposed?" - yes (Recommended) / expose more in the header /
  expose fewer, keep more fixed / I'll list changes (Other).
- If the script had no options: Q whether to add the usual ones (format, quality...) that the
  underlying library supports; propose concretely.

## Round 3 - Extras catalogue
Propose with reasons; ask multiSelect. Mark your recommendation.

| Extra | Fits when | Feature key |
|---|---|---|
| Retry failed | any | retry |
| Reveal in file manager | any (always on) | - |
| Result previews (thumbnails) | output is an image | previews |
| History dialog | user re-runs on the same sources | history |
| Delete original (ask/never/always, trash) | converters that replace files | delete |
| Open-with MIME types | known input types | mimetypes |
| Keep a CLI (`python3 -m pkg.core`) | always (on by default) | - |
| Rename vs overwrite | any (always on) | - |
| Desktop notification when batch finishes | long jobs | notify (implement via `notify-send` in backend) |
| Custom output naming pattern | script names outputs | naming |
| Low-power mode | always on | - |

## Round 4 - Placement & name
- Q "App name?" - proposed PascalCase name from the script (Recommended) / 2 alternatives.
- Q "Where should the droplet folder go?" - `<script dir>/<AppName>/` (Recommended) /
  `~/Apps/<AppName>` / somewhere else (Other).
- Q "Install when done?" - per-user install (Recommended) / just build, I'll install / `--link` dev install.

## Round 5 - Look
Read look.md first. Offer 2-3 concepts with one-line descriptions tied to the purpose, e.g. for a
video converter: "film strip: frames scrolling past a scan head"; for an audio tool: "waveform
ribbons and level meters". Then:
- Q "Background concept?" - concept A (Recommended) / B / C.
- Q "Mascot?" - pixel icon that assembles (Recommended) / app icon glyph / kaomoji / none.
- Q "Palette mood?" - 3 named moods with example colours (e.g. slate+cyan, warm paper+amber, deep purple+magenta).

## --quick
Skip rounds 1-4. Use: proposed inputs, one file = one job, next to source, options as proposed,
extras: retry + previews(if image) + mimetypes + CLI, name from script, folder next to script,
no install. Ask only round 5.

## --plan
Enter plan mode. Write the full proposal (all five rounds, pre-filled with recommendations) as
the plan; exit plan mode for approval; then generate without further questions unless the user
edits the plan.
