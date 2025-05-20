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
        self.thermal_node = None
        self.last_thermal_data = None
        self.last_fetch_time = 0
        self.fetch_interval = 0.1  # Minimum time between fetches (seconds)

    async def connect(self):
        """Establish connection to OPC-UA server"""
        try:
            config = self.appConfigs.load_config()
            server_url = config.get('opcua_server')
            self.client = asyncua.Client(server_url)
            await self.client.connect()
            
            ns_array = await self.client.get_namespace_array()
            self.custom_ns_idx = next((idx for idx, ns in enumerate(ns_array) if ns == self.custom_ns_name), 2)
            self.thermal_node = await self.client.nodes.objects.get_child([f"{self.custom_ns_idx}:ThermalData"])
            
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
                
                # Try re-connect
                if not self.connected and (current_time - last_connection_attempt) > self.reconnect_delay:
                    last_connection_attempt = current_time
                    await self.connect()
                
                # Fetch and process data if connected
                if self.connected and self.client and self.thermal_node:
                    try:
                        # Rate limit data fetching for better performance
                        if current_time - self.last_fetch_time >= self.fetch_interval:
                            self.last_fetch_time = current_time

                            thermal_data = await self.thermal_node.read_value()
                            
                            # Store the raw thermal data for temperature display
                            if isinstance(thermal_data, list) and len(thermal_data) == 768:
                                self.last_thermal_data = thermal_data
                                
                                # Process thermal data
                                # Reshape to original sensor resolution (24x32)
                                thermal_array = np.array(thermal_data, dtype=np.float32).reshape((24, 32))
                                
                                # Normalize to full range
                                min_temp = np.min(thermal_array)
                                max_temp = np.max(thermal_array)
                                
                                # Normalize with custom max-min scaling
                                normalized = (thermal_array - max_temp) / (min_temp - max_temp)
                                
                                # Resize with cubic interpolation
                                resized = cv2.resize(
                                    normalized, 
                                    (32 * self.scale_factor, 24 * self.scale_factor), 
                                    interpolation=cv2.INTER_CUBIC
                                )
                                
                                # Apply colormap
                                heatmap = cv2.applyColorMap(
                                    np.uint8(resized * 255), 
                                    cv2.COLORMAP_JET
                                )
                                
                                # Compress for better performance
                                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
                                _, buffer_frame = cv2.imencode('.jpg', heatmap, encode_param)
                                
                                # Add to buffer if not full
                                if not self.buffer.full():
                                    self.buffer.put(buffer_frame.tobytes())
                                else:
                                    # If buffer is full, remove oldest item and add new one
                                    self.buffer.get() 
                                    self.buffer.put(buffer_frame.tobytes())
                    except Exception as e:
                        self.appConfigs.logging(f"Data fetch error: {e}")
                        print(f"Data fetch error: {e}")
                        self.connected = False
                
                await asyncio.sleep(0.03)
                
            except Exception as e:
                self.appConfigs.logging(f"Critical error in fetch loop: {e}")
                print(f"Critical error in fetch loop: {e}")
                await asyncio.sleep(1)
            
            # Check stop condition
            if not self.running:
                break

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