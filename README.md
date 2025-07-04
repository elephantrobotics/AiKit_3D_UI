# AiKit_3D_UI
For AiKit 3D Package Project, only supports MyCobot 280-PI devices

# Requires environment

Windows 10 or Windows 11 + python3.9 + pyqt6 + Socket communication

# Run the server script

When using the 280 PI device, you need to run the server script in the 280 PI system in advance before running the AiKit_3D_UI program on the PC. The 280PI system needs to be in the same network segment as the PC, that is, connected to the same network.

Server script address: [Server_280.py](https://github.com/elephantrobotics/pymycobot/blob/main/demo/Server_280.py)

Open the terminal and run:

```bash
python Server_280.py
```

After the server is running, the terminal will output the corresponding IP address and port number

# Install

```angular2html
git clone -b Deeyea_280_PI https://github.com/elephantrobotics/AiKit_3D_UI.git
```

# Use

```angular2html
cd AiKit_3D_UI
pip install -r requirements.txt
```

# Run

```angular2html
cd AiKit_3D_UI

python main.py
```

The PC needs to be in the same network segment as the 280 PI device. After the UI program is started, connect the robot arm in the UI interface according to the IP address and port number output by the server running 280 PI. Since socket communication is affected by network latency, the robot arm connection communication may be delayed, so you need to wait patiently.

For more usage methods, please see:

- [AiKit_3D Kit use](https://docs.elephantrobotics.com/docs/aikit-3D-en/2-serialproduct/2.11-AIkit2023en_3D/AiKit_UI_Download.html)

- [AiKit_3D 套装使用](https://docs.elephantrobotics.com/docs/aikit-3D-cn/2-serialproduct/2.11-AIkit2023_3D/AiKit3D_UI_Manual.html)