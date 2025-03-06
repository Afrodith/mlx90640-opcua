For generating the ifc-micorservice.exe bundle with all depedencies, first we need to install the following tools:

Visual Studio Build Tools: Install VS Build tools 2022, can be found here: https://visualstudio.microsoft.com/downloads/. We use them to build depedency libraries mathutils and bpy later on with poetry.

Python 3.11: https://www.python.org/downloads/release/python-3119/ <br>
  - on pipeline server install it for all user with path and pip. <br>
  - VS Build Tools: vs_buildTool.exe, execute with standard configuration<br>

scoop: https://scoop.sh/ <br>
pipx: https://github.com/pypa/pipx <br>
poetry: https://python-poetry.org/docs/#installation <br>

The installation of poetry is the following:

# Install scoop first:
In pipeline, pipx is installed with pip. For further details see pipeline.

  ```
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
  ```

# Install pipx with scoop:
  ```
  scoop install pipx
  pipx ensurepath
  ```

# Install poetry with pipx:
start in a new powershell to have the updated path variable.

  pipx install poetry

# Build project
To build the poetry project and generate the executable, do the following:

- change to project directory:

  cd embedded_device\

- create a python virtual environmentl:

  python -m venv venv

- activate virtual environment:
  
  ./venv/Scripts/activate
  
- Now open a poetry shell to work on the contained environment:
	
  poetry shell
	
- Istall projects depedencies and tools:
	
  poetry install

- Generate the executable by using the embedded pyinstaller api in poetry with the following command:
	
  poetry run build
	
	

The executable will be generated in the dist folder. Copy the exe to the desired location and alongside it copy the folder app_configuration with the embedded_device_config.json inside it and thermal_viewer.qml ui file.

![depedencies](C:\Users\afrodititoufa\AppData\Roaming\Typora\typora-user-images\image-20250306060731331.png)



The embedded_device_config.json file contains all the configurations for the service (log genration, opcua server ip) . Now the exe is ready to be run.	

When the exe is started a log file (embedded_device.log) is produced that contains runtime messages from the app.

For more information, documentation check the following:

https://pyinstaller.org/en/stable/index.html <br>
https://python.land/deployment/pyinstaller <br>
https://stackoverflow.com/questions/76145761/use-poetry-to-create-binary-distributable-with-pyinstaller-on-package
