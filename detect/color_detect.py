import cv2
import numpy as np
from typing import Tuple, Any
import sys
import os
from typing import *
from dataclasses import dataclass, astuple

sys.path.append(os.getcwd())

from Utils.vision_tools import get_angle_from_rect


class ColorDetector:
    @dataclass
    class DetectResult:
        color: str
        corners: np.ndarray

        def __iter__(self):
            return iter(astuple(self))

    def __init__(self) -> None:
        self.area_low_threshold = 15000
        self.detected_name = None
        self.hsv_range = {
            "green": ((40, 50, 50), (90, 256, 256)),
            # "blueA": ((91, 100, 100), (105, 256, 256)),
            # "yellow": ((20, 240, 170), (30, 256, 256)),
            "yellow": ((15, 46, 43), (30, 256, 256)),
            "redA": ((0, 100, 100), (6, 256, 256)),
            "redB": ((170, 100, 100), (179, 256, 256)),
            # "orange": ((8, 100, 100), (15, 256, 256)),
            "blue": ((100, 43, 46), (124, 256, 256)),
        }

    def get_radian(self, res: DetectResult):
        return get_angle_from_rect(res.corners) / 180 * np.pi

    def detect(self, frame: np.ndarray):
        """Detect certain color in HSV color space, return targets min bounding box.

        Args:
            frame (np.ndarray): Src frame
            hsv_low (Tuple[int, int, int]): HSV lower bound
            hsv_high (Tuple[int, int, int]): HSV high bound

        Returns:
            List[Tuple[int, int, int, int]] | None: list of bounding box or empty list
        """
        result = []
        for color, (hsv_low, hsv_high) in self.hsv_range.items():
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            in_range = cv2.inRange(hsv_frame, hsv_low, hsv_high)

            # 对颜色区域进行膨胀和腐蚀
            kernel = np.ones((5, 5), np.uint8)
            in_range = cv2.morphologyEx(in_range, cv2.MORPH_CLOSE, kernel)
            in_range = cv2.morphologyEx(in_range, cv2.MORPH_OPEN, kernel)

            contours, hierarchy = cv2.findContours(
                in_range, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            contours = list(
                filter(lambda x: cv2.contourArea(x) > self.area_low_threshold, contours)
            )

            rects = list(map(cv2.minAreaRect, contours))
            boxes = list(map(cv2.boxPoints, rects))
            boxes = list(map(np.int32, boxes))

            if len(boxes) != 0:
                if color.startswith("red"):
                    color = "red"
                for box in boxes:
                    result.append(ColorDetector.DetectResult(color, box))
                    # self.detected_name = result
                    self.detected_name = result[0].color
        return result

    def draw_result(self, frame: np.ndarray, res: List[DetectResult]):
        for obj in res:
            cv2.drawContours(frame, [obj.corners], -1, (0, 0, 255), 3)
            cv2.putText(
                frame,
                obj.color,
                self.target_position(obj),
                fontFace=cv2.FONT_HERSHEY_COMPLEX,
                fontScale=1,
                color=(0, 255, 0),
                thickness=1,
            )

    def target_position(self, res: DetectResult) -> Tuple[int, int]:
        pos = np.mean(np.array(res.corners), axis=0).astype(np.int32)
        x, y = pos
        return x, y

    def get_rect(self, res: DetectResult):
        return res.corners
