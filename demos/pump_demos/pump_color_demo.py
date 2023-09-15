import os
import sys

sys.path.append(os.getcwd())

from detect.color_detect import ColorDetector
from demos.pump_demos.pump_demo_driver import driver
# from demos.pump_demos.pump_color_test import driver

if __name__ == "__main__":
    driver(ColorDetector(), (5, 0, -73))
