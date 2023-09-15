#!/usr/bin/python
# -*- coding:utf-8 -*-
# @File    : stack_items_demo.py
# @Author  : Wang Weijian
# @Time    :  2023/09/08 14:58:03
# @function: Case of item stacking, using a suction pump to pick up the stacked items into the material box
# @version : V1

import os
import sys

sys.path.append(os.getcwd())

from detect.color_detect import ColorDetector
from pump_demo_driver import driver

if __name__ == "__main__":
    detector = ColorDetector()
    detector.area_low_threshold = 5000
    driver(detector, (5, 0, -76))
