import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts

// "Delete the original?" prompt, shown after a successful job.
Popup {
    id: dlg
    property Item bgSource: null
    readonly property var info: backend.pendingDelete

    parent: Overlay.overlay
    anchors.centerIn: parent
    modal: true
    dim: true
    closePolicy: Popup.NoAutoClose
    visible: backend.hasPendingDelete
    padding: 0
    width: Math.min(520, (parent ? parent.width : 520) - 40)
    height: col.implicitHeight + 56

    Overlay.modal: Rectangle { color: Qt.rgba(0.10, 0.18, 0.40, 0.35) }
    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 200 }
            NumberAnimation { property: "scale"; from: 0.85; to: 1; duration: 350; easing.type: Easing.OutBack }
        }
    }
    exit: Transition { NumberAnimation { property: "opacity"; to: 0; duration: 150 } }

    background: Item {}
    contentItem: GlassCard {
        source: dlg.bgSource
        tintAlpha: 1.0
        blurred: false

        ColumnLayout {
            id: col
            anchors.fill: parent
            anchors.margins: 28
            spacing: 14

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "__DONE_TITLE__"
                font.pixelSize: 22; font.weight: Font.Bold; font.family: Theme.font; color: Theme.text
            }
            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WrapAnywhere
                text: "Delete the original?\n" + dlg.info.source
                font.pixelSize: 14; font.family: Theme.font; color: Theme.textSoft
            }
            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WrapAnywhere
                text: "→ " + dlg.info.output
                font.pixelSize: 12; font.family: Theme.font; color: Theme.mint
            }
            Text {
                visible: dlg.info.count > 1
                Layout.alignment: Qt.AlignHCenter
                text: (dlg.info.count - 1) + " more waiting"
                font.pixelSize: 12; font.family: Theme.font; color: Theme.textSoft
            }
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 10
                PillButton { label: "Keep"; onClicked: backend.answerDelete("no") }
                PillButton {
                    primary: true
                    label: backend.settings.useTrash ? "Move to trash" : "Delete"
                    onClicked: backend.answerDelete("yes")
                }
            }
            RowLayout {
                visible: dlg.info.count > 1
                Layout.alignment: Qt.AlignHCenter
                spacing: 10
                PillButton { label: "Keep all"; fontSize: 12; implicitHeight: 32; onClicked: backend.answerDelete("noAll") }
                PillButton { label: "Delete all"; danger: true; fontSize: 12; implicitHeight: 32; onClicked: backend.answerDelete("yesAll") }
            }
        }
    }
}
