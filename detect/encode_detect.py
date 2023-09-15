#!/usr/bin/python
# -*- coding:utf-8 -*-
# @File    : encode_detect.py
# @Author  : Wang Weijian
# @Time    :  2023/09/09 14:26:00
# @function: aruco code recognition algorithm script
# @version : V1

import cv2
import numpy as np
from typing import Tuple, Any
import sys
import os
from typing import *
from dataclasses import dataclass, astuple

sys.path.append(os.getcwd())

from Utils.vision_tools import get_angle_from_rect


class ArucoDetector:
    @dataclass
    class DetectResult:
        ids: int
        corners: np.ndarray

        def __iter__(self):
            return iter(astuple(self))

    def __init__(self) -> None:
        self.area_low_threshold = 15000
        self.detected_name = None

    def get_radian(self, res: DetectResult):
        return get_angle_from_rect(res.corners) / 180 * np.pi

    def detect(self, frame: np.ndarray):
        """Detect certain color in HSV color space, return targets min bounding box.

        Args:
            frame (np.ndarray): Src frame

        Returns:
            List[Tuple[int, int, int, int]] | None: list of bounding box or empty list
        """
        result = []
        # Load camera calibration parameters
        camera_matrix = np.array(
            [[452.2630920410156, 0.0, 317.03485107421875], [0.0, 452.2630920410156, 241.24710083007812],
             [0.0, 0.0, 1.0]])
        distortion_coefficients = np.array(([[0.049957774579524994, -0.06437692791223526, 0.0, 0.0, 0.0]]))
        # Initialize ArUco detector
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        parameters = cv2.aruco.DetectorParameters()
        # transfrom the img to model of gray
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Preprocess the image (e.g. remove distortion)
        if camera_matrix is not None and distortion_coefficients is not None:
            frame = cv2.undistort(gray, camera_matrix, distortion_coefficients)
        # Detect ArUco code
        corners, ids, _ = cv2.aruco.detectMarkers(frame, aruco_dict, parameters=parameters)

        rects = list(map(np.int32, corners))
        if ids is not None:
            # Mark the detected ArUco code
            self.detected_name = ids[0][0]
            result.append(ArucoDetector.DetectResult(ids, rects))
            # cv2.aruco.drawDetectedMarkers(frame, corners, ids, borderColor=(0, 255, 0))
        return result

    def draw_result(self, frame: np.ndarray, res: List[DetectResult]):
        for obj in res:
            contours = np.squeeze(obj.corners)
            cv2.drawContours(frame, [contours], -1, (0, 0, 255), 3)

            text = 'ids:{}'.format(obj.ids[0][0])
            cv2.putText(
                frame,
                str(text),
                self.target_position(obj),
                fontFace=cv2.FONT_HERSHEY_COMPLEX,
                fontScale=1,
                color=(0, 255, 0),
                thickness=1,
            )

    def target_position(self, res: DetectResult) -> Tuple[int, int]:
        pos = np.mean(np.array(res.corners), axis=0).astype(np.int32)
        # Calculate the average of the four corner points to get the center coordinates
        center_x = int(np.mean(pos[0, :, 0]))
        center_y = int(np.mean(pos[0, :, 1]))
        return center_x, center_y

    def get_rect(self, res: DetectResult):
        return res.corners
