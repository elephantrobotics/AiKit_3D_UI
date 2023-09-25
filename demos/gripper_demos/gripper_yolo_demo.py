import os
import sys
from pathlib import Path
sys.path.append(os.getcwd())

from detect.yolov8_detect import YOLODetector
from demos.gripper_demos.gripper_yolo_driver import driver


if __name__ == "__main__":
    driver(YOLODetector(), (15, -10, 5))
