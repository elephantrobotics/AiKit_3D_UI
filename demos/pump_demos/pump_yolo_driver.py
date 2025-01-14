#!/usr/bin/python
# -*- coding:utf-8 -*-
# @File    : pump_yolo_driver.py
# @Author  : Wang Weijian
# @Time    :  2023/09/07 17:35:50
# @function: yolo recognizes the robotic arm control logic script
# @version : V1
import random

import cv2
import numpy as np
from typing import Tuple, Any
import sys
import os
import time
from pathlib import Path

from pymycobot.utils import get_port_list

sys.path.append(os.getcwd())

from RealSenseCamera import RealSenseCamera
from Utils.mouse_callbacks import *
from Utils.coord_calc import CoordCalc
from Utils.crop_tools import crop_frame, crop_poly
from configs.config_pump import *
from Utils.arm_controls import *

# from detect.yolov8_detect import YOLODetector
import pymycobot
from packaging import version

# min low version require
MIN_REQUIRE_VERSION = '3.6.3'

current_verison = pymycobot.__version__
print('current pymycobot library version: {}'.format(current_verison))
if version.parse(current_verison) < version.parse(MIN_REQUIRE_VERSION):
    raise RuntimeError('The version of pymycobot library must be greater than {} or higher. The current version is {}. Please upgrade the library version.'.format(MIN_REQUIRE_VERSION, current_verison))
else:
    print('pymycobot library version meets the requirements!')
    from pymycobot import MechArm270

