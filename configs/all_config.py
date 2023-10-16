#!/usr/bin/python
# -*- coding:utf-8 -*-
# @File    : all_config.py
# @Author  : Wang Weijian
# @Time    :  2023/09/12 18:06:10
# @function: the script is used to do something
# @version : V1

arm_serial_port = "COM27"
# arm_idle_angle = [-90, 0, 0, 0, 90, 0]
# arm_pick_hover_angle_pump = [0, 30, -27, 0, 90, 90]
# arm_pick_hover_angle_gripper = [0, 30, -27, 0, 90, 0]

arm_idle_angle=[-40,0,-80,0,0,0] # 280
arm_pick_hover_angle_pump=[15,15,-97,0,0,0] #280
arm_pick_hover_angle_gripper = [15,15,-97,0,0,0] #280

# 裁剪目标正方形的边长
crop_size = 135

# 缩放系数
zoom_factor = 3

# 最终帧大小
# 因为特征点识别的需要，所以要缩放图像到更大的尺寸，方便提取特征
final_frame_size = crop_size * zoom_factor

# 裁剪偏移，裁剪出Camera Zone
# crop_offset = (-25, -40)
crop_offset = (20, -12)
# 目标平面的实际大小
# target_plan_real_world_size = 105
target_plan_real_world_size = 108

# 平面像素大小与实际大小（毫米）的比例
plane_frame_size_ratio = target_plan_real_world_size / final_frame_size

# Calc的坐标平面中心参数
target_base_pos3d_pump = (135, 0, -25)
target_base_pos3d_gripper = (160, 0, -33)

# 最终坐标偏移量
final_coord_offset = [0, 0, 0]
# camera distance to floor
floor_depth = 385

# 工具坐标系
tool_frame_pump = [0, 0, 80, 0, 0, 0]
tool_frame_gripper = [0, -10, 80, 0, 0, 0]

# 放置位置
box_position = [
    # [-48.86, 28.21, -16.25, 0.17, 66.7, 0.0],  # Bin D
    # [-30.93, 49.04, -46.23, 0.43, 49.04, 0.26],  # Bin C
    # [51.67, 24.6, -7.38, 0.0, 53.87, -0.26],  # Bin A
    # [88.06, 15.46, 0.79, 0.61, 68.02, 0.35],  # Bin B


    [-28.65,-7.11,-103.35,26.01,-1.4,-142.47],
    [-14.76,-44.12,-51.06,20.56,0.87,-142.47],
    
    [66.44,-17.84,-79.98,12.91,4.3,-142.47],
    [106.08,12.48,-104.76,5.88,1.23,-143.61]
]


