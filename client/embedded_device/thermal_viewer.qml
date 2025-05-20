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
                    color: "lightgray"
                    radius: 5
                    border.color: "lightgray"
                    border.width: 1

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

        // Thermal image display
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
                    Layout.fillWidth: true
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