# Mapping script options to UI controls

Settings keys are camelCase, declared in `core.OPTION_DEFAULTS`, read in QML as `dlg.s.<key>` /
`win.s.<key>`, written with `backend.setSetting("<key>", value)`. They reach `process()` in `opts`.

| Script option | Control | QML (inside the `droopy:options` region of SettingsDialog.qml) |
|---|---|---|
| bool flag | `PillSwitch` | `Row_ { title: "Keep metadata"; PillSwitch { checked: dlg.s.keepMeta; onToggled: (v) => backend.setSetting("keepMeta", v) } }` |
| enum, 2-4 values | `Segmented` | `Row_ { title: "Format"; Segmented { model: ["PNG","WebP"]; currentIndex: ["png","webp"].indexOf(dlg.s.format); onActivated: (i) => backend.setSetting("format", ["png","webp"][i]) } }` |
| enum, 5+ values | `Segmented` with short labels, or two rows | split into groups; never a dropdown (no styled ComboBox in the kit) |
| int/float range | `GlowSlider` | `Row_ { title: "Quality: " + dlg.s.quality; GlowSlider { from: 1; to: 100; stepSize: 1; value: dlg.s.quality; width: 190; onMoved: backend.setSetting("quality", Math.round(value)) } }` |
| folder path | `PillButton` + FolderDialog | copy the `outPicker` pattern in SettingsDialog.qml |
| free text (prefix, pattern) | `TextField` from Controls.Basic styled with Theme | keep rare; prefer presets |
| internal knob | fixed | keep as a constant in core.py, mention in README |

Header quick toggles go between the `droopy:header` markers in Main.qml, preceded by the `→`
arrow Text if it is a target-format choice:

```qml
// droopy:header begin
Text { text: "→"; font.pixelSize: 22; font.weight: Font.Bold; color: Theme.dark ? "white" : Theme.text }
Segmented {
    model: ["PNG", "WebP"]
    currentIndex: Math.max(0, ["png", "webp"].indexOf(win.s.format))
    onActivated: (i) => backend.setSetting("format", ["png", "webp"][i])
}
// droopy:header end
```

Add a `hint:` to every Row_ that is not self-explanatory (one sentence, what the setting changes).
Give every option a CLI flag in `core.main()` so the terminal path matches the GUI.
