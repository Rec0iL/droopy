pragma Singleton
import QtQuick

// Light / dark palette. Everything is derived from `night` (0..1) which animates,
// so switching themes cross-fades the whole UI and the shader background.
QtObject {
    id: theme

    // "auto" follows the desktop colour scheme; set from Main.qml (settings.theme)
    property string mode: "auto"
    readonly property bool systemDark: Qt.styleHints.colorScheme === Qt.ColorScheme.Dark
    readonly property bool dark: mode === "dark" || (mode === "auto" && systemDark)

    property real night: dark ? 1 : 0
    Behavior on night { NumberAnimation { duration: 600; easing.type: Easing.InOutSine } }

    function mix(a, b, t) {
        const ca = Qt.color(a), cb = Qt.color(b)
        return Qt.rgba(ca.r + (cb.r - ca.r) * t, ca.g + (cb.g - ca.g) * t,
                       ca.b + (cb.b - ca.b) * t, ca.a + (cb.a - ca.a) * t)
    }
    function glass(alpha) {
        const base = mix(glassLight, glassDark, night)
        return Qt.rgba(base.r, base.g, base.b, Math.max(0, Math.min(1, alpha + night * 0.12)))
    }
    function edge(alpha) {
        return Qt.rgba(1, 1, 1, alpha * (1 - night * 0.72))
    }

    // droopy:palette begin   (edited per app in the look phase - light value, dark value)
    readonly property color glassLight: "#ffffff"
    readonly property color glassDark: "#101828"
    readonly property color windowBg: mix("#dbe5f3", "#0b1020", night)
    readonly property color text: mix("#1b2a44", "#e6eefb", night)
    readonly property color textSoft: mix("#53667f", "#9fb0c8", night)
    readonly property color dataText: mix("#5b7190", "#8fb6d9", night)   // background glyph layer
    readonly property color accent: mix("#2f6fe4", "#4f8dff", night)     // primary (buttons, bars)
    readonly property color accent2: mix("#1aa3c9", "#3fd0ff", night)    // secondary (gradients)
    readonly property color mint: mix("#1fa97f", "#4fe0b5", night)       // success
    readonly property color warm: mix("#e8962a", "#ffb547", night)       // overall progress start
    readonly property color danger: mix("#e04f6a", "#ff6f86", night)
    readonly property color dangerBg: mix("#ffdde3", "#4a1d2a", night)
    readonly property color field: mix(Qt.rgba(0.25, 0.42, 0.75, 0.14), Qt.rgba(1, 1, 1, 0.07), night)
    readonly property color fieldBorder: mix(Qt.rgba(0.25, 0.42, 0.75, 0.40), Qt.rgba(1, 1, 1, 0.22), night)
    readonly property color glyphGlow: mix("#2f6fe4", "#2fc8ff", night)  // shadow of background glyphs
    readonly property color titleOutline: Qt.rgba(0.2, 0.6, 0.9, 0.45)
    readonly property string font: "Noto Sans"
    readonly property string mono: "Noto Sans Mono"
    // droopy:palette end

    readonly property color glassBorder: edge(0.70)
}
