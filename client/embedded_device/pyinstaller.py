import PyInstaller.__main__
from pathlib import Path

HERE = Path(__file__).parent.absolute().parent.absolute()
path_to_main = str(HERE / "app.spec")

def install():
    PyInstaller.__main__.run([
        '--noconfirm',
         path_to_main
    ])

    