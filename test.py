import os
import sys
import threading
import time
import traceback
from pathlib import Path

sys.path.append(str(Path("./libs").resolve()))
os.add_dll_directory(str(Path("./libs").resolve()))
print(sys.path)
import Device

print("OK")

'''
@pyqtSlot(QImage)
def update_image(self, image):
    # 在主线程中更新UI元素
    pixmap = QPixmap.fromImage(image)
    self.show_camera_lab_rgb.setPixmap(pixmap.scaled(390, 390))

@pyqtSlot(QImage)
def update_processed_image(self, image):
    # 在主线程中更新UI元素
    pixmap = QPixmap.fromImage(image)
    self.show_camera_lab_depth.setPixmap(pixmap.scaled(390, 390))


class CameraVideoThread(QThread):
    """"
    颜色、图像、特征点、yolov5等识别的摄像头线程类
    """
    frame_signal = pyqtSignal(QImage)
    processed_frame_signal = pyqtSignal(QImage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        # 日志信息
        self.log = MyLogging().logger

    def run(self):
        self.running = True
        while self.running:
            try:
                time.sleep((0.1))  # 需修改为标志位
                if AiKit_window.color_frame is not None and AiKit_window.depth_frame is not None:
                    # rgb转为qt图像
                    rgb = AiKit_window.color_frame
                    rgb_show = QImage(rgb, rgb.shape[1], rgb.shape[0], QImage.Format.Format_BGR888)
                    # height, width, channel = rgb.shape
                    # bytes_per_line = 3 * width  # 3 通道 RGB 图像
                    # qimage = QImage(rgb.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)

                    # 发送rgb图像信号给主线程
                    self.frame_signal.emit(rgb_show)

                    # depth转为qt图像
                    depth = AiKit_window.depth_frame
                    depth_show = QImage(depth, depth.shape[1], depth.shape[0], QImage.Format.Format_BGR888)
                    # height, width, channel = depth.shape
                    # bytes_per_line = 3 * width  # 3 通道 RGB 图像
                    # qimage = QImage(depth.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
                    # 发送depth图像信号给主线程
                    self.processed_frame_signal.emit(depth_show)
            except Exception as e:
                e = traceback.format_exc()
                self.log.error(e)

'''

from pymycobot.mecharm import MechArm
from Utils.arm_controls import *
from configs.all_config import *

mc = MechArm('COM27', 115200)

is_coords = True


def robot_pick_move():
    for i in range(100):
        print('开始第{}次'.format(i + 1))
        mc.send_angles([0, 30, -27, 0, 90, 90], 50)
        time.sleep(3)

        mc.send_coords([166.8, 8.8, 20, -177, 0, 90], 40, 1)
        time.sleep(3)

        pump_on(mc)
        time.sleep(1.5)
        mc.send_coord(3, 90, 40)
        time.sleep(3)

        mc.send_angles(box_position[3], 50)
        time.sleep(3)
        pump_off(mc)
        time.sleep(1.5)
        mc.send_angles([-90, 0, 0, 0, 90, 0], 50)
        time.sleep(4)


def get_data_coords():
    while is_coords:
        try:
            coord = mc.get_coords()
        except Exception as e:
            e = traceback.format_exc()
            coord = []
            pass
        if coord and len(coord) == 6:
            coord = 'X: {} Y: {} Z: {} Rx: {} Ry: {} Rz: {}'.format(coord[0], coord[1], coord[2], coord[3],
                                                                    coord[4],
                                                                    coord[5])
            print('coord:{}'.format(coord))
        time.sleep(0.2)


def crawl_move_thread():
    # 获取锁
    crawl_move_lock = threading.Lock()
    crawl_move_lock.acquire()
    try:
        # 执行需要加锁的操作
        robot_pick_move()
    finally:
        # 释放锁
        crawl_move_lock.release()


thread = threading.Thread(target=robot_pick_move)
thread.start()

coord = threading.Thread(target=get_data_coords)
coord.start()

# mc.send_angles([0, 30, -27, 0, 90, 90], 50)
# time.sleep(3)
# status = mc.is_in_position([0, 30, -27, 0, 90, 90], 0)
# print(status)
# if status:
#     print('已到达')
# else:
#     print(mc.get_angles())
#     print('未到达')
#
# print(mc.get_angles())
# time.sleep(0.1)
# print(mc.get_error_information())

# mc.send_coords([135, 0, -25, 179.9, -9.22, 179.99], 40, 1)
