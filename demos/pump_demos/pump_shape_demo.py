import os
import sys

sys.path.append(os.getcwd())

from detect.shape_detect import ShapeDetector
from demos.pump_demos.pump_demo_driver import driver

if __name__ == "__main__":
    driver(ShapeDetector(), (5, 0, -70))
