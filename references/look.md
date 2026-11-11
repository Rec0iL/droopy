# The look phase: background shader, palette, glyphs, icon, mascot

Goal: the background should say what the app does at a glance. Not generic blobs, not kawaii unless
chosen. Think of the medium the app works on and the process it performs, then animate that.

## Concept recipes (pick/adapt, propose 2-3 with one line each)

| Purpose | Concept |
|---|---|
| icon / resource extraction | pixel grid, scan line sweeping, bitmap cells lighting up (see `template/shaders/examples/icon_scanner.frag`) |
| image conversion / resize | soft photo-paper gradient, developing-tray ripples, aspect-ratio frames drifting |
| video transcoding | film strip rows scrolling at different speeds, a playhead, waveform under it |
| audio | horizontal waveform ribbons, VU bars breathing with `energy` |
| archive / packing | boxes stacking into a grid, zip-teeth meshing, compression "squeeze" pulse |
| documents / PDF | pages sliding into a stack, typographic ruled lines, paper grain |
| 3D / CAD | isometric wireframe grid, slowly rotating polyhedron edges |
| data / CSV | columns of tick marks, scatter points settling into bars |
| manga / comics (kawaii) | pastel aurora + kaomoji (see `examples/pastel_aurora.frag`) |

Always include: a calm idle state, a visible reaction to `energy` (drag hover / working), a
`night` cross-fade with a readable light variant, and a cheap path when `quality == 0`.

## Shader contract (do not change the uniform block)
`shaders/bg.frag` uses `time`, `resolution`, `energy` (0..1), `quality` (0/1), `night` (0..1).
Keep GLSL 440 Qt-shader style as in the template. Compile:

```bash
qsb-qt6 --glsl "100 es,120,150" --hlsl 50 --msl 12 -o shaders/bg.frag.qsb shaders/bg.frag
```

If `qsb-qt6` is missing: the manifest `look.background` becomes `soft` and `qml/BackgroundSoft.qml`
is used; express the concept there with Rectangles/Shapes/animations instead of GLSL.

## Palette (region `droopy:palette` in qml/Theme.qml)
Pick light and dark values for: windowBg, text, textSoft, dataText, accent, accent2, mint, warm,
danger, field, glyphGlow, titleOutline, glassLight/glassDark. Match the shader's colours (the glass
cards tint over it). Check contrast in both screenshots.

## Glyph layer (region `droopy:glyphs` in Background*.qml)
Short strings that belong to the medium (hex bytes and resource names for binaries, timecodes for
video, note names for audio, file extensions for archives). 8-16 entries, mono font, opacity ~0.35,
`glyphDrift` 0 to hover or >0 to stream upward. `glyphs: []` for none.

## Icon (packaging/<app_id>.svg, 256x256)
Rounded square with a gradient from the palette, a simple object that reads at 48 px (the medium
+ an arrow or spark for the action). `example_icon.svg` shows the style; no text in the icon.

## Mascot (manifest `features.mascot`)
- `pixel`: `PixelIcon.qml` 11x11 bitmap; edit its `bitmap` to resemble the app's output.
- `glyph`: the app icon in the header, a Unicode glyph (`drop.glyph`) in the drop zone.
- `kaomoji`: faces in header, drop zone and job cards.
- `none`: no mascot; status chips only.
