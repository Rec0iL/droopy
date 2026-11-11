import QtQuick
import QtQuick.Shapes

// Big dashed drop target. Shrinks to a compact strip when the queue has items.
Item {
    id: zone
    property bool hovering: false
    property bool compact: false
    signal browseFiles()
    signal browseFolder()

    readonly property int pad: 14

    Shape {
        anchors.fill: parent
        anchors.margins: zone.pad
        ShapePath {
            strokeColor: zone.hovering ? "white" : Qt.rgba(1, 1, 1, 0.85)
            strokeWidth: zone.hovering ? 4 : 3
            fillColor: zone.hovering ? Qt.rgba(1, 1, 1, 0.22) : "transparent"
            strokeStyle: ShapePath.DashLine
            dashPattern: [3, 3]
            capStyle: ShapePath.RoundCap
            PathRectangle {
                x: 0; y: 0
                width: zone.width - zone.pad * 2
                height: zone.height - zone.pad * 2
                radius: 22
            }
            NumberAnimation on dashOffset {
                from: 0; to: 6
                duration: zone.hovering ? 500 : 1800
                loops: Animation.Infinite
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: zone.browseFiles()
    }

    // ---- big layout ----------------------------------------------------------
    Column {
        anchors.centerIn: parent
        spacing: 10
        visible: !zone.compact
        opacity: zone.compact ? 0 : 1
        Behavior on opacity { NumberAnimation { duration: 250 } }

        // droopy:feature mascot_pixel begin
        PixelIcon {
            anchors.horizontalCenter: parent.horizontalCenter
            cellSize: 11
            assembled: zone.hovering ? 1.0 : idleAsm.value
            SequentialAnimation on y {
                loops: Animation.Infinite
                running: !zone.compact
                NumberAnimation { to: -6; duration: 1400; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0; duration: 1400; easing.type: Easing.InOutSine }
            }
            scale: zone.hovering ? 1.12 : 1.0
            Behavior on scale { NumberAnimation { duration: 300; easing.type: Easing.OutBack } }
        }
        QtObject {
            id: idleAsm
            property real value: 0.45
            SequentialAnimation on value {
                loops: Animation.Infinite
                running: !zone.compact && !zone.hovering
                PauseAnimation { duration: 1200 }
                NumberAnimation { to: 1.0; duration: 1600; easing.type: Easing.OutCubic }
                PauseAnimation { duration: 2200 }
                NumberAnimation { to: 0.35; duration: 900; easing.type: Easing.InCubic }
            }
        }
        // droopy:feature mascot_pixel end
        // droopy:feature mascot_kaomoji begin
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: zone.hovering ? "ヽ(>∀<☆)ノ" : "(๑˃ᴗ˂)ﻭ"
            font.pixelSize: 64
            font.family: Theme.font
            color: "white"
            style: Text.Outline
            styleColor: Theme.titleOutline
            SequentialAnimation on y {
                loops: Animation.Infinite
                running: !zone.compact
                NumberAnimation { to: -8; duration: 900; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0; duration: 900; easing.type: Easing.InOutSine }
            }
            scale: zone.hovering ? 1.15 : 1.0
            Behavior on scale { NumberAnimation { duration: 300; easing.type: Easing.OutBack } }
        }
        // droopy:feature mascot_kaomoji end
        // droopy:feature mascot_glyph begin
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: zone.hovering ? "⬇" : "__DROP_GLYPH__"
            font.pixelSize: 64
            color: "white"
            style: Text.Outline
            styleColor: Theme.titleOutline
            SequentialAnimation on y {
                loops: Animation.Infinite
                running: !zone.compact
                NumberAnimation { to: -6; duration: 1400; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0; duration: 1400; easing.type: Easing.InOutSine }
            }
            scale: zone.hovering ? 1.15 : 1.0
            Behavior on scale { NumberAnimation { duration: 300; easing.type: Easing.OutBack } }
        }
        // droopy:feature mascot_glyph end
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: zone.hovering ? "__DROP_HOVER__" : "__DROP_TITLE__"
            font.pixelSize: 28
            font.weight: Font.Bold
            font.family: Theme.font
            color: Theme.text
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "__DROP_HINT__  ·  or click to browse"
            font.pixelSize: 14
            font.family: Theme.font
            color: Theme.textSoft
        }
        PillButton {
            anchors.horizontalCenter: parent.horizontalCenter
            label: "Browse folder…"
            onClicked: zone.browseFolder()
        }
    }

    // ---- compact layout ------------------------------------------------------
    Row {
        anchors.centerIn: parent
        spacing: 14
        visible: zone.compact
        opacity: zone.compact ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 250 } }
        // droopy:feature mascot_pixel begin
        PixelIcon {
            anchors.verticalCenter: parent.verticalCenter
            cellSize: 4
            assembled: zone.hovering ? 1.0 : 0.6
        }
        // droopy:feature mascot_pixel end
        // droopy:feature mascot_kaomoji begin
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: zone.hovering ? "ヽ(>∀<☆)ノ" : "(๑˃ᴗ˂)ﻭ"
            font.pixelSize: 26; font.family: Theme.font; color: "white"
            style: Text.Outline; styleColor: Theme.titleOutline
        }
        // droopy:feature mascot_kaomoji end
        // droopy:feature mascot_glyph begin
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: zone.hovering ? "⬇" : "__DROP_GLYPH__"
            font.pixelSize: 26; color: "white"
            style: Text.Outline; styleColor: Theme.titleOutline
        }
        // droopy:feature mascot_glyph end
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: zone.hovering ? "Release to add more" : "Drop more files, or click to browse"
            font.pixelSize: 16; font.weight: Font.DemiBold; font.family: Theme.font
            color: Theme.text
        }
        PillButton {
            anchors.verticalCenter: parent.verticalCenter
            label: "Folder…"
            onClicked: zone.browseFolder()
        }
    }
}
