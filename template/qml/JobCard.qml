import QtQuick
import QtQuick.Layouts

// One row in the queue.
Item {
    id: card
    required property int jobId
    required property string name
    required property string source
    required property string sourceDir
    required property string output
    required property real progress
    required property string status
    required property string message
    required property int index

    width: ListView.view ? ListView.view.width : 400
    height: 84

    readonly property var labels: ({
        "queued": "QUEUED", "working": "__WORKING_LABEL__", "done": "DONE",
        "error": "FAILED", "skipped": "SKIPPED"
    })
    readonly property var faces: ({
        "queued": "(˘ω˘)ᶻᶻ", "working": "ᕕ( ᐛ )ᕗ", "done": "(◕‿◕)♡",
        "error": "(╥﹏╥)", "skipped": "(・_・;)"
    })
    readonly property bool finished: status === "done" || status === "error" || status === "skipped"

    // pop-in
    opacity: 0
    scale: 0.94
    Component.onCompleted: appear.start()
    ParallelAnimation {
        id: appear
        NumberAnimation { target: card; property: "opacity"; to: 1; duration: 320 }
        NumberAnimation { target: card; property: "scale"; to: 1; duration: 420; easing.type: Easing.OutBack }
    }

    Rectangle {
        anchors.fill: parent
        anchors.bottomMargin: 8
        radius: 20
        color: Theme.glass(0.52)
        border.width: 1
        border.color: card.status === "error" ? Qt.rgba(0.94, 0.36, 0.48, 0.8) : Theme.glassBorder

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 16; anchors.rightMargin: 12
            spacing: 14

            // droopy:feature mascot_kaomoji begin
            Text {
                Layout.preferredWidth: 92
                horizontalAlignment: Text.AlignHCenter
                text: card.faces[card.status] ?? ""
                font.pixelSize: 21
                font.family: Theme.font
                color: card.status === "error" ? Theme.danger : Theme.text
                SequentialAnimation on y {
                    running: card.status === "working"
                    loops: Animation.Infinite
                    NumberAnimation { from: 0; to: -3; duration: 260; easing.type: Easing.OutQuad }
                    NumberAnimation { from: -3; to: 0; duration: 260; easing.type: Easing.InQuad }
                }
            }
            // droopy:feature mascot_kaomoji end
            // droopy:feature status_chip begin
            Rectangle {   // status chip
                Layout.preferredWidth: 78; Layout.preferredHeight: 24
                radius: 6
                color: card.status === "done" ? Qt.rgba(0.2, 0.7, 0.5, 0.18)
                     : card.status === "error" ? Qt.rgba(0.9, 0.3, 0.4, 0.18)
                     : card.status === "working" ? Qt.rgba(0.2, 0.6, 0.9, 0.22)
                     : Theme.field
                border.width: 1
                border.color: card.status === "done" ? Theme.mint : card.status === "error" ? Theme.danger
                            : card.status === "working" ? Theme.accent2 : Theme.fieldBorder
                Text {
                    anchors.centerIn: parent
                    text: card.labels[card.status] ?? ""
                    font.pixelSize: 11
                    font.family: Theme.mono
                    font.weight: Font.Bold
                    font.letterSpacing: 1
                    color: card.status === "done" ? Theme.mint : card.status === "error" ? Theme.danger
                         : card.status === "working" ? Theme.accent2 : Theme.textSoft
                    SequentialAnimation on opacity {
                        running: card.status === "working"
                        loops: Animation.Infinite
                        NumberAnimation { to: 0.45; duration: 500 }
                        NumberAnimation { to: 1.0; duration: 500 }
                    }
                }
            }
            // droopy:feature status_chip end

            // droopy:feature previews begin
            Image {   // thumbnail of the result when it is an image
                Layout.preferredWidth: 40; Layout.preferredHeight: 40
                visible: card.status === "done" && /\.(png|jpe?g|webp|gif|bmp|svg)$/i.test(card.output)
                source: visible ? "file://" + card.output : ""
                fillMode: Image.PreserveAspectFit
                smooth: true
                asynchronous: true
                sourceSize.width: 80; sourceSize.height: 80
            }
            // droopy:feature previews end

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 5
                Text {
                    Layout.fillWidth: true
                    text: card.name
                    elide: Text.ElideMiddle
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                    font.family: Theme.font
                    color: Theme.text
                }
                GlowBar {
                    Layout.fillWidth: true
                    value: card.status === "queued" ? 0 : card.progress
                    active: card.status === "working"
                    from: card.status === "error" ? "#ff9ab3" : card.status === "done" ? Theme.mint : Theme.accent
                    to: card.status === "error" ? Theme.danger : card.status === "done" ? "#8fe9d3" : Theme.accent2
                }
                Text {
                    Layout.fillWidth: true
                    text: card.finished
                          ? card.message + (card.output ? "  ·  → " + card.output : "")
                          : card.message + "  ·  from " + card.sourceDir
                    elide: Text.ElideMiddle
                    font.pixelSize: 12
                    font.family: Theme.font
                    color: card.status === "error" ? Theme.danger : Theme.textSoft
                }
            }

            Text {
                Layout.preferredWidth: 42
                horizontalAlignment: Text.AlignRight
                text: card.status === "done" ? "✓" : card.status === "error" ? "!" :
                      card.status === "skipped" ? "–" : Math.round(card.progress * 100) + "%"
                font.pixelSize: 15
                font.weight: Font.Bold
                font.family: Theme.font
                color: card.status === "done" ? Theme.mint : card.status === "error" ? Theme.danger : Theme.textSoft
            }

            Item {   // reveal in file manager
                Layout.preferredWidth: 30; Layout.preferredHeight: 30
                visible: card.output !== "" || card.sourceDir !== ""
                Rectangle {
                    anchors.fill: parent; radius: 15
                    color: Theme.glass(revealMa.containsMouse ? 0.8 : 0.4)
                }
                Text { anchors.centerIn: parent; text: "↗"; font.pixelSize: 16; color: Theme.text }
                MouseArea {
                    id: revealMa; anchors.fill: parent; hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: backend.reveal(card.output !== "" ? card.output : card.source)
                }
            }
            Item {   // remove
                Layout.preferredWidth: 30; Layout.preferredHeight: 30
                opacity: card.status === "working" ? 0.3 : 1
                Rectangle {
                    anchors.fill: parent; radius: 15
                    color: Theme.glass(rmMa.containsMouse ? 0.8 : 0.4)
                }
                Text { anchors.centerIn: parent; text: "✕"; font.pixelSize: 13; color: Theme.text }
                MouseArea {
                    id: rmMa; anchors.fill: parent; hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: backend.removeJob(card.jobId)
                }
            }
        }
    }
}
