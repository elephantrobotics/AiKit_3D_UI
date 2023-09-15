import os
import sys
from pathlib import Path

sys.path.append(str(Path("./libs").resolve()))
os.add_dll_directory(str(Path("./libs").resolve()))

from ObTypes import *
from Property import *
import Context
import Pipeline
import StreamProfile
import Device
from Error import ObException
import cv2
import numpy as np
import sys
import math

q = 113
ESC = 27


# Turn on Depth Streaming and Color Streaming for all devices
def StartStream(pipes):
    for pipe in pipes:
        # Create Config
        config = Pipeline.Config()
        # Get all stream configurations for the color camera,
        # including the stream resolution, frame rate, and frame format
        profiles = pipe.getStreamProfileList(OB_PY_SENSOR_COLOR)
        videoProfile = profiles.getVideoStreamProfile(640, 0, OB_PY_FORMAT_RGB888, 30)
        colorProfile = videoProfile.toConcreteStreamProfile(OB_PY_STREAM_VIDEO)
        config.enableStream(colorProfile)

        # Get all stream configurations for the depth camera,
        # including the stream resolution, frame rate, and frame format
        profiles = pipe.getStreamProfileList(OB_PY_SENSOR_DEPTH)
        videoProfile = profiles.getVideoStreamProfile(640, 0, OB_PY_FORMAT_UNKNOWN, 30)
        depthProfile = videoProfile.toConcreteStreamProfile(OB_PY_STREAM_VIDEO)
        config.enableStream(depthProfile)
        config.setAlignMode(OB_PY_ALIGN_D2C_HW_MODE)
        pipe.start(config, None)


try:
    # Main function entry
    pipes = []
    key = -1

    # Create a Context to get a list of devices
    ctx = Context.Context(None)
    ctx.setLoggerSeverity(OB_PY_LOG_SEVERITY_ERROR)
    devList = ctx.queryDeviceList()
    devCount = devList.deviceCount()

    # Iterate through the list of devices and create a pipe
    # for i in range(devCount):
    # Get the device and create a Pipeline
    dev = devList.getDevice(0)
    pipe = Pipeline.Pipeline(dev, None)
    if pipe.getDevice().isPropertySupported(OB_PY_PROP_DEPTH_MIRROR_BOOL, OB_PY_PERMISSION_WRITE):
        pipe.getDevice().setBoolProperty(OB_PY_PROP_DEPTH_MIRROR_BOOL, True)
    pipes.append(pipe)

    # Turn on depth streaming and color streaming for all devices
    StartStream(pipes)
    buffers = [[None, None] for i in range(len(pipes))]
    current_buffer_index = 0

    isExit = False
    while isExit == False:
        index = 0
        colorDatas = [None] * len(pipes)
        depthDatas = [None] * len(pipes)
        for pipe in pipes:
            frameSet = pipe.waitForFrames(100)
            if frameSet == None:
                continue
            else:
                # Renders a set of frames in the window, here the color frames and depth frames will be rendered
                colorFrame = frameSet.colorFrame()
                depthFrame = frameSet.depthFrame()
                if colorFrame is not None and depthFrame is not None:
                    colorSize = colorFrame.dataSize()
                    colorData = np.asarray(colorFrame.data())
                    depthSize = depthFrame.dataSize()
                    depthData = np.asarray(depthFrame.data())
                    colorWidth = colorFrame.width()
                    colorHeight = colorFrame.height()
                    depthWidth = depthFrame.width()
                    depthHeight = depthFrame.height()
                    if colorData is not None and depthData is not None:
                        colorMat = colorData
                        if colorFrame.format() == OB_PY_FORMAT_MJPG:
                            colorMat = cv2.imdecode(colorMat, 1)
                            if colorMat is not None:
                                colorMat = np.resize(
                                    colorMat, (colorHeight, colorWidth, 3)
                                )
                        elif colorFrame.format() == OB_PY_FORMAT_RGB888:
                            colorMat = np.resize(colorMat, (colorHeight, colorWidth, 3))
                            colorMat = cv2.cvtColor(colorMat, cv2.COLOR_RGB2BGR)
                        elif colorFrame.format() == OB_PY_FORMAT_YUYV:
                            colorMat = np.resize(colorMat, (colorHeight, colorWidth, 2))
                            colorMat = cv2.cvtColor(colorMat, cv2.COLOR_YUV2BGR_YUYV)
                        elif colorFrame.format() == OB_PY_FORMAT_UYVY:
                            colorMat = np.resize(colorMat, (colorHeight, colorWidth, 2))
                            colorMat = cv2.cvtColor(colorMat, cv2.COLOR_YUV2BGR_UYVY)
                        elif colorFrame.format() == OB_PY_FORMAT_I420:
                            colorMat = colorMat.reshape(
                                (colorHeight * 3 // 2, colorWidth)
                            )
                            colorMat = cv2.cvtColor(colorMat, cv2.COLOR_YUV2BGR_I420)
                            colorMat = cv2.resize(colorMat, (colorWidth, colorHeight))

                        depthMat = depthData.reshape((depthHeight, depthWidth, 2))

                        depthMat = depthMat[:, :, 0] + depthMat[:, :, 1] * 256
                        # Conversion of frame data to 1mm units

                        depthMat = depthMat / np.max(depthMat) * 255
                        depthMat = depthMat.astype("uint8")

                        depthMat = cv2.cvtColor(depthMat, cv2.COLOR_GRAY2RGB)

                        depthMat = cv2.resize(depthMat, (colorWidth, colorHeight))

                        # depthMat = cv2.resize(
                        #     depthMat, (depthWidth // 2, depthHeight // 2)
                        # )

                        # Resize the color frame to the same size as the depth frame
                        if colorMat is not None:
                            colorMat = cv2.resize(
                                colorMat, (depthWidth // 2, depthHeight // 2)
                            )
                            colorDatas[index] = colorMat

                        depthDatas[index] = depthMat

                        print(f"color:{colorDatas[index].shape}")
                        print(f"depth:{depthDatas[index].shape}")
                        if (
                                colorDatas[index] is not None
                                and depthDatas[index] is not None
                        ):
                            display = np.vstack((colorDatas[index], depthDatas[index]))
                            # Display the stitched image in the window
                            windowsName = (
                                    str(pipe.getDevice().getDeviceInfo().name(), "utf-8")
                                    + " "
                                    + str(
                                pipe.getDevice().getDeviceInfo().serialNumber(),
                                "utf-8",
                            )
                                    + " color and depth"
                            )
                            cv2.imshow(windowsName, display)

                        key = cv2.waitKey(1)
                        # Press ESC or 'q' to close the window
                        if key == ESC or key == q:
                            isExit = True
                            break
            index += 1

    cv2.destroyAllWindows()

    # Stopping Pipeline and  will no longer generate frame data
    for pipe in pipes:
        pipe.stop()

except ObException as e:
    print(
        "function: %s\nargs: %s\nmessage: %s\ntype: %d\nstatus: %d"
        % (
            e.getName(),
            e.getArgs(),
            e.getMessage(),
            e.getExceptionType(),
            e.getStatus(),
        )
    )
