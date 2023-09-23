from typing import Tuple, Optional
import pyrealsense2 as rs
import numpy as np
import cv2
import time

# Tested with camera D400


class RealSenseCamera:
    def __init__(self):
        super().__init__()

        # Configure depth and color streams
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30)
        self.flip_h = True
        self.flip_v = True

        # Get device product line for setting a supporting resolution
        pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        pipeline_profile = self.config.resolve(pipeline_wrapper)
        # set auto exposure
        color = pipeline_profile.get_device().query_sensors()[0]
        color.set_option(rs.option.enable_auto_exposure, True)

        device = pipeline_profile.get_device()

        sensor_infos = list(
            map(lambda x: x.get_info(rs.camera_info.name), device.sensors)
        )

        # set resolution
        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)

        align_to = rs.stream.color
        self.align = rs.align(align_to)

    def capture(self):
        # Start streaming
        self.pipeline.start(self.config)

        # warm up
        for i in range(60):
            pipeline = self.pipeline
            frames = pipeline.wait_for_frames()

    def release(self):
        self.pipeline.stop()

    def update_frame(self) -> None:
        pipeline = self.pipeline
        frames = pipeline.wait_for_frames()
        aligned_frames = self.align.process(frames)
        self.curr_frame = aligned_frames
        self.curr_frame_time = time.time_ns()

    def color_frame(self) -> Optional[np.ndarray]:
        frame = self.curr_frame.get_color_frame()
        if not frame:
            return None
        frame = np.asanyarray(frame.get_data())
        if self.flip_h:
            frame = cv2.flip(frame, 1)
        if self.flip_v:
            frame = cv2.flip(frame, 0)
        return frame

    def depth_frame(self) -> Optional[np.ndarray]:
        frame = self.curr_frame.get_depth_frame()
        if not frame:
            return None
        frame = np.asanyarray(frame.get_data())
        if self.flip_h:
            frame = cv2.flip(frame, 1)
        if self.flip_v:
            frame = cv2.flip(frame, 0)
        return frame


# Test example
if __name__ == "__main__":
    import os
    import sys

    sys.path.append(os.getcwd())
    from Utils.mouse_callbacks import *
    from Utils.crop_tools import crop_frame
    from configs.config_gripper import *

    cam = RealSenseCamera()
    cam.capture()

    while True:
        cam.update_frame()

        color_frame = cam.color_frame()
        color_frame = crop_frame(color_frame, crop_size, crop_offset)
        color_frame = cv2.resize(color_frame, None, fx=3, fy=3)
        if color_frame is not None:
            cv2.imshow("Color", color_frame)
            bind_mouse_event(color_frame, "Color", mouseHSV)

        cv2.waitKey(1)
