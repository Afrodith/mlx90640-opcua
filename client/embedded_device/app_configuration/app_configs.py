import os
import json
from datetime import datetime
from pathlib import Path

class AppConfigs:

    def __init__(self):
        self.config = self.load_config()
        self.log_file = self.__get_log_file()
        

    def load_config(self):
        file_path = os.path.join(os.getcwd(),'app_configuration','embedded_device_config.json')
        try:
            with open(file_path, 'r') as config_file:
                return  json.load(config_file)
        except Exception as e:
            print(f"Error config file doesn't exist: {e}")
            return
        

    def logging(self, message, error=None):
        timestamp = self.__log_timestamp()
        if error is None:
            self.log_file.write(timestamp + ": " + message + "\n")
            self.log_file.flush()
        else:
            self.log_file.write(timestamp + ": " + message + ". " + "Error: " + str(error) + "\n")
            self.log_file.flush()

    def __log_timestamp(self):
        return  datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def __get_log_file(self):
        logfile = open(self.config.get('log_file', 'embedded_device.log'), 'w')
        return logfile
