import sys
import numpy as np
import cv2
import threading
import base64
import os

# Change PyQt6 imports to PySide6
from PySide6.QtCore import QObject, Signal as pyqtSignal, Slot as pyqtSlot, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QUrl
from PySide6.QtQuickControls2 import QQuickStyle

from multithreading.buffer import CircularBuffer
from multithreading.producer import Producer
from app_configuration.app_configs import AppConfigs

class ThermalImageProcessor(QObject):
    """Handles thermal image processing and conversion"""
    def __init__(self):
        super().__init__()

    
    def convert_to_base64(self, frame):
        """Convert OpenCV frame to base64 encoded image"""
        if frame is None:
            return None
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Encode image to PNG
        _, buffer = cv2.imencode('.jpg', frame_rgb)
        
        # Convert to base64
        base64_image = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpg;base64,{base64_image}"

class ThermalViewerController(QObject):
    """Main controller for thermal viewer application"""
    
    # Signals for QML communication
    frameUpdated = pyqtSignal(str, arguments=['frameBase64'])
    streamStateChanged = pyqtSignal(bool, arguments=['isRunning'])
    
    def __init__(self):
        super().__init__()
        
        # Configuration and buffer
        self.appConfigs = AppConfigs()
        self.buffer = CircularBuffer(buffer_size=10)
        
        # Image processor
        self.image_processor = ThermalImageProcessor()
        
        # Producer
        self.producer = Producer(self.buffer, self.appConfigs)
        
        self.producer_thread = None
        self.running = False
        
        # Frame update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(70)  

    @pyqtSlot()
    def toggle_stream(self):
        """Toggle the thermal stream on and off"""
        if not self.running:
            self.start_stream()
        else:
            self.stop_stream()
    
    def start_stream(self):
        """Start the thermal data producer"""
        if not self.running:
            self.running = True
            self.producer_thread = threading.Thread(target=self.producer.start)
            self.producer_thread.start()
            
            # Notify QML about stream state
            self.streamStateChanged.emit(True)
    
    def stop_stream(self):
        """Stop the thermal data producer"""
        if self.running:
            self.running = False
            
            # Stop producer
            if self.producer:
                self.producer.stop()
            
            # Wait for thread to finish
            if self.producer_thread:
                self.producer_thread.join()
            
            self.streamStateChanged.emit(False)
    
    def update_frame(self):
        """Update the displayed frame from the buffer"""
        if not self.running:
            return
        
        # Get frame from buffer
        frame_bytes = self.buffer.get()
        
        if frame_bytes is not None:
            # Decode the image from buffer
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            
            if frame is not None:
                # Convert to base64
                base64_image = self.image_processor.convert_to_base64(frame)
                
                if base64_image:
                    # Emit signal to update QML
                    self.frameUpdated.emit(base64_image)

    def cleanup(self):
        """Clean up resources before closing the application"""
        self.stop_stream()
        if self.producer:
            self.producer.stop()
        if self.producer_thread:
            self.producer_thread.join()
            
        self.appConfigs.logging("Producer and thread cleaned up")
        print("Producer and thread cleaned up")

def main():
    # Create Qt Application
    app = QApplication(sys.argv)
    
    # Create QML engine
    engine = QQmlApplicationEngine()
    
    # Create controller
    controller = ThermalViewerController()
    
    # Expose controller to QML
    engine.rootContext().setContextProperty("thermalController", controller)
    
    QQuickStyle.setStyle("Universal")  
    
    # Load QML file
    engine.load(QUrl.fromLocalFile('thermal_viewer.qml'))
    
    
    if not engine.rootObjects():
        print("Failed to load QML file")
        sys.exit(-1)
        
    # Handle window closing
    engine.rootObjects()[0].destroyed.connect(controller.cleanup)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()