coords_transformer = CoordCalc(
    target_base_pos3d,
    (final_frame_size // 2, final_frame_size // 2),
    plane_frame_size_ratio,
)

# connect arm
plist = get_port_list()
print(plist)

arm = MechArm270(plist[0])


def driver(detector, offset_3d=(0, 0, 0)):
    cam = RealSenseCamera()
    cam.capture()

    arm.send_angles(arm_idle_angle, 50)
    time.sleep(3)
    arm.set_fresh_mode(0)
    time.sleep(1)

    # set tool frame to match the gripper
    arm.set_tool_reference([0, -10, 100, 0, 0, 0])
    time.sleep(1)
    arm.set_end_type(1)
    time.sleep(1)
    pump_off(arm)
    time.sleep(3)

    while True:
        cam.update_frame()
        color_frame = cam.color_frame()
        depth_frame = cam.depth_frame()
        if color_frame is None or depth_frame is None:
            time.sleep(0.1)
            continue
        color_frame = crop_frame(color_frame, crop_size, crop_offset)
        depth_frame = crop_frame(depth_frame, crop_size, crop_offset)
        depth_visu_frame = depth_frame.copy()

        color_frame = cv2.resize(color_frame, None, fx=zoom_factor, fy=zoom_factor)
        depth_frame = cv2.resize(depth_frame, None, fx=zoom_factor, fy=zoom_factor)
        if color_frame is not None:
            depth_visu_frame = depth_visu_frame / np.max(depth_frame) * 255
            depth_visu_frame = depth_visu_frame.astype(np.uint8)

            depth_visu_frame = cv2.cvtColor(depth_visu_frame, cv2.COLOR_GRAY2BGR)
            cv2.namedWindow("depth", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("depth", 390, 390)
            cv2.imshow("color", color_frame)
            cv2.imshow("depth", depth_visu_frame)
            # cv2.waitKey(1)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cam.release()
                cv2.destroyAllWindows()
                sys.exit()

        if color_frame is None:
            continue

        res = detector.detect(color_frame)
        if res:
            for r in res:
                # draw class name
                render = r.plot()
                cv2.imshow("color", render)
                cv2.waitKey(1)

            # interpret result
            obj_configs = []
            # Multi-target coordinate results
            coords_res = []
            for obj in res:
                rect = detector.get_rect(
                    obj)  # [[[167, 158], [173, 158], [173, 164], [167, 164]], [[291, 245], [297, 245], [297, 251], [291, 251]], [[146, 266], [152, 266], [152, 272], [146, 272]]]
                for coords in detector.target_position(obj):
                    x, y = coords
                    coords_res.append((x, y))
                coords_res = tuple(coords_res)
                obj_configs.append((rect, coords_res))

            # pack (depth, pos, angle) together
            depth_pos_pack = []
            # Multiple Target Depth Results
            depth_res = []
            for obj in obj_configs:
                rect = obj[
                    0]  # [[[167, 158], [173, 158], [173, 164], [167, 164]], [[291, 245], [297, 245], [297, 251], [291, 251]], [[146, 266], [152, 266], [152, 272], [146, 272]]]
                coords = obj[1]  # ((170, 161), (294, 248), (149, 269))
                rect = np.array(rect)
                for rects in rect:
                    target_depth_frame = crop_poly(depth_frame, rects)
                    mean_depth = np.sum(target_depth_frame) / np.count_nonzero(
                        target_depth_frame
                    )
                    depth_res.append(mean_depth)
                depth_list = tuple(depth_res)
                depth_pos_pack.append((depth_list, coords))
            print('depth_pos_pack:', depth_pos_pack)  # [((394.0, 378.0, 393.0), ((170, 161), (294, 248), (149, 269)))]
            # print('lowest:', min(depth_pos_pack))  # ((394.0, 378.0, 393.0), ((170, 161), (294, 248), (149, 269)))
            # find lowest depth (highest in pile)
            data = min(depth_pos_pack)
            print('data:', data)
            # 提取深度值和坐标点
            depth_values = data[0]  # (394.0, 378.0, 393.0)
            coordinate_tuples = data[1]  # ((170, 161), (294, 248), (149, 269))

            # 创建一个字典来将深度值映射到坐标点
            depth_coordinate_map = {}

            # 将深度值和坐标点进行匹配
            for i, depth in enumerate(depth_values):
                if i < len(coordinate_tuples):
                    coordinates = coordinate_tuples[i]
                    depth_coordinate_map[depth] = coordinates

            # 现在您可以通过深度值来查找相应的坐标点
            depth_to_match = min(depth_values)
            matched_coordinates = depth_coordinate_map.get(depth_to_match)
            if np.isnan(depth_to_match):
                continue
            x, y, z = 0, 0, 0
            if matched_coordinates:
                x, y = matched_coordinates
                x, y = int(x), int(y)
                z = int(floor_depth - depth_to_match)
                print(f"深度值 {depth_to_match} 对应的坐标点是 {matched_coordinates}")
            else:
                print(f"未找到深度值 {depth_to_match} 对应的坐标点")
            # x, y = 180, 271
            print(f"xyz in cam frame: {x} {y} {z}")
            arm_move(x, y, z, offset_3d)


def arm_move(x, y, z, offset_3d=(0, 0, 0)):
    """
        The process of controlling the movement of the robotic arm to grab objects
        控制机械臂运动抓取物块的流程
    """
    # target placement point
    box_position = [
        [-48.86, 28.21, -16.25, 0.17, 66.7, 0.0],  # Bin D
        [-30.93, 49.04, -46.23, 0.43, 49.04, 0.26],  # Bin C
        [51.67, 24.6, -7.38, 0.0, 53.87, -0.26],  # Bin A
        [88.06, 15.46, 0.79, 0.61, 68.02, 0.35],  # Bin B
    ]
    # Generate random numbers for random placement
    random_number = random.randint(0, 3)
    print('put index number:', random_number)
    # hover to avoid collision
    arm.send_angles(arm_pick_hover_angle, 50)
    time.sleep(3)

    target_pos3d = coords_transformer.frame2real(x, y)
    target_pos3d = list(target_pos3d)
    print(f"raw coord: {target_pos3d}")

    # adjust final offset
    off_x, off_y, off_z = offset_3d
    target_pos3d[0] += final_coord_offset[0] + off_x + 5
    target_pos3d[1] += final_coord_offset[1] + off_y
    target_pos3d[2] += final_coord_offset[2] + z - 20 + off_z
    # add angle
    target_pos3d.extend([-177, 0, 90])

    # send angle
    # move x-y first
    coord_xy = target_pos3d.copy()[:3]
    coord_xy[2] = 50
    print('target XYZ:', (coord_xy[0], coord_xy[1], coord_xy[2]))
    print(f"X-Y move: {coord_xy}")
    # arm.send_angle(1, 0, 50)
    # time.sleep(3)
    # arm.send_coords(coord_xy, 50)
    # time.sleep(3)
    position_move(arm, *coord_xy)
    time.sleep(3)

    # send target angle
    arm.send_coords(target_pos3d, 20, 1)
    print(f"Target move: {target_pos3d}")
    time.sleep(3)
    print(f"Actual coord : {arm.get_coords()}")
    # time.sleep(0.1)
    pump_on(arm)
    time.sleep(3)

    # elevate first
    arm.send_coord(3, 90, 25)
    time.sleep(4)

    # sent to drop point
    arm.send_angles(box_position[random_number], 50)
    time.sleep(3)

    pump_off(arm)
    time.sleep(1.5)
    arm.send_angles(arm_idle_angle, 50)
    time.sleep(4)
