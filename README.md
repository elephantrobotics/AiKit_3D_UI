# AiKit_3D_UI
For AiKit 3D Package Project, only supports MyCobot 280-M5 devices

## Requires environment

- Windows 10 or Windows 11 + python3.9 + pyqt6 + realsense camera
- Recommend using virtual environment

## realsense visualization tool installation

download link：[Intel.RealSense.Viewer.exe
](https://github.com/IntelRealSense/librealsense/releases/download/v2.54.1/Intel.RealSense.Viewer.exe)

## Install Code

```bash
git clone -b Realsense_280_M5 https://github.com/elephantrobotics/AiKit_3D_UI.git
```

## Install Python dependencies

```angular2html
cd AiKit_3D_UI
pip install -r requirements.txt
```

## Start the program

- **Run in terminal**

Enter the directory where the main program is located in the terminal and run

```bash
cd AiKit_3D_UI

python main.py
```

- **Run in pycharm**

Simply run the `main.py` file in the AiKit_3D_UI folder.

For more details, see [AiKit 3D UI Instructions](https://docs.elephantrobotics.com/docs/aikit-3D-en/2-serialproduct/2.11-AIkit2023en_3D/AiKit_UI_Download.html)

## Notice

The RealSense camera must be connected using a USB 3.2 cable, otherwise depth information may be incorrect. The gripper version is currently unstable, so use the pump version if possible.