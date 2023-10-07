#!/usr/bin/python
# -*- coding:utf-8 -*-
# @File    : yolo_test.py
# @Author  : Wang Weijian
# @Time    :  2023/09/27 10:51:04
# @function: the script is used to do something
# @version : V1

from ultralytics import YOLO
from ObbrecCamera import ObbrecCamera
import time
from PIL import Image
import torch

model = YOLO("../resources/yolo/best.pt")
predict_args = {"conf": 0.2}

if __name__ == "__main__":
    import os
    import sys

    sys.path.append(os.getcwd())
    from Utils.mouse_callbacks import *
    from Utils.crop_tools import crop_frame
    from configs.config_gripper import *

    cam = ObbrecCamera()
    cam.capture()

    conf_log = torch.tensor((0, 0))
    frame_count = 0
    detect_frame_count = 0

    while True:
        cam.update_frame()

        color_frame = cam.color_frame()

        if color_frame is None:
            time.sleep(0.1)
            continue

        frame_count += 1
        color_frame = crop_frame(color_frame, crop_size, crop_offset)
        color_frame = cv2.resize(color_frame, (640, 640))

        if color_frame is not None:
            # frame = np.hstack([color_frame, depth_frame])
            cv2.imshow("test", color_frame)
            result = model.predict(color_frame, **predict_args)
            # res = list(filter(lambda x: len(x.boxes) != 0, result))
            # print('res:', result[0].names, type(result))
            for r in result:
                # print('rrrrrr:', type(r), r)
                render = r.plot()
                if len(r.boxes.data) != 0:
                    detect_frame_count += 1
                conf_log = torch.cat((conf_log, torch.mean(r.boxes.conf).reshape(1)), 0)
                cv2.imshow("test", render)

        if cv2.waitKey(10) == ord("q"):
            break

    print(torch.mean(conf_log))
    print(f"识别率 {detect_frame_count / frame_count}")