import cv2
import numpy as np


def get_angle_from_rect(corners: np.ndarray) -> int:
    center, size, angle = cv2.minAreaRect(corners)
    angle = angle - 360 if angle > 360 else angle
    return angle
