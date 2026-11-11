import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    id: win
    visible: true
    width: 900
    height: 680
    minimumWidth: 700
    minimumHeight: 560
    title: "__APP_NAME__"
    color: Theme.windowBg

    readonly property var s: backend.settings
    Binding { target: Theme; property: "mode"; value: win.s.theme }
    readonly property bool hasJobs: backend.jobCount > 0

    // --- background ------------------------------------------------------------
    __BACKGROUND_COMPONENT__ {
        id: bg
        anchors.fill: parent
        lowPower: win.s.lowPower
        energy: drop.containsDrag ? 1.0 : backend.busy ? 0.55 : 0.0
    }

    // --- whole window accepts drops -------------------------------------------
    DropArea {
        id: drop
        anchors.fill: parent
        onDropped: (ev) => {
            if (ev.hasUrls) backend.addUrls(ev.urls.map(u => u.toString()))
        }
    }

    FileDialog {
        id: filePicker
        title: "__FILE_DIALOG_TITLE__"
        fileMode: FileDialog.OpenFiles
        nameFilters: ["__FILE_FILTER__", "All files (*)"]
        currentFolder: win.s.lastDir !== "" ? "file://" + win.s.lastDir : ""
        onAccepted: backend.addUrls(selectedFiles.map(u => u.toString()))
    }
    FolderDialog {
        id: folderPicker
        title: "Choose a folder"
        currentFolder: win.s.lastDir !== "" ? "file://" + win.s.lastDir : ""
        onAccepted: backend.addUrls([selectedFolder.toString()])
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 26
        spacing: 16

        // ---- header ----------------------------------------------------------
        RowLayout {
            Layout.fillWidth: true
            spacing: 14

            // droopy:feature mascot_pixel begin
            PixelIcon {
                cellSize: 3.4
                Layout.alignment: Qt.AlignVCenter
                // assembles cell by cell while working, stays whole otherwise, half-built on error
                assembled: backend.mascotState === "working" ? workAsm.value
                         : backend.mascotState === "error" ? 0.55 : 1.0
                QtObject {
                    id: workAsm
                    property real value: 0.2
                    SequentialAnimation on value {
                        loops: Animation.Infinite
                        running: backend.mascotState === "working"
                        NumberAnimation { from: 0.15; to: 1.0; duration: 1100; easing.type: Easing.OutCubic }
                        PauseAnimation { duration: 350 }
                    }
                }
                transformOrigin: Item.Center
                scale: backend.busy ? 1.06 : 1.0
                Behavior on scale { NumberAnimation { duration: 250 } }
            }
            // droopy:feature mascot_pixel end
            // droopy:feature mascot_kaomoji begin
            Text {
                readonly property var faces: ({ "idle": "(◕ᴗ◕✿)", "working": "ᕕ( ᐛ )ᕗ", "done": "٩(◕‿◕)۶", "error": "(╥﹏╥)" })
                text: faces[backend.mascotState]
                font.pixelSize: 34
                font.family: Theme.font
                color: "white"
                style: Text.Outline
                styleColor: Theme.titleOutline
                transformOrigin: Item.Center
                SequentialAnimation on scale {
                    loops: Animation.Infinite
                    running: true
                    NumberAnimation { to: backend.busy ? 1.14 : 1.05; duration: backend.busy ? 280 : 1200; easing.type: Easing.InOutSine }
                    NumberAnimation { to: 1.0; duration: backend.busy ? 280 : 1200; easing.type: Easing.InOutSine }
                }
            }
            // droopy:feature mascot_kaomoji end
            // droopy:feature mascot_glyph begin
            Image {
                source: "../packaging/__APP_ID__.svg"
                sourceSize.width: 40; sourceSize.height: 40
                Layout.alignment: Qt.AlignVCenter
                transformOrigin: Item.Center
                scale: backend.busy ? 1.06 : 1.0
                Behavior on scale { NumberAnimation { duration: 250 } }
            }
            // droopy:feature mascot_glyph end
            Text {
                text: "__APP_NAME__"
                font.pixelSize: 30
                font.weight: Font.Bold
                font.family: Theme.font
                color: Theme.dark ? "white" : Theme.text
                style: Text.Outline
                styleColor: Theme.dark ? Theme.titleOutline : Qt.rgba(1, 1, 1, 0.6)
            }
            Item { Layout.fillWidth: true }

            // droopy:header begin   (quick toggles for the 1-2 most used options)
            // droopy:header end
            PillButton {
                label: Theme.dark ? "☀" : "☾"
                fontSize: 18
                implicitWidth: 44
                onClicked: backend.setSetting("theme", Theme.dark ? "light" : "dark")
            }
            // droopy:feature history begin
            PillButton { label: "History"; onClicked: history.open() }
            // droopy:feature history end
            PillButton { label: "⚙  Settings"; onClicked: settings.open() }
        }

        // ---- main area -------------------------------------------------------
        Item {
            id: area
            Layout.fillWidth: true
            Layout.fillHeight: true

            GlassCard {
                id: zoneCard
                source: bg
                tintAlpha: win.hasJobs ? 0.34 : 0.22
                blurAmount: 0.45
                blurMax: 24
                width: parent.width
                height: win.hasJobs ? 120 : area.height
                Behavior on height { NumberAnimation { duration: 450; easing.type: Easing.OutCubic } }

                DropZone {
                    anchors.fill: parent
                    hovering: drop.containsDrag
                    compact: win.hasJobs
                    onBrowseFiles: filePicker.open()
                    onBrowseFolder: folderPicker.open()
                }
            }

            ListView {
                id: queue
                anchors.top: zoneCard.bottom
                anchors.topMargin: 14
                anchors.bottom: footer.top
                anchors.bottomMargin: 6
                width: parent.width
                clip: true
                model: backend.jobs
                visible: win.hasJobs
                spacing: 0
                boundsBehavior: Flickable.StopAtBounds
                delegate: JobCard {}
                add: Transition { NumberAnimation { property: "opacity"; to: 1; duration: 250 } }
                displaced: Transition { NumberAnimation { properties: "y"; duration: 250; easing.type: Easing.OutCubic } }
                remove: Transition { NumberAnimation { property: "opacity"; to: 0; duration: 200 } }
            }

            // ---- footer: overall progress ------------------------------------
            Item {
                id: footer
                anchors.bottom: parent.bottom
                width: parent.width
                height: win.hasJobs ? 52 : 0
                visible: win.hasJobs
                opacity: win.hasJobs ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 300 } }

                Rectangle {
                    anchors.fill: parent
                    radius: 26
                    color: Theme.glass(0.5)
                    border.width: 1
                    border.color: Theme.glassBorder
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 20
                    anchors.rightMargin: 8
                    spacing: 14
                    Text {
                        text: backend.doneCount + " / " + backend.jobCount
                        font.pixelSize: 15; font.weight: Font.Bold; font.family: Theme.font
                        color: Theme.text
                    }
                    GlowBar {
                        Layout.fillWidth: true
                        implicitHeight: 14
                        value: backend.overallProgress
                        active: backend.busy
                        from: Theme.warm
                        to: Theme.accent
                    }
                    Text {
                        text: Math.round(backend.overallProgress * 100) + "%"
                        font.pixelSize: 15; font.weight: Font.Bold; font.family: Theme.font
                        color: Theme.textSoft
                        Layout.preferredWidth: 44
                        horizontalAlignment: Text.AlignRight
                    }
                    // droopy:feature retry begin
                    PillButton { label: "Retry failed"; fontSize: 13; implicitHeight: 34; onClicked: backend.retryFailed() }
                    // droopy:feature retry end
                    PillButton { label: "Clear finished"; fontSize: 13; implicitHeight: 34; onClicked: backend.clearFinished() }
                }
            }
        }
    }

    // ---- toast -----------------------------------------------------------------
    Rectangle {
        id: toast
        property alias text: toastText.text
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height - 90 + (shown ? 0 : 30)
        opacity: shown ? 1 : 0
        property bool shown: false
        width: toastText.implicitWidth + 40
        height: 42
        radius: 21
        color: Qt.rgba(0.12, 0.22, 0.45, 0.92)
        Behavior on opacity { NumberAnimation { duration: 250 } }
        Behavior on y { NumberAnimation { duration: 300; easing.type: Easing.OutBack } }
        Text {
            id: toastText
            anchors.centerIn: parent
            color: "white"; font.pixelSize: 14; font.family: Theme.font
        }
        Timer { id: toastTimer; interval: 3500; onTriggered: toast.shown = false }
    }
    Connections {
        target: backend
        function onToast(msg) { toast.text = msg; toast.shown = true; toastTimer.restart() }
    }

    // ---- dialogs ---------------------------------------------------------------
    // droopy:feature delete begin
    DeleteDialog { id: deleteDlg; bgSource: bg }
    // droopy:feature delete end
    SettingsDialog { id: settings; objectName: "settingsDlg"; bgSource: bg }
    // droopy:feature history begin
    HistoryDialog { id: history; bgSource: bg }
    // droopy:feature history end
}
