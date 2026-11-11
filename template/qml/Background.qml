import QtQuick
import QtQuick.Effects

// Animated background: GLSL shader (shaders/bg.frag) + a floating glyph layer.
Item {
    id: root

    property real energy: 0          // 0 calm .. 1 excited (smoothed)
    property bool lowPower: false
    property real t: 0               // animation clock, speeds up with energy

    Behavior on energy { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }

    FrameAnimation {
        running: root.visible
        onTriggered: root.t += frameTime * (root.lowPower ? 0.5 : 1.0) * (1.0 + root.energy * 1.2)
    }

    ShaderEffect {
        anchors.fill: parent
        property real time: root.t
        property size resolution: Qt.size(width, height)
        property real energy: root.energy
        property real quality: root.lowPower ? 0.0 : 1.0
        property real night: Theme.night
        fragmentShader: "../shaders/bg.frag.qsb"
    }

    // droopy:glyphs begin   (edited per app in the look phase)
    // text, x, y, size, speed, phase  - set `glyphs: []` for none
    readonly property var glyphs: [
        ["▣", 0.08, 0.14, 22, 0.55, 0.0], ["◈", 0.82, 0.10, 24, 0.45, 1.3],
        ["✦", 0.46, 0.06, 20, 0.60, 2.1], ["⬡", 0.90, 0.40, 22, 0.50, 3.4],
        ["▦", 0.05, 0.46, 22, 0.40, 4.2], ["◧", 0.70, 0.72, 24, 0.55, 5.0],
        ["▤", 0.20, 0.82, 22, 0.48, 0.7], ["◇", 0.50, 0.90, 20, 0.52, 1.9]
    ]
    readonly property string glyphFont: Theme.mono
    readonly property real glyphOpacity: 0.35
    readonly property real glyphDrift: 18        // px/s upward drift; 0 = hover in place
    // droopy:glyphs end

    Repeater {
        model: root.glyphs
        delegate: Text {
            required property var modelData
            readonly property real sp: modelData[4] * (root.lowPower ? 0.5 : 1)
            readonly property real ph: modelData[5]
            text: modelData[0]
            font.pixelSize: modelData[3]
            font.family: root.glyphFont
            color: Theme.dataText
            opacity: root.glyphOpacity + 0.20 * Math.sin(root.t * 0.5 + ph) + 0.15 * root.energy
            transformOrigin: Item.Center
            x: modelData[1] * (root.width - width) + Math.sin(root.t * sp * 0.4 + ph) * 12
            y: root.glyphDrift > 0
               ? ((modelData[2] * root.height - root.t * sp * root.glyphDrift * (1 + root.energy)) % (root.height + height)
                  + root.height + height) % (root.height + height) - height
               : modelData[2] * (root.height - height) + Math.cos(root.t * sp * 0.5 + ph * 1.3) * 16
            rotation: root.glyphDrift > 0 ? 0 : Math.sin(root.t * sp * 0.7 + ph) * (4 + root.energy * 8)

            layer.enabled: !root.lowPower
            layer.effect: MultiEffect {
                shadowEnabled: true
                shadowColor: Theme.glyphGlow
                shadowBlur: 0.8
                shadowOpacity: 0.45
                shadowVerticalOffset: 0
                shadowHorizontalOffset: 0
            }
        }
    }
}
