import asyncio
import time
import numpy as np
import cv2
import asyncua
import logging

from multithreading.buffer import CircularBuffer
from app_configuration.app_configs import AppConfigs

class Producer:
    def __init__(self, buffer: CircularBuffer, appConfigs: AppConfigs):
        self.buffer = buffer
        self.running = False
        self.connected = False
        self.reconnect_delay = 5  # seconds between reconnection attempts
        self.custom_ns_name = "BeagleBoneThermal"
        self.custom_ns_idx = None
        self.client = None
        self._loop = None
        self.appConfigs = appConfigs
        self.scale_factor = 10

    async def connect(self):
        """Establish connection to OPC-UA server"""
        try:
            config = self.appConfigs.load_config()
            server_url = config.get('opcua_server')
            self.client = asyncua.Client(server_url)
            await self.client.connect()
            
            # Get namespace index
            ns_array = await self.client.get_namespace_array()
            self.custom_ns_idx = next((idx for idx, ns in enumerate(ns_array) if ns == self.custom_ns_name), 2)
            
            self.connected = True
            self.appConfigs.logging(f"Connected to OPC-UA server at {server_url}")
            print(f"Connected to OPC-UA server at {server_url}")
            return self.client
        except Exception as e:
            self.appConfigs.logging(f"Connection error: {e}")
            self.connected = False
            return None

    async def fetch_thermal_data(self):
        """Fetch data from the OPC-UA server and fill the buffer"""
        last_connection_attempt = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Reconnect if not connected
                if not self.connected and (current_time - last_connection_attempt) > self.reconnect_delay:
                    last_connection_attempt = current_time
                    await self.connect()
                
                # Fetch and process data if connected
                if self.connected and self.client:
                    try:
                        objects = self.client.nodes.objects
                        opcua_node = await objects.get_child([f"{self.custom_ns_idx}:ThermalData"])
                        
                        thermal_data = await opcua_node.read_value()

                        if isinstance(thermal_data, list) and len(thermal_data) == 768:
                            # Process thermal data
                            # Reshape to original sensor resolution (24x32)
                            thermal_array =  np.array(thermal_data, dtype=np.float32).reshape((24, 32))
                            
                            # Normalize to full range, but preserve temperature information
                            min_temp = np.min(thermal_array)
                            max_temp = np.max(thermal_array)
                            
                            # Normalize with custom max-min scaling, this is to keep the colormap values to correct ranges.
                            normalized = (thermal_array - max_temp) / (min_temp - max_temp)
                            
                       
                            
                            # Resize with cubic interpolation
                            resized = cv2.resize(
                                normalized, 
                                (32 * self.scale_factor, 24 * self.scale_factor), 
                                interpolation=cv2.INTER_CUBIC
                            )
                            
                          
                            heatmap = cv2.applyColorMap(
                                np.uint8(resized * 255), 
                                cv2.COLORMAP_JET )

                            heatmap = self.add_temperature_overlay(heatmap, thermal_data)

                            _, buffer_frame = cv2.imencode('.jpg', heatmap)
                         
                            # Add to buffer if not full
                            if not self.buffer.full():
                                self.buffer.put(buffer_frame.tobytes())
                                self.appConfigs.logging(f"Added frame to buffer.")
                            
                    except Exception as e:
                        self.appConfigs.logging(f"Data fetch error: {e}")
                        print(f"Data fetch error: {e}")
                        self.connected = False
                
                # Control loop 
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.appConfigs.logging(f"Critical error in fetch loop: {e}")
                print(f"Critical error in fetch loop: {e}")
                await asyncio.sleep(5)
            
            # Check stop condition
            if not self.running:
                break

    def add_temperature_overlay(self, heatmap, thermal_data):
            """
            Add temperature overlay to the heatmap
            Add min,max and avg temp on heatmap frame to display
            """
            try:
                # Reshape thermal data
                thermal_array = np.array(thermal_data, dtype=np.float32).reshape((24, 32))
                
                # Calculate min, max, and mean temperatures
                min_temp = np.min(thermal_array)
                max_temp = np.max(thermal_array)
                mean_temp = np.mean(thermal_array)
                
                # Prepare text overlay
                overlay_text = [
                    f"Min: {min_temp:.2f}°C",
                    f"Max: {max_temp:.2f}°C",
                    f"Avg: {mean_temp:.2f}°C"
                ]
                
                # Add text to image
                for i, text in enumerate(overlay_text):
                    cv2.putText(
                        heatmap, 
                        text, 
                        (10, 30 + i * 30),  # Position text
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7,  # Font scale
                        (255, 255, 255),  # White color
                        1  # Thickness
                    )
                
                return heatmap
            except Exception as e:
                self.appConfigs.logging(f"Thermal data processing error: {e}")
                self.logger.error(f"Thermal data processing error: {e}")
                return None


    def start(self):
        """Start the producer"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self.running = True
            self._loop.run_until_complete(self.fetch_thermal_data())
        except Exception as e:
            self.appConfigs.logging(f"Producer error: {e}")
            print(f"Producer error: {e}")
        finally:
            if self.client and self.connected:
                self._loop.run_until_complete(self.disconnect())
            self._loop.close()
            self._loop = None
            self.appConfigs.logging("Producer thread completed")
            print("Producer thread completed")

    async def disconnect(self):
        """Disconnect from OPC-UA server"""
        if self.client:
            try:
                await self.client.disconnect()
                self.appConfigs.logging("Disconnected from OPC-UA server")
                print("Disconnected from OPC-UA server")
            except Exception as e:
                self.appConfigs.logging(f"Disconnection error: {e}")
                print(f"Disconnection error: {e}")
            finally:
                self.client = None
                self.connected = False

    def stop(self):
        """Stop the producer"""
        self.running = False
        self.appConfigs.logging("Producer stop requested...")
        print("Producer stop requested...")