import os
import sys

sys.path.append(os.getcwd())

from detect.color_detect import ColorDetector
from demos.pump_demos.pump_demo_driver import driver

if __name__ == "__main__":
    driver(ColorDetector(), (30, 10, -10))
