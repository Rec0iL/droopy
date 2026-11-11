import QtQuick
import QtQuick.Controls.Basic

// Pill-styled stepped slider.
Slider {
    id: control
    implicitWidth: 200
    implicitHeight: 28
    snapMode: Slider.SnapAlways

    background: Item {
        x: control.leftPadding
        y: control.topPadding + control.availableHeight / 2 - height / 2
        implicitWidth: 200
        implicitHeight: 10
        width: control.availableWidth
        height: 10

        Rectangle {
            anchors.fill: parent
            radius: 5
            color: Theme.field
            border.width: 1
            border.color: Theme.fieldBorder
        }
        Rectangle {
            width: control.visualPosition * parent.width
            height: parent.height
            radius: 5
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: Theme.pink }
                GradientStop { position: 1; color: Theme.lavender }
            }
        }
        // step ticks
        Repeater {
            model: Math.round((control.to - control.from) / control.stepSize) + 1
            delegate: Rectangle {
                required property int index
                width: 4; height: 4; radius: 2
                x: index / (Math.round((control.to - control.from) / control.stepSize)) * (parent.width - width)
                y: parent.height / 2 - height / 2
                color: Qt.rgba(1, 1, 1, 0.7)
                visible: index > 0 && index < Math.round((control.to - control.from) / control.stepSize)
            }
        }
    }

    handle: Rectangle {
        x: control.leftPadding + control.visualPosition * (control.availableWidth - width)
        y: control.topPadding + control.availableHeight / 2 - height / 2
        width: 24; height: 24; radius: 12
        color: "white"
        border.width: 2
        border.color: Theme.pink
        scale: control.pressed ? 1.18 : (control.hovered ? 1.08 : 1.0)
        Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutBack } }
    }
}
