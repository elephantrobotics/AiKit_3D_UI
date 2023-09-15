import numpy as np
from numpy.typing import NDArray
from typing import Tuple
import cv2


def Rx(theta):
    return np.array(
        [
            [1, 0, 0],
            [0, np.cos(theta), -np.sin(theta)],
            [0, np.sin(theta), np.cos(theta)],
        ]
    )


def Ry(theta):
    return np.array(
        [
            [np.cos(theta), 0, np.sin(theta)],
            [0, 1, 0],
            [-np.sin(theta), 0, np.cos(theta)],
        ]
    )


def Rz(theta):
    return np.array(
        [
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0],
            [0, 0, 1],
        ]
    )


def degree2radian(degree):
    return (degree / 180) * np.pi


def rotation_matrix(rx, ry, rz, order="ZYX"):
    order = order.upper()
    if len(order) != 3 or set(order) != set("XYZ"):
        raise Exception("Order must be string of component of XYZ or xyz")
    mat = np.identity(3)
    rx = degree2radian(rx)
    ry = degree2radian(ry)
    rz = degree2radian(rz)
    for c in order:
        if c == "X":
            mat = mat @ Rx(rx)
        elif c == "Y":
            mat = mat @ Ry(ry)
        elif c == "Z":
            mat = mat @ Rz(rz)
    return mat


def homo_transform_matrix(x, y, z, rx, ry, rz, order="ZYX"):
    rot_mat = rotation_matrix(rx, ry, rz, order=order)
    trans_vec = np.array([[x, y, z, 1]]).T
    mat = np.vstack([rot_mat, np.zeros((1, 3))])
    mat = np.hstack([mat, trans_vec])
    return mat


def get_angle_from_rect(corners : NDArray) -> int:
    center, size, angle = cv2.minAreaRect(corners)
    return angle


if __name__ == "__main__":
    corners = np.array([(0, 40), (40, 40), (0, 0), (40, 0)])
    get_angle_from_rect(corners)
