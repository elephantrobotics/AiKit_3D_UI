#!/usr/bin/python
# -*- coding:utf-8 -*-
# @File    : finger_location_demo.py
# @Author  : Wang Weijian
# @Time    :  2023/09/09 14:00:51
# @function: Use QR code recognition for finger positioning
# @version : V1

import os
import sys

sys.path.append(os.getcwd())

from detect.encode_detect import ArucoDetector
from pump_encode_driver import driver

if __name__ == "__main__":
    detector = ArucoDetector()
    detector.area_low_threshold = 5000
    driver(detector, (10, -5, -55))
