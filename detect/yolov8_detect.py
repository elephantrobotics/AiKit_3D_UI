import os

import cv2
from ultralytics import YOLO
import ultralytics
from dataclasses import dataclass, astuple
import numpy as np
from typing import List, Tuple
from Utils.vision_tools import get_angle_from_rect

class YOLODetector:
    DetectResult = List[ultralytics.engine.results.Results]

    def __init__(self) -> None:
        """
        init YOLO model。
        """
        self.model_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/resources/yolo/best.pt'
        self.model = YOLO(self.model_path)
        self.predict_args = {"conf": 0.2}

        self.detected_name = None

    def get_radian(self, res: DetectResult):
        return 0

    def detect(self, frame: np.ndarray):
        """
        Perform object detection on input images.

        Args:
            frame (np.ndarray): Input image frame.

        Returns:
            List[DetectResult]: A list containing the detection results.
        """
        res = self.model.predict(frame, **self.predict_args)
        res = list(filter(lambda x: len(x.boxes) != 0, res))
        if len(res) == 0:
            return None
        else:
            names = self.get_names(res)
            self.detected_name = names
            return res

    def draw_result(self, frame: np.ndarray, res: List[DetectResult]):
        """
        Draws the bounding box of the detection results on the image.

        Args:
             frame (np.ndarray): Input image frame.
             res (List[DetectResult]): List of detection results.
        """
        res = list(filter(lambda x: len(x.boxes) != 0, res))
        for r in res:
            boxes = r.boxes.xyxy.numpy()
            for box in boxes:
                x1, y1, x2, y2 = box.astype(int)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=1)
                cv2.putText(frame, "Name: " + str(self.detected_name), (20, 80),
                            cv2.FONT_HERSHEY_COMPLEX_SMALL, 1,
                            (0, 0, 255))
            # x1, y1, x2, y2 = np.squeeze(r.boxes.xyxy.numpy()).astype(int)
            # cv2.rectangle(frame, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=1)

    def target_position(self, res: DetectResult) -> Tuple[int, int]:
        """
        Extract the location information of the target from the detection results.

         Args:
             res (DetectResult): detection result.

         Returns:
             Tuple[int, int]: The position coordinates (x, y) of the target.
        """
        boxes = res.boxes.xywh.numpy()
        boxs_list = []
        for box in boxes:
            x, y, w, h = box.astype(int)  #x, y for target position
            boxs_list.append((x, y))
        boxs_list = tuple(boxs_list)
        return boxs_list

    def get_rect(self, res: DetectResult):
        """
        Obtain the bounding box coordinate information of the target from the detection result.

        Args:
             res (DetectResult): detection result.

         Returns:
             List[Tuple[int, int]]: The bounding box coordinate information of the target, including four vertex coordinates.
        """
        boxes = res.boxes.xywh.numpy()
        box_list = []
        for box in boxes:
            x, y, w, h = box.astype(int)
            size = 3
            rect = [
                [x - size, y - size],
                [x + size, y - size],
                [x + size, y + size],
                [x - size, y + size],
            ]
            box_list.append(rect)
        return box_list

    def get_names(self, res: DetectResult):
        """
        Get the category name in the detection results

        Args:
             res (DetectResult): detection result.

         Returns:
             List[names]: A list category names.
        """
        names_dict = {
            0: 'jeep', 1: 'apple', 2: 'banana1', 3: 'bed', 4: 'grape',
            5: 'laptop', 6: 'microwave', 7: 'orange', 8: 'pear',
            9: 'refrigerator1', 10: 'refrigerator2', 11: 'sofa', 12: 'sofa2',
            13: 'tv', 14: 'washing machine1'
        }

        ids = [int(cls) for cls in res[0].boxes.cls.numpy()]  # Assuming you have only one result in the list
        names = [names_dict.get(id, 'Unknown') for id in ids]

        return names
