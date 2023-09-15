import os
import sys
import threading
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