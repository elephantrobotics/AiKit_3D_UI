import time

import cv2
import numpy as np
from typing import Tuple, Any, List
import math
from enum import Enum
from dataclasses import dataclass, astuple
import sys
import os

sys.path.append(os.getcwd())

from Utils.vision_tools import get_angle_from_rect


class ObjectShapeType(Enum):
    triangle = "Triangle"
    square = "Square"
    rectangle = "Rectangle"
    circle = "Circle"


class ShapeDetector:
    @dataclass
    class ShapeDetectResult:
        object_type: ObjectShapeType
        cnt: np.ndarray
        pos2d: Tuple[int, int]

        def __iter__(self):
            return iter(astuple(self))

    def __init__(self) -> None:
        self.area_low_threshold = 1000
        self.detected_name = None

    def detect(self, frame) -> List[ShapeDetectResult]:
        x = 0
        y = 0

        # filter out low bright pixel
        Alpha = 20
        Gamma = -120 * 20
        cal = cv2.addWeighted(frame, Alpha, frame, 0, Gamma)

        # convert to gray scale
        gray = cv2.cvtColor(cal, cv2.COLOR_BGR2GRAY)

        # open operation to filter out noise
        gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, np.ones((3, 3)))

        erosion = cv2.erode(gray, np.ones((2, 2), np.uint8), iterations=2)

        # the image for expansion operation, its role is to deepen the color depth in the picture
        dilation = cv2.dilate(erosion, np.ones(
            (1, 1), np.uint8), iterations=2)

        # 设定灰度图的阈值, 把点值统一化
        _, threshold = cv2.threshold(dilation, 175, 255, cv2.THRESH_BINARY)
        # 边缘检测
        edges = cv2.Canny(threshold, 50, 100)
        # 检测物体边框
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # No contour detected
        if len(contours) == 0:
            return None

        res: List[ShapeDetector.ShapeDetectResult] = []

        for cnt in contours:
            if cv2.contourArea(cnt) < 13000:
                continue
            # print('area:', cv2.contourArea(cnt))
            # PolyDP
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            objCor = len(approx)

            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            box = np.int0(box)

            x = int(rect[0][0])
            y = int(rect[0][1])
            # print('xyxy:', objCor)
            if objCor == 3:
                objectType = ObjectShapeType.triangle
                res.append(self.ShapeDetectResult(objectType, cnt, (x, y)))

            elif objCor == 4:
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                _W = math.sqrt(
                    math.pow((box[0][0] - box[1][0]), 2)
                    + math.pow((box[0][1] - box[1][1]), 2)
                )
                _H = math.sqrt(
                    math.pow((box[0][0] - box[3][0]), 2)
                    + math.pow((box[0][1] - box[3][1]), 2)
                )
                aspRatio = _W / float(_H)

                if 0.98 < aspRatio < 1.03:
                    objectType = ObjectShapeType.square
                    res.append(self.ShapeDetectResult(objectType, cnt, (x, y)))
                else:
                    objectType = ObjectShapeType.rectangle
                    res.append(self.ShapeDetectResult(objectType, cnt, (x, y)))

            elif objCor >= 5:
                objectType = ObjectShapeType.circle
                res.append(self.ShapeDetectResult(objectType, cnt, (x, y)))
            else:
                pass
            for result in res:
                self.detected_name = result.object_type.value
                print("Detected shape:", self.detected_name)
        return res

    @classmethod
    def draw_result(cls, frame, res: List[ShapeDetectResult]):
        if frame is None:
            return
        for e in res:
            objType, cnt, (x, y) = e
            cv2.drawContours(frame, [cnt], -1, (0, 0, 255), 3)
            cv2.putText(
                frame,
                f"{objType.value}",
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                1,
                cv2.LINE_AA,
            )

    def target_position(self, res: ShapeDetectResult) -> Tuple[int, int]:
        x, y = res.pos2d
        return x, y

    def get_rect(self, res: ShapeDetectResult):
        return res.cnt

    def get_radian(self, res: ShapeDetectResult):
        return get_angle_from_rect(res.cnt)
