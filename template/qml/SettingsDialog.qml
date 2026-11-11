import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs

Popup {
    id: dlg
    property Item bgSource: null
    readonly property var s: backend.settings

    parent: Overlay.overlay
    anchors.centerIn: parent
    modal: true
    dim: true
    padding: 0
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
    width: Math.min(560, (parent ? parent.width : 560) - 40)
    height: Math.min(col.implicitHeight + 64, (parent ? parent.height : 700) - 40)

    Overlay.modal: Rectangle { color: Qt.rgba(0.10, 0.18, 0.40, 0.35) }
    enter: Transition {
        ParallelAnimation {
            NumberAnimation { property: "opacity"; from: 0; to: 1; duration: 200 }
            NumberAnimation { property: "scale"; from: 0.9; to: 1; duration: 320; easing.type: Easing.OutBack }
        }
    }
    exit: Transition { NumberAnimation { property: "opacity"; to: 0; duration: 150 } }

    FolderDialog {
        id: outPicker
        title: "Choose output folder"
        onAccepted: {
            backend.setSetting("customDir", backend.toLocalPath(selectedFolder.toString()))
            backend.setSetting("outputMode", "custom")
        }
    }

    background: Item {}
    contentItem: GlassCard {
        source: dlg.bgSource
        tintAlpha: 1.0
        blurred: false

        Flickable {
            anchors.fill: parent
            contentHeight: col.implicitHeight + 56
            clip: true
            boundsBehavior: Flickable.StopAtBounds

        ColumnLayout {
            id: col
            width: parent.width - 56
            x: 28; y: 28
            spacing: 16

            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: "Settings"
                    font.pixelSize: 24; font.weight: Font.Bold; font.family: Theme.font; color: Theme.text
                    Layout.fillWidth: true
                }
                PillButton { label: "Done"; primary: true; onClicked: dlg.close() }
            }

            component Row_: RowLayout {
                id: rr
                property string title: ""
                property string hint: ""
                default property alias controls: holder.data
                Layout.fillWidth: true
                Layout.preferredWidth: 100000
                spacing: 12
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1
                    Text { text: rr.title; font.pixelSize: 15; font.weight: Font.DemiBold
                           font.family: Theme.font; color: Theme.text }
                    Text { visible: rr.hint !== ""; text: rr.hint; font.pixelSize: 12
                           font.family: Theme.font; color: Theme.textSoft; wrapMode: Text.WordWrap
                           Layout.fillWidth: true }
                }
                Row { id: holder; spacing: 8 }
            }

            Row_ {
                title: "Appearance"
                hint: dlg.s.theme === "auto" ? "Following your system theme" : ""
                Segmented {
                    model: ["Auto", "Light", "Dark"]
                    currentIndex: ["auto", "light", "dark"].indexOf(dlg.s.theme)
                    onActivated: (i) => backend.setSetting("theme", ["auto", "light", "dark"][i])
                }
            }

            // droopy:options begin   (one Row_ per exposed option - see references/options-mapping.md)
            // droopy:options end

            Row_ {
                title: "Save to"
                hint: dlg.s.outputMode === "custom" && dlg.s.customDir !== "" ? dlg.s.customDir
                                                                               : "Right next to the original"
                Segmented {
                    model: ["Source folder", "Custom"]
                    currentIndex: dlg.s.outputMode === "custom" ? 1 : 0
                    onActivated: (i) => {
                        if (i === 1 && dlg.s.customDir === "") outPicker.open()
                        else backend.setSetting("outputMode", i === 1 ? "custom" : "source")
                    }
                }
                PillButton { visible: dlg.s.outputMode === "custom"; label: "Browse…"; onClicked: outPicker.open() }
            }
            Row_ {
                title: "If the output already exists"
                Segmented {
                    model: ["Rename", "Overwrite"]
                    currentIndex: dlg.s.overwrite === "overwrite" ? 1 : 0
                    onActivated: (i) => backend.setSetting("overwrite", i === 1 ? "overwrite" : "rename")
                }
            }
            // droopy:feature delete begin
            Row_ {
                title: "Delete original after success"
                Segmented {
                    model: ["Ask", "Never", "Always"]
                    currentIndex: ["ask", "never", "always"].indexOf(dlg.s.deleteMode)
                    onActivated: (i) => backend.setSetting("deleteMode", ["ask", "never", "always"][i])
                }
            }
            Row_ {
                title: "Move to trash instead of deleting"
                PillSwitch { checked: dlg.s.useTrash; onToggled: (v) => backend.setSetting("useTrash", v) }
            }
            // droopy:feature delete end
            Row_ {
                title: "Low-power background"
                hint: "Calmer animation, no glow - easier on the GPU."
                PillSwitch { checked: dlg.s.lowPower; onToggled: (v) => backend.setSetting("lowPower", v) }
            }
        }
        }
    }
}
