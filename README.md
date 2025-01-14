# AiKit_3D_UI
For AiKit 3D Package Project, only supports MyCobot 280-M5 devices

# Requires environment

- Windows 10 or Windows 11 + python3.9 + pyqt6 + realsense camera
- Recommend using virtual environment

### realsense visualization tool installation

download link：[Intel.RealSense.Viewer.exe
](https://github.com/IntelRealSense/librealsense/releases/download/v2.54.1/Intel.RealSense.Viewer.exe)

# Install

```angular2html
git clone -b Realsense_280_M5 https://github.com/elephantrobotics/AiKit_3D_UI.git
```

# Use

```angular2html
cd AiKit_3D_UI
pip install -r requirements.txt
```

# Run

- Run in terminal
```angular2html
cd AiKit_3D_UI

python main.py
```

- Run in pycharm

直接运行AiKit_3D_UI文件夹下的main.py文件即可

# Notice

realsense相机必须要用USB3.2的线连接，不然深度信息可能出错 夹爪版本目前不稳定，尽量用吸泵版本
