import sys
import numpy as np
import cv2
import threading
import base64
import os
import time

# PySide6 imports
from PySide6.QtCore import QObject, Signal as pyqtSignal, Slot as pyqtSlot, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QUrl
from PySide6.QtQuickControls2 import QQuickStyle

from multithreading.buffer import CircularBuffer
from multithreading.producer import Producer
from app_configuration.app_configs import AppConfigs


# PyInstaller
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS  
else:
    base_path = os.path.dirname(__file__)

qml_file = os.path.join(base_path, ".", "thermal_viewer.qml")

class ThermalImageProcessor(QObject):
    """Handles thermal image processing and conversion"""
    def __init__(self):
        super().__init__()
    
    def convert_to_base64(self, frame):
        """Convert OpenCV frame to base64 encoded image"""
        if frame is None:
            return None
        
       
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Encode image to JPG with reduced quality for better performance
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
        _, buffer = cv2.imencode('.jpg', frame_rgb, encode_param)
        
        
        base64_image = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpg;base64,{base64_image}"
    
    def extract_temperature_data(self, thermal_data):
        """Extract temperature data from thermal array"""
        if thermal_data is None or not isinstance(thermal_data, list):
            return 0.0, 0.0, 0.0
        
        try:
            # Reshape thermal data to original sensor resolution
            thermal_array = np.array(thermal_data, dtype=np.float32).reshape((24, 32))
            
            # Calculate min, max, and mean temperatures
            min_temp = np.min(thermal_array)
            max_temp = np.max(thermal_array)
            mean_temp = np.mean(thermal_array)
            
            return min_temp, max_temp, mean_temp
        except Exception as e:
            print(f"Error extracting temperature data: {e}")
            return 0.0, 0.0, 0.0

class ThermalViewerController(QObject):
    """Main controller for thermal viewer application"""
    
    # Signals for QML communication
    frameUpdated = pyqtSignal(str, arguments=['frameBase64'])
    streamStateChanged = pyqtSignal(bool, arguments=['isRunning'])
    temperatureDataUpdated = pyqtSignal(float, float, float, arguments=['min', 'max', 'avg'])
    
    def __init__(self):
        super().__init__()
        
       
        self.appConfigs = AppConfigs()
        self.buffer = CircularBuffer(buffer_size=30) 
        
        # Image processor
        self.image_processor = ThermalImageProcessor()
        
        # Producer
        self.producer = Producer(self.buffer, self.appConfigs)
        
        self.producer_thread = None
        self.running = False
        self.last_thermal_data = None
        
        # Frame update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)  # 30fps

        # Log start
        self.appConfigs.logging("Thermal Viewer Controller initialized")

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
            self.producer_thread.daemon = True
            self.producer_thread.start()
            
            # Notify QML about stream state
            self.streamStateChanged.emit(True)
            self.appConfigs.logging("Stream started")
    
    def stop_stream(self):
        """Stop the thermal data producer"""
        if self.running:
            self.running = False
            
            # Stop producer
            if self.producer:
                self.producer.stop()
            
            # Wait for thread to finish with timeout
            if self.producer_thread:
                self.producer_thread.join(timeout=2.0)
            
            # Reset last thermal data
            self.last_thermal_data = None
            
            # Notify QML that stream is stopped
            self.streamStateChanged.emit(False)
            self.appConfigs.logging("Stream stopped")
    
    def update_frame(self):
        """Update the displayed frame from the buffer"""
        if not self.running:
            return
        
        # Get frame from buffer
        frame_bytes = self.buffer.get()
        
        if frame_bytes is not None:
            try:
                # Decode the image from buffer
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    # Get thermal data from producer for temperature display
                    if hasattr(self.producer, 'last_thermal_data') and self.producer.last_thermal_data is not None:
                        self.last_thermal_data = self.producer.last_thermal_data
                        
                        # Extract temperature data
                        min_temp, max_temp, mean_temp = self.image_processor.extract_temperature_data(self.last_thermal_data)
                        
                        # Update temperature values in QML
                        self.temperatureDataUpdated.emit(min_temp, max_temp, mean_temp)
                    
                    # Convert to base64 without temperature overlay
                    base64_image = self.image_processor.convert_to_base64(frame)
                    
                    if base64_image:
                        # Emit signal to update QML
                        self.frameUpdated.emit(base64_image)
                        
            except Exception as e:
                self.appConfigs.logging(f"Error updating frame: {e}")
                print(f"Error updating frame: {e}")

    def cleanup(self):
        """Clean up resources before closing the application"""
        self.stop_stream()
        if self.producer:
            self.producer.stop()
        if self.producer_thread and self.producer_thread.is_alive():
            self.producer_thread.join(timeout=2.0)
            
        self.appConfigs.logging("Producer and thread cleaned up")
        print("Producer and thread cleaned up")

def main():
    
    app = QApplication(sys.argv)
    
    
    engine = QQmlApplicationEngine()
    
    
    controller = ThermalViewerController()
    
    # Expose controller to QML
    engine.rootContext().setContextProperty("thermalController", controller)
    
    QQuickStyle.setStyle("Universal")  
    
    # Load QML file
    engine.load(QUrl.fromLocalFile(qml_file))
    
    if not engine.rootObjects():
        print("Failed to load QML file")
        sys.exit(-1)
        
    # Handle window closing
    engine.rootObjects()[0].destroyed.connect(controller.cleanup)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()