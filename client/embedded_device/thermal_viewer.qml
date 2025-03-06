import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Window {
    id: mainWindow
    visible: true
    width: 1024
    height: 768
    title: qsTr("Thermal Camera Viewer")

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        // Thermal Image Display
        Rectangle {
            id: imageContainer
            Layout.fillWidth: true
            Layout.fillHeight: true
            border.color: "lightgray"
            border.width: 2

            Image {
                id: thermalImage
                anchors.fill: parent
                fillMode: Image.PreserveAspectFit
                cache: false
            }

            // Loading Indicator
            BusyIndicator {
                anchors.centerIn: parent
                running: !streamToggle.checked
                visible: running
            }
        }

        // Control Panel
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: 10
            spacing: 10

            // Stream Toggle Switch
            Switch {
                id: streamToggle
                text: checked ? qsTr("Stop Stream") : qsTr("Start Stream")
                checked: false

                onCheckedChanged: {
                    thermalController.toggle_stream()
                }
            }

            // Stream Status
            Label {
                text: streamToggle.checked ? qsTr("Stream Running") : qsTr("Stream Stopped")
                color: streamToggle.checked ? "green" : "red"
            }

            // Spacer
            Item {
                Layout.fillWidth: true
            }

            // Additional Controls (Placeholder for future features)
            Button {
                text: qsTr("Settings")
                onClicked: {
                    // Future: Open settings dialog
                }
            }
        }
    }

    // Connections to Python Controller
    Connections {
        target: thermalController

        function onFrameUpdated(frameBase64) {
            thermalImage.source = frameBase64
        }

        function onStreamStateChanged(isRunning) {
            streamToggle.checked = isRunning
        }
    }
}