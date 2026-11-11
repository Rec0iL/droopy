import QtQuick

// A small pixel-art "app icon" that assembles cell by cell - the thing we extract.
Item {
    id: icon
    property real cellSize: 10
    property bool excited: false
    property real assembled: 1.0            // 0 = empty grid, 1 = full icon

    // 11x11 bitmap: 0 empty, 1 blue, 2 cyan, 3 amber, 4 white
    readonly property var bitmap: [
        [0,0,1,1,1,1,1,1,1,0,0],
        [0,1,1,1,1,1,1,1,1,1,0],
        [1,1,1,1,1,3,1,1,1,1,1],
        [1,1,1,1,3,3,3,1,1,1,1],
        [1,1,3,3,3,3,3,3,3,1,1],
        [1,1,1,3,3,4,3,3,1,1,1],
        [1,1,1,1,3,3,3,1,1,1,1],
        [1,1,1,3,3,1,3,3,1,1,1],
        [1,1,3,3,1,1,1,3,3,1,1],
        [0,2,2,2,2,2,2,2,2,2,0],
        [0,0,2,2,2,2,2,2,2,0,0]
    ]
    readonly property var palette: ["transparent", Theme.accent, Theme.accent2, Theme.warm, "white"]

    width: cellSize * 11
    height: cellSize * 11

    Behavior on assembled { NumberAnimation { duration: 700; easing.type: Easing.OutCubic } }

    Grid {
        columns: 11
        spacing: 0
        Repeater {
            model: 121
            delegate: Rectangle {
                required property int index
                readonly property int v: icon.bitmap[Math.floor(index / 11)][index % 11]
                readonly property real order: ((index * 37) % 121) / 121   // pseudo-random assembly order
                width: icon.cellSize; height: icon.cellSize
                radius: 1.5
                color: icon.palette[v]
                opacity: v === 0 ? 0 : (icon.assembled > order ? 0.95 : 0.12)
                Behavior on opacity { NumberAnimation { duration: 180 } }
                scale: 0.88
            }
        }
    }
}
