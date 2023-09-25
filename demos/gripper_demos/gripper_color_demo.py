import os
import sys

sys.path.append(os.getcwd())

from detect.color_detect import ColorDetector
from demos.gripper_demos.gripper_demo_driver import driver

if __name__ == "__main__":
    detector = ColorDetector()
    detector.area_low_threshold = 5000
    driver(detector, (15, -10, 5))
