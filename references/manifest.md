# droopy.json

Written by the skill before scaffolding; copied into the droplet; read by `/droopy update`.

```json
{
  "app_name": "IconExtractor",            "app_id": "iconextractor",
  "comment": "Drag & drop icon extractor for .exe / .dll files (PNG / ICO)",
  "generic_name": "Icon Extractor",       "categories": "Utility;",
  "keywords": "icon;exe;dll;png;ico;",
  "mimetypes": "application/x-ms-dos-executable;application/x-msdownload;image/vnd.microsoft.icon;",
  "script": "/home/me/Scripts/icon_extractor.py",
  "kind": "python",                       "supported": [".exe", ".dll", ".ico"],
  "accept_dirs": false,
  "option_defaults": {"sizeMode": "largest", "allGroups": false},
  "options": [
    {"key": "sizeMode", "type": "enum", "values": ["largest", "all", "ico"], "labels": ["PNG", "All sizes", "ICO"],
     "control": "segmented", "placement": "header", "title": "Export as", "hint": "..."},
    {"key": "allGroups", "type": "bool", "control": "switch", "placement": "settings", "title": "Every icon group"}
  ],
  "py_deps": ["icoextract", "PIL"],       "py_requirements": ["icoextract>=0.1.4", "Pillow>=9.0"],
  "tool_checks": [],
  "features": {"history": false, "delete": false, "retry": true, "previews": true, "mascot": "pixel"},
  "drop": {"title": "Drop .exe / .dll here", "hover": "Release to extract",
           "hint": "Windows binaries, .ico files or whole folders", "glyph": "▣",
           "file_dialog_title": "Choose Windows binaries",
           "file_filter": "Windows binaries & icons (*.exe *.dll *.ico)",
           "nothing_msg": "Nothing to extract here (no .exe / .dll / .ico found)",
           "working_label": "READING", "done_title": "Extraction finished!"},
  "look": {"background": "shader", "concept": "resource scanner: pixel grid + scan line",
           "mood": "slate + cyan + amber"},
  "readme_body": "- **Input:** ...\n- **Output:** ...",
  "install": "user"
}
```

`features.mascot`: `pixel` | `glyph` | `kaomoji` | `none`. `look.background`: `shader` | `soft`.
`options` is documentation for `update` and the README; the scaffold only uses `option_defaults`.

Protected on update (never overwritten): `<pkg>/core.py`, `shaders/bg.frag(.qsb)`, `README.md`,
`packaging/<app_id>.svg`, `tests/test_core.py`. Protected regions inside regenerated files:
`droopy:options`, `droopy:header` (Main/SettingsDialog), `droopy:palette` (Theme),
`droopy:glyphs` (Background*). Everything else is re-rendered from the template.
