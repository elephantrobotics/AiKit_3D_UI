#!/usr/bin/python
# -*- coding:utf-8 -*-
# @File    : test.py
# @Author  : Wang Weijian
# @Time    :  2023/09/04 11:05:44
# @function: the script is used to do something
# @version : V1

import numpy as np

from  pymycobot.mecharm import MechArm

# mc = MechArm('COM27', 115200)
# print(mc.get_coords())
# mc.send_coords([172.4, -6.092307692307693, 80, -177, 0, 90], 50)

obj_config = [([[[161, 97], [167, 97], [167, 103], [161, 103]], [[182, 282], [188, 282], [188, 288], [182, 288]]], ((164, 100), (185, 285)))]
print(type(obj_config))
# for obj in obj_config:
#     print(obj)
#     rect, (x, y) = obj
#     rect = np.array(rect)
#     print('rect:', type(rect), rect)
#     print('x,y:', type((x,y)), (x,y))

# 示例数据
data = ((393.0, 394.0, 395.0), ((311, 217), (170, 160), (149, 264)))

# 提取深度值和坐标点
depth_values = data[0]
coordinate_tuples = data[1]

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

x, y = matched_coordinates
print('x, y:', x, y)

if matched_coordinates:
    print(f"深度值 {depth_to_match} 对应的坐标点是 {matched_coordinates}")
else:
    print(f"未找到深度值 {depth_to_match} 对应的坐标点")

import random

# 生成随机数字，包括0、1、2和3
random_number = random.randint(0, 3)

print(random_number)

import numpy as np

# 原始的四维数组
four_dim_array = [[[[277, 124], [250, 282], [94, 256], [119, 100]]]]

# # 提取坐标点到一个列表
# coordinates = []
# for polygon in four_dim_array:
#     for contour in polygon:
#         for point in contour:
#             coordinates.append(tuple(point))
# print(coordinates)
# # 将列表转换为二维数组
# polygon_vertices = np.array(coordinates, dtype=np.int32)
# print(polygon_vertices)
# 现在，polygon_vertices 是一个二维数组，可以传递给 cv2.fillPoly 函数

import numpy as np

# 给定四个角点的像素坐标
corners = np.array([[[119, 281], [103, 131], [251, 120], [268, 268]]])

# 计算四个角点的平均值，以获得中心坐标
center_x = int(np.mean(corners[0, :, 0]))
center_y = int(np.mean(corners[0, :, 1]))

# 打印中心坐标
print("Aruco码中心坐标 (x, y):", center_x, center_y)
