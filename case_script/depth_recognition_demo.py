#!/usr/bin/python
# -*- coding:utf-8 -*-
# @File    : depth_recognition_demo.py
# @Author  : Wang Weijian
# @Time    :  2023/09/08 14:55:11
# @function: Depth recognition case, always able to pick up the deepest wood block
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
