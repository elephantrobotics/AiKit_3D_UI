#!/usr/bin/python
# -*- coding:utf-8 -*-
# @File    : open_camera.py
# @Author  : Wang Weijian
# @Time    :  2023/09/22 17:56:37
# @function: 检测能否正常打开realsense相机，显示画面
# @version : V1

import os
import sys

from RealSenseCamera import RealSenseCamera

sys.path.append(os.getcwd())
from Utils.mouse_callbacks import *
from Utils.crop_tools import crop_frame
from configs.config_pump import *

cam = RealSenseCamera()
cam.capture()

while True:
    cam.update_frame()

    color_frame = cam.color_frame()
    color_frame = crop_frame(color_frame, crop_size, crop_offset)
    color_frame = cv2.resize(color_frame, None, fx=3, fy=3)
    if color_frame is not None:
        cv2.imshow("Color", color_frame)
        bind_mouse_event(color_frame, "Color", mouseHSV)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        cam.release()
        cv2.destroyAllWindows()
        sys.exit()
