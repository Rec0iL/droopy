import QtQuick
import QtQuick.Effects

// Fallback background without a compiled shader: layered gradients, drifting soft
// blobs and the same glyph layer. Used when qsb-qt6 was not available at build time.
Item {
    id: root
    property real energy: 0
    property bool lowPower: false
    property real t: 0
    Behavior on energy { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
    FrameAnimation {
        running: root.visible
        onTriggered: root.t += frameTime * (root.lowPower ? 0.5 : 1.0) * (1.0 + root.energy * 1.2)
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0; color: Theme.windowBg }
            GradientStop { position: 1; color: Qt.darker(Theme.windowBg, 1.25) }
        }
    }
    Repeater {
        model: 6
        delegate: Rectangle {
            required property int index
            readonly property real ph: index * 1.1
            width: 260 + index * 60; height: width; radius: width / 2
            color: index % 2 ? Theme.accent : Theme.accent2
            opacity: 0.10 + 0.05 * Math.sin(root.t * 0.4 + ph) + 0.06 * root.energy
            x: (0.1 + 0.15 * index) * root.width - width / 2 + Math.sin(root.t * 0.25 + ph) * 60
            y: (0.2 + 0.12 * index) * root.height - height / 2 + Math.cos(root.t * 0.2 + ph) * 40
            layer.enabled: !root.lowPower
            layer.effect: MultiEffect { blurEnabled: true; blurMax: 64; blur: 1.0 }
        }
    }

    // droopy:glyphs begin
    readonly property var glyphs: [
        ["▣", 0.08, 0.14, 22, 0.55, 0.0], ["◈", 0.82, 0.10, 24, 0.45, 1.3],
        ["✦", 0.46, 0.06, 20, 0.60, 2.1], ["⬡", 0.90, 0.40, 22, 0.50, 3.4]
    ]
    readonly property string glyphFont: Theme.mono
    readonly property real glyphOpacity: 0.35
    readonly property real glyphDrift: 18
    // droopy:glyphs end
    Repeater {
        model: root.glyphs
        delegate: Text {
            required property var modelData
            readonly property real sp: modelData[4] * (root.lowPower ? 0.5 : 1)
            readonly property real ph: modelData[5]
            text: modelData[0]; font.pixelSize: modelData[3]; font.family: root.glyphFont
            color: Theme.dataText
            opacity: root.glyphOpacity + 0.20 * Math.sin(root.t * 0.5 + ph)
            x: modelData[1] * (root.width - width) + Math.sin(root.t * sp * 0.4 + ph) * 12
            y: root.glyphDrift > 0
               ? ((modelData[2] * root.height - root.t * sp * root.glyphDrift) % (root.height + height)
                  + root.height + height) % (root.height + height) - height
               : modelData[2] * (root.height - height) + Math.cos(root.t * sp * 0.5 + ph) * 16
        }
    }
}
