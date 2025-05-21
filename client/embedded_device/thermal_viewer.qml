import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Window {
    id: mainWindow
    width: 1024
    height: 768
    visible: true
    title: "Thermal Viewer"
    color: "#f0f0f0"

    // Store temperature values
    property real minTemp: 0.0
    property real maxTemp: 0.0
    property real avgTemp: 0.0
    property bool isStreaming: false
    property bool settingsPanelOpen: false
    property bool showTempWarning: enableTempWarning.checked && maxTemp > 100.0

    // Main layout
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 10

        // Temperature information panel
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "#e0e0e0"
            radius: 5
            border.color: "#cccccc"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 20

                // Min temperature
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "lightgray"
                    radius: 5
                    border.color: "lightgray"
                    border.width: 1

                    Column {
                        anchors.centerIn: parent
                        spacing: 5
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "Min Temperature"
                            font.pixelSize: 14
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: isStreaming ? minTemp.toFixed(2) + "°C" : "---"
                            font.pixelSize: 18
                            font.bold: true
                        }
                    }
                }

                // Max temperature
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: showTempWarning ? "#ffebee" : "lightgray"
                    radius: 5
                    border.color: showTempWarning ? "#f44336" : "lightgray"
                    border.width: showTempWarning ? 2 : 1

                    Column {
                        anchors.centerIn: parent
                        spacing: 5
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "Max Temperature"
                            font.pixelSize: 14
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: isStreaming ? maxTemp.toFixed(2) + "°C" : "---"
                            font.pixelSize: 18
                            font.bold: true
                            color: showTempWarning ? "#d32f2f" : "black"
                        }
                    }
                }

                // Average temperature
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "lightgray"
                    radius: 5
                    border.color: "lightgray"
                    border.width: 1

                    Column {
                        anchors.centerIn: parent
                        spacing: 5
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: "Avg Temperature"
                            font.pixelSize: 14
                        }
                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            text: isStreaming ? avgTemp.toFixed(2) + "°C" : "---"
                            font.pixelSize: 18
                            font.bold: true
                        }
                    }
                }
            }
        }

        // Thermal image display with high temperature warning
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            border.color: "lightgray"
            border.width: 2

            // Display status text when not streaming
            Text {
                anchors.centerIn: parent
                text: ""
                color: "#888888"
                font.pixelSize: 24
                visible: !isStreaming || thermalImage.source == ""
            }

            // Thermal image
            Image {
                id: thermalImage
                anchors.fill: parent
                fillMode: Image.PreserveAspectFit
                cache: false
                source: ""
            }

            // High temperature warning message
            Rectangle {
                id: warningBox
                visible: showTempWarning && isStreaming
                anchors {
                    top: parent.top
                    right: parent.right
                    margins: 10
                }
                width: warningText.width + 20
                height: warningText.height + 10
                color: "#ffcdd2"
                border.color: "#f44336"
                border.width: 2
                radius: 5
                
                Text {
                    id: warningText
                    anchors.centerIn: parent
                    text: "WARNING: Temperature above 100°C!"
                    color: "#d32f2f"
                    font.bold: true
                    font.pixelSize: 14
                }
            }

            // Loading Indicator
            BusyIndicator {
                anchors.centerIn: parent
                running: !streamToggle.checked
                visible: running
            }
        }

        // Controls
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            color: "#e0e0e0"
            radius: 5
            border.color: "#cccccc"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
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

                Item {
                    Layout.preferredWidth: 50
                }
                
                Button {
                    id: settingsButton
                    Layout.fillHeight: true
                    Layout.preferredWidth: 120
                    text: settingsPanelOpen ? "Close Settings" : "Settings"
                    background: Rectangle {
                        color: settingsPanelOpen ? "lightgray" : "#6060ff"
                        radius: 5
                    }

                    onClicked: {
                        settingsPanelOpen = !settingsPanelOpen;
                    }
                }

                Item {
                    Layout.fillWidth: true
                }

            }
        }
    }

    // Settings Panel (slides from the right)
    Rectangle {
        id: settingsPanel
        width: 250
        anchors {
            top: parent.top
            bottom: parent.bottom
            right: parent.right
            rightMargin: settingsPanelOpen ? 0 : -width
        }
        color: "#e0e0e0"
        radius: 5
        border.color: "lightgray"
        border.width: 1
        z: 10

        // Animation for panel sliding
        Behavior on anchors.rightMargin {
            NumberAnimation { 
                duration: 200
                easing.type: Easing.InOutQuad
            }
        }

        // Settings panel content
        ColumnLayout {
            anchors {
                fill: parent
                margins: 15
            }
            spacing: 15

            // Settings Title
            Text {
                text: "Settings"
                font.bold: true
                font.pixelSize: 20
                Layout.alignment: Qt.AlignHCenter
            }

            Rectangle {
                height: 1
                Layout.fillWidth: true
                color: "#dddddd"
            }

            // Colormap Selection
            Text {
                text: "Colormap"
                font.pixelSize: 16
                font.bold: true
            }

            ComboBox {
                id: colormapSelector
                Layout.fillWidth: true
                model: [
                    "JET", 
                    "HOT", 
                    "COOL", 
                    "RAINBOW", 
                    "VIRIDIS", 
                    "PLASMA", 
                    "INFERNO", 
                    "MAGMA", 
                    "CIVIDIS", 
                    "PARULA"
                ]
                currentIndex: 0
                
                onCurrentIndexChanged: {
                    thermalController.set_colormap(currentIndex)
                }
            }

            Rectangle {
                height: 1
                Layout.fillWidth: true
                color: "#dddddd"
            }

            // Temperature Warning Settings
            Text {
                text: "Temperature Warning"
                font.pixelSize: 16
                font.bold: true
            }

            // Enable Warning Switch
            Switch {
                id: enableTempWarning
                text: checked ? qsTr("Enabled") : qsTr("Disabled")
                checked: true
            }  

            Item {
                Layout.fillHeight: true
            }

            // Close Side Panel Button
            Button {
                text: "Close"
                Layout.fillWidth: true
                background: Rectangle {
                    color: "#6060ff"
                    radius: 5
                }
                
                onClicked: {
                   // thermalController.apply_settings(
                     //   colormapSelector.currentIndex,
                       // enableTempWarning.checked
                    //)
                    settingsPanelOpen = !settingsPanelOpen;
                }
            }
        }
    }

    // Connections to handle signals from controller
    Connections {
        target: thermalController

        function onFrameUpdated(frameBase64) {
            thermalImage.source = frameBase64;
        }

        function onStreamStateChanged(running) {
            isStreaming = running;
            if (!running) {
                // Clear the image when streaming stops
                thermalImage.source = "";
            }
        }

        function onTemperatureDataUpdated(min, max, avg) {
            minTemp = min;
            maxTemp = max;
            avgTemp = avg;
        }
    }

    onClosing: {
        thermalController.cleanup();
    }
}