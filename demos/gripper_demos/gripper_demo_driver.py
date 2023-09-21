import cv2
import numpy as np
from typing import Tuple, Any
import sys
import os
from pymycobot import MechArm
import time

from pymycobot.utils import get_port_list

sys.path.append(os.getcwd())

from ObbrecCamera import ObbrecCamera
from Utils.mouse_callbacks import *
from Utils.coord_calc import CoordCalc
from Utils.crop_tools import crop_frame, crop_poly
from configs.config_gripper import *
from Utils.arm_controls import *

coords_transformer = CoordCalc(
    target_base_pos3d,
    (final_frame_size // 2, final_frame_size // 2),
    plane_frame_size_ratio,
)

plist = get_port_list()
print(plist)

arm = MechArm(plist[0])


def driver(detector, offset_3d=(0, 0, 0)):
    cam = ObbrecCamera()
    cam.capture()

    # arm = MechArm(arm_serial_port)
    arm.send_angles(arm_idle_angle, 50)
    arm.set_fresh_mode(0)
    time.sleep(1)
    arm.set_tool_reference(tool_frame)
    time.sleep(1)
    arm.set_end_type(1)
    time.sleep(1)
    open_gripper(arm)
    time.sleep(3)
    release_gripper(arm)
    time.sleep(0.1)

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
            detector.draw_result(color_frame, res)
            cv2.imshow("color", color_frame)
            bind_mouse_event(color_frame, "color", mouseHSV)
            cv2.waitKey(1)

            # interpret result
            obj_configs = []
            for obj in res:
                angle = detector.get_radian(obj)
                rect = detector.get_rect(obj)
                x, y = detector.target_position(obj)
                obj_configs.append((rect, (x, y), angle))

            # pack (depth, pos, angle) together
            depth_pos_pack = []
            for obj in obj_configs:
                rect, (x, y), angle = obj
                # rect = np.array([(x - 10, y -10), (x + 10, y - 10), (x + 10, y+ 10), (x-10, y+10)])
                rect = np.array(rect)
                target_depth_frame = crop_poly(depth_frame, rect)
                mean_depth = np.sum(target_depth_frame) / np.count_nonzero(
                    target_depth_frame
                )
                depth_pos_pack.append((mean_depth, (x, y), angle))

            # find the lowest depth (highest in pile)
            depth, (x, y), angle = min(depth_pos_pack)
            angle = (angle / np.pi) * 180
            angle = angle - 180 if angle > 180 else angle
            x, y = int(x), int(y)
            z = int(floor_depth - depth)
            angle = 0
            # transform angle from camera frame to arm frame
            print(f"Raw x,y,z,angle : {x} {y} {z} {angle}")
            detected_name = detector.detected_name
            color_id = 0
            # 根据识别到的颜色设置投放点
            if detected_name == "redA" or detected_name == "redB" or detected_name == "Triangle":
                color_id = 0
            elif detected_name == "green" or detected_name == "Square":
                color_id = 1
            elif detected_name == "blueB" or detected_name == "Rectangle":
                color_id = 2
            elif detected_name == "yellow" or detected_name == "Circle":
                color_id = 3
            arm_move(color_id, x, y, z, angle, offset_3d)


def arm_move(color_id, x, y, z, angle, offset_3d=(0, 0, 0)):
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
    # hover to avoid collision
    arm.send_angles(arm_pick_hover_angle, 50)
    time.sleep(3)

    # rotate to target angle
    # arm.send_angle(6, angle, 50)
    # time.sleep(3)

    coord = coords_transformer.frame2real(x, y)
    coord = list(coord)

    # adjust final offset
    off_x, off_y, off_z = offset_3d
    coord[0] += final_coord_offset[0] + off_x
    coord[1] += final_coord_offset[1] + off_y
    coord[2] += final_coord_offset[2] + off_z + z

    # add angle
    # rz = 90 + (90 - angle)
    rz = 90 + (90 - 10)
    coord.extend([175, 0, rz])

    # send angle
    # move x-y first
    coord_xy = coord.copy()[:3]
    # set z still
    coord_xy[2] = 50
    print(f"X-Y move: {coord_xy}")
    # arm.send_coords(coord_xy, 50, 1)
    position_move(arm, *coord_xy)
    time.sleep(3)

    open_gripper(arm)
    print("Open gripper")
    time.sleep(3)

    # send target angle
    arm.send_coords(coord, 25, 1)
    print(f"Target move: {coord}")
    time.sleep(3)

    close_gripper(arm)
    print("Close gripper")
    time.sleep(3)

    # elevate first
    arm.send_coord(3, 90, 50)
    time.sleep(2)

    arm.send_angles(box_position[color_id], 50)
    time.sleep(3)

    open_gripper(arm)
    print("Open gripper")
    time.sleep(3)
    arm.send_angles(arm_idle_angle, 50)
    time.sleep(4)
    release_gripper(arm)
    time.sleep(0.1)
