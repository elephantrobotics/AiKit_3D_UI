import os
import sys
from pathlib import Path


sys.path.append(str(Path(os.path.dirname(__file__)) / Path("libs").resolve()))
os.add_dll_directory(str(Path(os.path.dirname(__file__)) / Path("libs").resolve()))

import Property
from ObTypes import *
import Context
import Pipeline
import time
import numpy as np
import cv2
from configs.config_gripper import *


class ObbrecCamera:
    def __init__(self):
        super().__init__()

        ctx = Context.Context(None)
        ctx.setLoggerSeverity(OB_PY_LOG_SEVERITY_NONE)
        dev_list = ctx.queryDeviceList()
        dev_count = dev_list.deviceCount()
        dev = dev_list.getDevice(0)
        dev.setIntProperty(Property.OB_PY_PROP_DEPTH_MAX_DIFF_INT, 6)
        dev.setIntProperty(Property.OB_PY_PROP_DEPTH_MAX_SPECKLE_SIZE_INT, 50)

        self.pipe = Pipeline.Pipeline(dev, None)
        if self.pipe.getDevice().isPropertySupported(
            Property.OB_PY_PROP_DEPTH_MIRROR_BOOL, OB_PY_PERMISSION_WRITE
        ):
            self.pipe.getDevice().setBoolProperty(
                Property.OB_PY_PROP_DEPTH_MIRROR_BOOL, True
            )

        self.config = Pipeline.Config()

        # setup color pipe
        profiles = self.pipe.getStreamProfileList(OB_PY_SENSOR_COLOR)
        video_profile = profiles.getVideoStreamProfile(640, 0, OB_PY_FORMAT_RGB888, 30)
        color_profile = video_profile.toConcreteStreamProfile(OB_PY_STREAM_VIDEO)
        self.config.enableStream(color_profile)

        # setup depth pipe
        profiles = self.pipe.getStreamProfileList(OB_PY_SENSOR_DEPTH)
        video_profile = profiles.getVideoStreamProfile(640, 0, OB_PY_FORMAT_UNKNOWN, 30)
        depth_profile = video_profile.toConcreteStreamProfile(OB_PY_STREAM_VIDEO)
        self.config.enableStream(depth_profile)

        self.config.setAlignMode(OB_PY_ALIGN_D2C_HW_MODE)

        self.curr_frame = None
        self.curr_frame_time = None
        self.flip_h = True
        self.flip_v = False

    def capture(self):
        self.pipe.start(self.config, None)

    def release(self):
        self.pipe.stop()

    def update_frame(self) -> None:
        pipeline = self.pipe
        frames = pipeline.waitForFrames(100)
        self.curr_frame = frames
        self.curr_frame_time = time.time_ns()

    @classmethod
    def process_color_frame(cls, color_frame):
        color_data = np.asarray(color_frame.data())
        width = color_frame.width()
        height = color_frame.height()

        if color_frame.format() == OB_PY_FORMAT_MJPG:
            color_data = cv2.imdecode(color_data, 1)
            color_data = np.resize(color_data, (height, width, 3))
        elif color_frame.format() == OB_PY_FORMAT_RGB888:
            color_data = np.resize(color_data, (height, width, 3))
            color_data = cv2.cvtColor(color_data, cv2.COLOR_RGB2BGR)
        elif color_frame.format() == OB_PY_FORMAT_YUYV:
            color_data = np.resize(color_data, (height, width, 2))
            color_data = cv2.cvtColor(color_data, cv2.COLOR_YUV2BGR_YUYV)
        elif color_frame.format() == OB_PY_FORMAT_UYVY:
            color_data = np.resize(color_data, (height, width, 2))
            color_data = cv2.cvtColor(color_data, cv2.COLOR_YUV2BGR_UYVY)
        elif color_frame.format() == OB_PY_FORMAT_I420:
            color_data = color_data.reshape((height * 3 // 2, width))
            color_data = cv2.cvtColor(color_data, cv2.COLOR_YUV2BGR_I420)
            color_data = cv2.resize(color_data, (width, height))

        return color_data

    def color_frame(self):
        if self.curr_frame is None or self.curr_frame.colorFrame() is None:
            return None

        color_frame_set = self.curr_frame.colorFrame()
        color_frame = self.process_color_frame(color_frame_set)
        if self.flip_h:
            color_frame = cv2.flip(color_frame, 1)
        if self.flip_v:
            color_frame = cv2.flip(color_frame, 0)
        return color_frame

    def depth_frame(self):
        if self.curr_frame is None or self.curr_frame.depthFrame() is None:
            return None
        depth_frame_set = self.curr_frame.depthFrame()
        depth_data = np.asarray(depth_frame_set.data())
        depth_width = depth_frame_set.width()
        depth_height = depth_frame_set.height()
        depth_frame = depth_data.reshape((depth_height, depth_width, 2))
        depth_frame = depth_frame[:, :, 0] + depth_frame[:, :, 1] * 256
        # Conversion of frame data to 1mm units
        depth_frame = (depth_frame * depth_frame_set.getValueScale()).astype("uint16")

        if self.flip_h:
            depth_frame = cv2.flip(depth_frame, 1)
        if self.flip_v:
            depth_frame = cv2.flip(depth_frame, 0)
        return depth_frame


# Test example
if __name__ == "__main__":
    import os
    import sys

    sys.path.append(os.getcwd())
    from Utils.mouse_callbacks import *
    from Utils.crop_tools import crop_frame
    from configs.config_gripper import *

    cam = ObbrecCamera()
    cam.capture()

    while True:
        cam.update_frame()

        color_frame = cam.color_frame()
        depth_frame = cam.depth_frame()

        if color_frame is None or depth_frame is None:
            time.sleep(0.1)
            continue

        color_frame = crop_frame(color_frame, crop_size, crop_offset)
        depth_frame = crop_frame(depth_frame, crop_size, crop_offset)
        depth_visu_frame = depth_frame.copy()

        color_frame = cv2.resize(color_frame, None, fx=3, fy=3)
        depth_visu_frame = cv2.resize(depth_frame, None, fx=3, fy=3)

        if color_frame is not None:
            depth_visu_frame = depth_visu_frame / np.max(depth_frame) * 255
            depth_visu_frame = depth_visu_frame.astype(np.uint8)

            depth_visu_frame = cv2.cvtColor(depth_visu_frame, cv2.COLOR_GRAY2BGR)
            # frame = np.hstack([color_frame, depth_frame])
            cv2.imshow("Color", color_frame)
            bind_mouse_event(color_frame, "Color", mouseHSV)

            cv2.imshow("Depth", depth_visu_frame)
            bind_mouse_event(depth_frame, "Color", mouseDepth)

        cv2.waitKey(1)
