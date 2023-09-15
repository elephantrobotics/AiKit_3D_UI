import numpy as np
from typing import Tuple
import cv2


def crop_frame(frame: np.ndarray, size: int, offset_2d: Tuple[int, int] = (0, 0)):
    """Crop a square area of size (size) in frame center

    Args:
        frame (np.ndarray): _description_
        size (int): _description_
        offset_2d (Tuple[int, int], optional): _description_. Defaults to (0, 0).

    Returns:
        _type_: _description_
    """
    offset_2d = offset_2d[1], offset_2d[0]

    size_x, size_y = frame.shape[:2]
    center_pos = np.array([size_x // 2, size_y // 2])
    center_pos += np.array(offset_2d)

    left_top_x, left_top_y = center_pos - size // 2

    if len(frame.shape) == 3:
        croped_frame = frame[
            left_top_x : left_top_x + size, left_top_y : left_top_y + size, :
        ]
    elif len(frame.shape) == 2:
        croped_frame = frame[
            left_top_x : left_top_x + size, left_top_y : left_top_y + size
        ]
    else:
        raise Exception(
            f"Frame shape not correct, expect [x,y,c] or [x,y] ,got {frame.shape}"
        )

    return croped_frame


def crop_poly(frame: np.ndarray, ploy_vertices: np.ndarray) -> np.ndarray:
    mask = np.zeros(frame.shape, dtype=np.uint8)
    cv2.fillPoly(mask, [ploy_vertices], 255)
    polygon_region = cv2.bitwise_and(frame, frame, mask=mask)
    return polygon_region
