#!/usr/bin/python
# -*- coding:utf-8 -*-
# @File    : pump_depalleting_demo.py
# @Author  : Wang Weijian
# @Time    :  2023/09/05 11:24:20
# @function: the script is used to do something
# @version : V1

import os
import sys
from pathlib import Path
sys.path.append(os.getcwd())

from detect.yolov8_detect import YOLODetector
from demos.pump_demos.pump_depalleting_driver import driver


if __name__ == "__main__":
    driver(YOLODetector(), (0, 0, -75))
