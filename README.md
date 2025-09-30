# AiKit_3D_UI
For AiKit 3D Package Project, only supports MechArm 270-M5 devices

## Requires environment

- Windows 10 or Windows 11 + python3.9 + pyqt6 + realsense camera
- Recommend using virtual environment

## realsense visualization tool installation

download link：[Intel.RealSense.Viewer.exe
](https://github.com/IntelRealSense/librealsense/releases/download/v2.54.1/Intel.RealSense.Viewer.exe)

## Install Code

```bash
git clone -b realsense_UI https://github.com/elephantrobotics/AiKit_3D_UI.git
```

## Creat Virtual Environment

Created through terminal command, where `virtual_name` is the custom virtual environment name:

```bash
# Create 
python -m venv virtual_name

# Activate virtual environment
cd virtual_name/Scripts
activate
```

## Install Python dependencies

The premise is to activate the virtual environment

```bash
cd AiKit_3D_UI
pip install -r requirements.txt
```

## Start the program

- **Run in terminal**

>> The premise is to activate the virtual environment

Enter the directory where the main program is located in the terminal and run

```bash
cd AiKit_3D_UI

python main.py
```

- **Run in pycharm**

Just run the `main.py` file in the AiKit_3D_UI folder (**Note:** The Python interpreter selects the virtual environment)

## Notice

The RealSense camera must be connected with a USB 3.2 cable, otherwise the depth information may be incorrect. The gripper version is currently unstable, so try to use the suction pump version.
