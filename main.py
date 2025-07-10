#!/usr/bin/python
# -*- coding:utf-8 -*-
# @File    : main.py
# @Author  : Wang Weijian
# @Time    :  2023/09/12 09:57:48
# @function: The main program run by AiKit 3D UI
# @version : V1.0

import os
import random
import sys
import threading
import time
import traceback

import cv2
import numpy as np
import serial
import serial.tools.list_ports
from PyQt6.QtCore import Qt, pyqtSlot, QDateTime, QRegularExpression, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QPixmap, QRegularExpressionValidator, QImage
from PyQt6.QtWidgets import QMainWindow, QWidget, QApplication, QMessageBox, QPushButton
from PyQt6.sip import isdeleted

from Utils.coord_calc import CoordCalc

sys.path.append(os.getcwd())

from resources.ui.AiKit_3D import Ui_AiKit_UI as AiKit_window
from resources.log.logfile import MyLogging
from configs.all_config import *
from Utils.arm_controls import *
from detect.shape_detect import ShapeDetector
from detect.color_detect import ColorDetector
from detect.yolov8_detect import YOLODetector
from ObbrecCamera import ObbrecCamera
from Utils.crop_tools import crop_frame, crop_poly
import pymycobot
from packaging import version

# min low version require
MIN_REQUIRE_VERSION = '3.6.3'

current_verison = pymycobot.__version__
print('current pymycobot library version: {}'.format(current_verison))
if version.parse(current_verison) < version.parse(MIN_REQUIRE_VERSION):
    raise RuntimeError(
        'The version of pymycobot library must be greater than {} or higher. The current version is {}. Please upgrade the library version.'.format(
            MIN_REQUIRE_VERSION, current_verison))
else:
    print('pymycobot library version meets the requirements!')
    from pymycobot import MyCobot280, MyCobot280Socket


class AiKit_App(AiKit_window, QMainWindow, QWidget):
    choose_function_signal = pyqtSignal()
    set_button_color = pyqtSignal(QPushButton, str)
    update_btn_state = pyqtSignal(QObject, bool)  # 对象 + 状态（True/False）
    update_rgb_signal = pyqtSignal(QPixmap)
    update_depth_signal = pyqtSignal(QPixmap)

    def __init__(self):
        super(AiKit_App, self).__init__()
        self.setupUi(self)
        # 去掉窗口顶部边框
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        self.min_btn.clicked.connect(self.min_clicked)
        self.close_btn.clicked.connect(self.close_clicked)
        self.language_btn.clicked.connect(self.set_language)
        self.comboBox_function.highlighted.connect(self.choose_function)
        self.comboBox_function.activated.connect(self.choose_function)
        # self.comboBox_port.highlighted.connect(self.get_serial_port_list)
        # self.comboBox_port.activated.connect(self.get_serial_port_list)
        # self.comboBox_baud.highlighted.connect(self.baud_choose)
        # self.comboBox_baud.activated.connect(self.baud_choose)
        self.connect_btn.clicked.connect(self.connect_checked)

        self.to_origin_btn.clicked.connect(self.go_home_function)
        self.offset_save_btn.clicked.connect(self.insert_offset)

        self.discern_btn.clicked.connect(self.discern_function)
        self.crawl_btn.clicked.connect(self.crawl_function)
        self.place_btn.clicked.connect(self.place_function)
        self.current_coord_btn.clicked.connect(self.get_current_coords_btn)
        self.image_coord_btn.clicked.connect(self.get_img_coords_btn)
        self.open_camera_btn.clicked.connect(self.camera_checked)
        self.add_support_robot_types()
        # self.M5 = ['mechArm 270 for M5']
        self.PI = ['myCobot 280 for PI']
        self.mc = None
        self.port_list = []
        self.logger = MyLogging().logger
        self.offset_x, self.offset_y, self.offset_z = 0, 0, 0
        self.pos_x, self.pos_y, self.pos_z = 0, 0, 0

        # 记录鼠标按下时的位置
        self.dragPos = None
        self.lastTime = None
        self.language = 1  # Control language, 1 is English, 2 is Chinese
        if self.language == 1:
            self.btn_color(self.language_btn, 'green')
        else:
            self.btn_color(self.language_btn, 'blue')
        self.is_language_btn_click = False
        self.is_go_home = False
        self.is_discern = False
        self.is_crawl = False
        self.is_place = False
        self.is_pick = True
        self.is_current_coords = False
        self.is_img_coords = False
        self.is_open_camera = False
        self.is_connected = False
        self.radioButton_A.setChecked(True)
        self.color_frame = None
        self.depth_frame = None
        self.algorithm_mode = None
        self.open_camera = None
        self.detect_thread = None
        self.show_camera_lab_depth.hide()
        self.show_camera_lab_rgb.hide()

        # 创建一个锁对象
        self.crawl_move_lock = threading.Lock()

        self.is_thread_running = True
        self.algorithm_pump = ['Color recognition pump', 'Shape recognition pump', 'yolov8 pump', 'Depalletizing pump',
                               '颜色识别 吸泵', '形状识别 吸泵', 'yolov8 吸泵', '拆码垛 吸泵']
        self.algorithm_gripper = ['Color recognition gripper', 'yolov8 gripper', '颜色识别 夹爪', 'yolov8 夹爪']
        self._init_main_window()
        self.choose_function()
        # self.get_serial_port_list()
        # self.baud_choose()
        self.init_btn_status(False)
        self.init_offset_tooltip()
        self.offset_change()
        # self.ip_lineEdit.setPlaceholderText("例如：192.168.1.100")
        # 信号
        self.choose_function_signal.connect(self.choose_function)
        self.set_button_color.connect(lambda btn, color: self.btn_color(btn, color))
        self.update_btn_state.connect(self.set_btn_enabled)

        self.update_rgb_signal.connect(self.show_camera_lab_rgb.setPixmap)
        self.update_depth_signal.connect(
            lambda pixmap: self.show_camera_lab_depth.setPixmap(pixmap.scaled(390, 390))
        )
        # 创建正则表达式验证器
        port_validator = QRegularExpressionValidator()
        ip_validator = QRegularExpressionValidator()
        # 设置正则表达式
        port_validator.setRegularExpression(
            QRegularExpression("^(?:[0-9]|[1-9][0-9]{1,3}|[1-5][0-9]{4}|6[0-5][0-5][0-3][0-5])$"))
        ip_validator.setRegularExpression(QRegularExpression(
            r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"))
        self.ip_lineEdit.setValidator(ip_validator)
        self.port_lineEdit.setValidator(port_validator)
        # self.ip_lineEdit.setText('192.168.123.226')

    def _init_main_window(self):
        """
        加载窗口logo图标、最小化按钮图标、关闭按钮图标
        Returns: None

        """
        try:
            self.pix = QPixmap(libraries_path + '/img/logo.ico')  # the path to the icon
            self.logo_lab.setPixmap(self.pix)
            self.logo_lab.setScaledContents(True)

            # Close, minimize button display text
            self.min_btn.setStyleSheet("border-image: url({}/img/min.ico);".format(libraries_path))
            self.close_btn.setStyleSheet("border-image: url({}/img/close.ico);".format(libraries_path))
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    @pyqtSlot()
    def close_clicked(self):
        self.close()
        QApplication.instance().quit()

    @pyqtSlot()
    def min_clicked(self):
        # minimize
        self.showMinimized()

    def mousePressEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and event.pos().y() < 50:
            self.dragPos = event.pos()
            self.lastTime = QDateTime.currentDateTime()

    def mouseMoveEvent(self, event):
        """添加一个计时器，限制窗口移动的最小时间间隔，从而减少窗口抖动的问题"""
        if self.dragPos is not None and self.lastTime is not None:
            currentTime = QDateTime.currentDateTime()
            elapsedTime = self.lastTime.msecsTo(currentTime)
            if elapsedTime >= 10:  # 限制窗口移动的最小时间间隔
                delta = event.pos() - self.dragPos
                self.move(self.pos() + delta)
                self.lastTime = currentTime
                event.accept()
                self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mouseReleaseEvent(self, event):
        self.dragPos = None
        self.lastTime = None
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_btn_enabled(self, button_obj, state: bool):
        button_obj.setEnabled(state)

    def btn_color(self, btn, color):
        """
        设置按钮的颜色样式
        Args:
            btn: 按钮名称
            color: 颜色名称

        Returns: None

        """
        try:
            if color == 'red':
                btn.setStyleSheet("background-color: rgb(231, 76, 60);\n"
                                  "color: rgb(255, 255, 255);\n"
                                  "border-radius: 10px;\n"
                                  "border: 2px groove gray;\n"
                                  "border-style: outset;")
            elif color == 'green':
                btn.setStyleSheet("background-color: rgb(39, 174, 96);\n"
                                  "color: rgb(255, 255, 255);\n"
                                  "border-radius: 10px;\n"
                                  "border: 2px groove gray;\n"
                                  "border-style: outset;")
            elif color == 'blue':
                btn.setStyleSheet("background-color: rgb(41, 128, 185);\n"
                                  "color: rgb(255, 255, 255);\n"
                                  "border-radius: 10px;\n"
                                  "border: 2px groove gray;\n"
                                  "border-style: outset;")
            elif color == 'gray':
                btn.setStyleSheet("background-color: rgb(185, 195, 199);\n"
                                  "color: rgb(255, 255, 255);\n"
                                  "border-radius: 10px;\n"
                                  "border: 2px groove gray;\n"
                                  "border-style: outset;")
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def set_language(self):
        """
        设置语言
        """
        try:
            self.is_language_btn_click = True
            if self.language == 1:
                self.language = 2
                self.btn_color(self.language_btn, 'blue')
            else:
                self.language = 1
                self.btn_color(self.language_btn, 'green')
            self._init_language()
            self.choose_function()
            self.is_language_btn_click = False
            self.init_offset_tooltip()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def _init_language(self):
        """
        初始化语言
        """
        if self.language == 1:
            if not self.is_language_btn_click:
                return
            self.camara_show.setText("Camera")
            if self.open_camera_btn.text() == '打开':
                self.open_camera_btn.setText("Open")
            else:
                self.open_camera_btn.setText("Close")
            self.connect_lab.setText("Connection")
            if self.connect_btn.text() == '连接':
                self.connect_btn.setText("CONNECT")
            else:
                self.connect_btn.setText("DISCONNECT")
            self.device_lab.setText("Device")
            self.port_lab.setText("Port")
            self.ip_lab.setText("IP Address")
            self.control_lab.setText("Control")
            self.to_origin_btn.setText("Go")
            self.home_lab.setText("Homing")
            self.recognition_lab.setText("Recognition")
            self.discern_btn.setText("Run")
            self.offsets_lab.setText("XYZ Offset")
            self.current_algorithm_lab.setText("Current Algorithm:")
            self.crawl_btn.setText("Run")
            self.pick_lab.setText("Pick")
            self.place_lab.setText("Place")
            self.place_btn.setText('Run')
            self.offset_save_btn.setText('Save')
            self.algorithm_lab2.setText("Algorithm")
            self.select_lab.setText("Select")
            self.comboBox_function.setItemText(0, "Color recognition pump")
            self.comboBox_function.setItemText(1, "Shape recognition pump")
            self.comboBox_function.setItemText(2, "yolov8 pump")
            self.comboBox_function.setItemText(3, "Depalletizing pump")
            self.comboBox_function.setItemText(4, "Color recognition gripper")
            self.comboBox_function.setItemText(5, "yolov8 gripper")

            self.display_lab.setText("Display")
            self.current_coord_btn.setText("current coordinates")
            self.image_coord_btn.setText("image coordinates")
            self.language_btn.setText("简体中文")
            self.show_camera_lab_depth.setText("Camera Depth Screen")
            self.show_camera_lab_rgb.setText("Camera Color Screen")

        else:
            self.camara_show.setText("相机")
            if self.is_language_btn_click:
                if self.open_camera_btn.text() == 'Open':
                    self.open_camera_btn.setText("打开")
                else:
                    self.open_camera_btn.setText("关闭")
            else:
                self.open_camera_btn.setText("打开")
            self.connect_lab.setText("连接")
            if self.is_language_btn_click:
                if self.connect_btn.text() == 'CONNECT':
                    self.connect_btn.setText("连接")
                else:
                    self.connect_btn.setText("断开")
            else:
                self.connect_btn.setText("连接")
            self.device_lab.setText("设备")
            self.port_lab.setText("端口号")
            self.ip_lab.setText("IP地址")
            self.control_lab.setText("控制")
            self.to_origin_btn.setText("运行")
            self.home_lab.setText("初始点")
            self.recognition_lab.setText("识别")
            self.discern_btn.setText("运行")
            self.offsets_lab.setText("XYZ 偏移量")
            self.current_algorithm_lab.setText("当前算法:")
            self.crawl_btn.setText("运行")
            self.pick_lab.setText("抓取")
            self.place_lab.setText("放置")
            self.place_btn.setText("运行")
            self.offset_save_btn.setText("保存")
            self.algorithm_lab2.setText("算法")
            self.select_lab.setText("选择")
            self.comboBox_function.setItemText(0, "颜色识别 吸泵")
            self.comboBox_function.setItemText(1, "形状识别 吸泵")
            self.comboBox_function.setItemText(2, "yolov8 吸泵")
            self.comboBox_function.setItemText(3, "拆码垛 吸泵")
            self.comboBox_function.setItemText(4, "颜色识别 夹爪")
            self.comboBox_function.setItemText(5, "yolov8 夹爪")

            self.display_lab.setText("坐标显示")
            self.current_coord_btn.setText("实时坐标")
            self.image_coord_btn.setText("图像坐标")
            self.language_btn.setText("English")
            self.show_camera_lab_depth.setText("相机深度画面")
            self.show_camera_lab_rgb.setText("相机彩色画面")

    def init_btn_status(self, status):
        """
        初始化各个按钮的状态
        Args:
            status: bool类型(True/False)

        Returns: None

        """
        try:
            btn_list = [self.to_origin_btn, self.crawl_btn, self.place_btn, self.current_coord_btn,
                        self.image_coord_btn, self.discern_btn, self.open_camera_btn]
            btn_list2 = [self.to_origin_btn]
            green_btn = [self.open_camera_btn, self.current_coord_btn, self.image_coord_btn]
            if status:
                for b in btn_list2:
                    b.setEnabled(True)
                    self.btn_color(b, 'blue')

                # for c in green_btn:
                #     c.setEnabled(True)
                #     self.btn_color(c, 'green')
            else:
                for b in btn_list:
                    b.setEnabled(False)
                    self.btn_color(b, 'gray')
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def choose_function(self):
        """
        根据算法下拉框选择显示当前算法名称,使用正则表达式限制偏移量的输入类型及其范围
        Returns: None

        """
        try:
            self.algorithm_mode = self.comboBox_function.currentText()
            self.algorithm_lab.setText(self.algorithm_mode)
            self.xoffset_edit.setEnabled(True)
            self.yoffset_edit.setEnabled(True)
            self.zoffset_edit.setEnabled(True)
            self.is_pick = True
            # 偏移量设置正则表达式校验器，只允许输入-255 到 255数字
            regex = QRegularExpression(r'^-?(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$')
            validator = QRegularExpressionValidator(regex)
            edit_widgets = [self.xoffset_edit, self.yoffset_edit, self.zoffset_edit]

            for edit_widget in edit_widgets:
                edit_widget.setValidator(validator)
            self.offset_change()
            if self.algorithm_mode in ['Depalletizing pump', '拆码垛 吸泵']:
                self.place_btn.setEnabled(False)
                self.btn_color(self.place_btn, 'gray')
            else:
                if self.is_connected:
                    self.place_btn.setEnabled(False)
                    self.btn_color(self.place_btn, 'gray')
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def check_ip_port(self):
        """
        检查IP地址是否合格
        """
        pass

    def get_serial_port_list(self):
        """
        获取当前串口号并映射到串口下拉框
        Returns: 串口号

        """
        plist = [
            str(x).split(" - ")[0].strip() for x in serial.tools.list_ports.comports()
        ]
        print(plist)
        try:
            if not plist:
                # if self.comboBox_port.currentText() == 'no port':
                #     return
                self.comboBox_port.clear()
                self.comboBox_port.addItem('no port')
                self.connect_btn.setEnabled(False)
                self.btn_color(self.connect_btn, 'gray')
                self.port_list = []
                return
            else:
                if self.port_list != plist:
                    self.port_list = plist
                    self.comboBox_port.clear()
                    self.connect_btn.setEnabled(True)
                    self.btn_color(self.connect_btn, 'green')
                    for p in plist:
                        self.comboBox_port.addItem(p)
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def add_support_robot_types(self):
        """
        增加后续可支持的机型
        """
        self.comboBox_device.clear()
        self.comboBox_device.addItem("myCobot 280 for PI")

    def baud_choose(self):
        """
        根据机器设备选择正确的串口号
        Returns: None

        """
        device = self.comboBox_device.currentText()
        if device in self.M5:
            self.comboBox_baud.setCurrentIndex(0)
        else:
            self.comboBox_baud.setCurrentIndex(1)

    def connect_checked(self):
        """
        连接按钮的状态切换
        Returns:

        """
        try:
            if self.language == 1:
                txt = 'CONNECT'
            else:
                txt = '连接'
            if self.connect_btn.text() == txt:
                self.robotics_connect()
            else:
                self.disconnect_robotics()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def is_valid_ip(self, ip):
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            if not part.isdigit() or not 0 <= int(part) <= 255:
                return False
        return True

    def is_valid_port(self, port):
        try:
            port = int(port)
            return 1024 <= port <= 65535 and port != 9999
        except ValueError:
            return False

    def robotics_connect(self):
        """
        启动机械臂连接的子线程
        Returns: None

        """
        try:
            ip = self.ip_lineEdit.text()
            port_text = self.port_lineEdit.text()
            algorithm_mode = self.comboBox_function.currentText()

            # 这里校验ip、端口合法性（同步UI线程安全操作）
            if not self.is_valid_ip(ip):
                if self.language == 1:
                    QMessageBox.warning(self, "Error", "Please enter a valid IP")
                else:
                    QMessageBox.warning(self, "错误", "请输入合法IP")
                return

            if not port_text.isdigit() or not self.is_valid_port(port_text):
                if self.language == 1:
                    QMessageBox.warning(self, "error",
                                        "Please enter a valid port number. The default is 9000, the range is 1024~65535, and cannot be 9999")
                else:
                    QMessageBox.warning(self, "错误", "请输入合法端口，默认是9000，范围1024~65535，且不能为9999")
                return
            port = int(port_text)

            self.comboBox_device.setEnabled(False)
            self.ip_lineEdit.setEnabled(False)
            self.port_lineEdit.setEnabled(False)
            self.prompts_lab.clear()
            device = self.comboBox_device.currentText()
            if device == 'myCobot 280 for PI':
                init_robotics = threading.Thread(target=self.init_280_PI, args=(ip, port, algorithm_mode))
                init_robotics.start()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def init_280_PI(self, ip, port, algorithm_mode):
        """
        连接机械臂，并对机械臂进行一些初始化
        Returns:

        """
        try:
            # self.comboBox_device.setEnabled(False)
            # self.ip_lineEdit.setEnabled(False)
            # self.port_lineEdit.setEnabled(False)
            # ip = self.ip_lineEdit.text()
            # port = int(self.port_lineEdit.text())
            self.algorithm_mode = algorithm_mode
            # self.algorithm_mode = self.comboBox_function.currentText()
            self.mc = MyCobot280Socket(ip, port)
            time.sleep(1)
            self.logger.info('connection succeeded !')
            self.mc.set_gpio_mode('BCM')
            self.mc.set_gpio_out(20, 'out')
            self.mc.set_gpio_out(21, 'out')
            self.is_connected = True
            self.init_btn_status(True)
            self.current_coord_btn.setEnabled(True)
            self.btn_color(self.current_coord_btn, 'green')
            if self.language == 1:
                self.connect_btn.setText('Disconnect')
            else:
                self.connect_btn.setText('断开')
            self.btn_color(self.connect_btn, 'red')

        except Exception as e:
            e = traceback.format_exc()
            error_mes = 'Connection failed !!!:{}'.format(e)
            self.mc = None
            self.is_connected = False
            self.ip_lineEdit.setEnabled(True)
            self.port_lineEdit.setEnabled(False)
            self.comboBox_device.setEnabled(True)
            self.init_btn_status(False)
            if self.language == 1:
                self.connect_btn.setText('CONNECT')
            else:
                self.connect_btn.setText('连接')
            self.btn_color(self.connect_btn, 'green')
            self.logger.error(error_mes)

    def has_mycobot(self):
        """
        检查机械臂是否连接
        Returns:

        """
        if not self.mc:
            self.logger.info("Mycobot is not connected yet! ! ! Please connect to myCobot first! ! !")
            return False
        return True

    def disconnect_robotics(self):
        """
        机械臂断开连接
        Returns: None

        """
        if not self.has_mycobot():
            return

        try:
            time.sleep(0.1)
            del self.mc
            self.mc = None
            self.logger.info("Disconnected successfully !")
            self.is_connected = False
            self.port_lineEdit.setEnabled(True)
            self.ip_lineEdit.setEnabled(True)
            self.comboBox_device.setEnabled(True)
            self.comboBox_function.setEnabled(True)
            if self.language == 1:
                self.connect_btn.setText('CONNECT')
            else:
                self.connect_btn.setText('连接')
            self.btn_color(self.connect_btn, 'green')
            self.init_btn_status(False)
            self.is_discern = False
            self.is_current_coords = False
            self.is_place = False
            self.is_crawl = False
            self.is_img_coords = False
            self.current_coord_lab.clear()
            self.img_coord_lab.clear()
            self.prompts_lab.clear()
            self.show_camera_lab_depth.hide()
            self.show_camera_lab_rgb.hide()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.info("Not yet connected to mycobot！！！{}".format(str(e)))

    # 开启吸泵
    def pump_on(self):
        # 打开电磁阀
        self.mc.set_gpio_output(20, 0)
        time.sleep(0.05)

    # 停止吸泵
    def pump_off(self):
        # 关闭电磁阀
        self.mc.set_gpio_output(20, 1)
        time.sleep(0.05)
        # 泄气阀门开始工作
        self.mc.set_gpio_output(21, 0)
        time.sleep(1)
        self.mc.set_gpio_output(21, 1)
        time.sleep(0.05)

    def robot_go_home(self):
        """
        控制机械臂回到初始点 [-90, 0, 0, 0, 90, 0]
        Returns: None

        """
        try:
            if self.mc.get_fresh_mode() != 0:
                self.mc.set_fresh_mode(0)
                time.sleep(0.5)
            device = self.comboBox_device.currentText()
            go_home_mes = 'The robot moves to the initial point'
            if device in self.PI:
                self.logger.info(go_home_mes)
                self.mc.send_angles(arm_idle_angle, 50)
                time.sleep(3)
            if self.algorithm_mode in self.algorithm_pump:  # for pump
                self.mc.set_tool_reference(tool_frame_pump)
                time.sleep(0.5)
                self.mc.set_end_type(1)
                time.sleep(0.05)
                self.pump_off()
                time.sleep(1.5)
            else:
                self.mc.set_tool_reference(tool_frame_gripper)  # for gripper
                time.sleep(0.05)
                self.mc.set_end_type(1)
                time.sleep(1)
                open_gripper(self.mc)
                time.sleep(2)
                print('open gripper')
                release_gripper(self.mc)
                time.sleep(0.1)
            self.is_go_home = False
            self.btn_color(self.to_origin_btn, 'blue')
            if not self.is_discern:
                self.discern_btn.setEnabled(True)
                self.btn_color(self.discern_btn, 'blue')
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def go_home_function(self):
        """
        回到初始点和初始化参数 按钮开关
        Returns: None

        """
        try:
            if self.is_go_home:
                self.is_go_home = False
                self.btn_color(self.to_origin_btn, 'blue')
            else:
                self.is_go_home = True
                self.btn_color(self.to_origin_btn, 'red')
                go_home = threading.Thread(target=self.robot_go_home)
                go_home.start()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def init_offset_tooltip(self):
        """
        鼠标悬浮在 XYZ Offsets 控件上的提示功能作用
        Returns: None

        """
        try:
            if self.language == 1:
                self.offsets_lab.setToolTip(
                    'Adjust the suction position of the end, add X forward,'
                    ' subtract X backward, \nadd Y to the left, and subtract Y to the right, decrease Z downward, and increase Z upward')
            else:
                self.offsets_lab.setToolTip(
                    '调整末端吸取位置，向前X加，向后X减，向左Y加，向右Y减，向下Z减，向上Z加。')
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def offset_change(self):
        """
        根据算法功能的不同，从文件中读取偏移量信息并将其显示在对应的文本框中
        Returns: None

        """
        try:
            self.algorithm_mode = self.comboBox_function.currentText()
            # 定义文件路径与功能的映射关系
            file_paths = {
                '颜色识别 吸泵': 'color_pump_offset.txt',
                'Color recognition pump': 'color_pump_offset.txt',
                '形状识别 吸泵': 'shape_pump_offset.txt',
                'Shape recognition pump': 'shape_pump_offset.txt',
                'yolov8 吸泵': 'yolo_pump_offset.txt',
                'yolov8 pump': 'yolo_pump_offset.txt',
                '拆码垛 吸泵': 'pallet_pump_offset.txt',
                'Depalletizing pump': 'pallet_pump_offset.txt',
                '颜色识别 夹爪': 'color_gripper_offset.txt',
                'Color recognition gripper': 'color_gripper_offset.txt',
                'yolov8 夹爪': 'yolo_gripper_offset.txt',
                'yolov8 gripper': 'yolo_gripper_offset.txt',
            }
            file_path = file_paths.get(self.algorithm_mode)
            if file_path:
                with open(libraries_path + '/offset/' + file_path, 'r', encoding='utf-8') as f:
                    offset = f.read().splitlines()
                    offset_values = eval(offset[0])
                    self.offset_x, self.offset_y, self.offset_z = map(int, offset_values)
                    self.xoffset_edit.clear()
                    self.yoffset_edit.clear()
                    self.zoffset_edit.clear()
                    self.xoffset_edit.setText(f'{offset_values[0]}')
                    self.yoffset_edit.setText(f'{offset_values[1]}')
                    self.zoffset_edit.setText(f'{offset_values[2]}')
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def insert_offset(self):
        """
        读取XYZ偏移量的值，并保存到对应文件中
        Returns: None

        """
        try:
            self.algorithm_mode = self.comboBox_function.currentText()
            x = self.xoffset_edit.text()
            y = self.yoffset_edit.text()
            z = self.zoffset_edit.text()
            offset = [x, y, z]
            file_paths = {
                '颜色识别 吸泵': 'color_pump_offset.txt',
                'Color recognition pump': 'color_pump_offset.txt',
                '形状识别 吸泵': 'shape_pump_offset.txt',
                'Shape recognition pump': 'shape_pump_offset.txt',
                'yolov8 吸泵': 'yolo_pump_offset.txt',
                'yolov8 pump': 'yolo_pump_offset.txt',
                '拆码垛 吸泵': 'pallet_pump_offset.txt',
                'Depalletizing pump': 'pallet_pump_offset.txt',
                '颜色识别 夹爪': 'color_gripper_offset.txt',
                'Color recognition gripper': 'color_gripper_offset.txt',
                'yolov8 夹爪': 'yolo_gripper_offset.txt',
                'yolov8 gripper': 'yolo_gripper_offset.txt',
            }
            file_path = file_paths.get(self.algorithm_mode)
            if file_path:
                with open(libraries_path + '/offset/' + file_path, 'w', encoding='utf-8') as f:
                    f.write(str(offset))
                self.offset_x, self.offset_y, self.offset_z = int(x), int(y), int(z)
                if self.language == 1:
                    msg_box = QMessageBox(QMessageBox.Icon.Information, 'prompt', 'Successfully saved！')
                else:
                    msg_box = QMessageBox(QMessageBox.Icon.Information, '提示', '保存成功！')
                msg_box.exec()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def discern_function(self):
        """
        识别按钮的开关, 如果打开识别按钮则可以打开摄像头按钮，以及点击查看图像按钮，如果关闭识别按钮，则摄像头打开按钮复位变绿色
        Returns: None

        """
        try:
            if self.is_discern:
                self.is_discern = False
                self.btn_color(self.discern_btn, 'blue')
                self.stop_thread()  # a flag
                self.open_camera.release()  # release camera
                self.detect_thread.join()  # wait for the thread stop totally
                self.open_camera = None
                self.is_thread_running = True
                self.is_open_camera = False
                self.show_camera_lab_depth.clear()
                self.show_camera_lab_rgb.clear()
                self.show_camera_lab_rgb.hide()
                self.show_camera_lab_depth.hide()
                self.pump_off()

                if self.language == 1:
                    self.open_camera_btn.setText('Open')
                else:
                    self.open_camera_btn.setText('打开')

                self.prompts_lab.clear()

                self.open_camera_btn.setEnabled(False)
                self.image_coord_btn.setEnabled(False)
                self.crawl_btn.setEnabled(False)
                self.btn_color(self.crawl_btn, 'gray')
                self.place_btn.setEnabled(False)
                self.btn_color(self.place_btn, 'gray')
                self.btn_color(self.open_camera_btn, 'gray')
                self.btn_color(self.image_coord_btn, 'gray')
                self.img_coord_lab.clear()
                self.is_img_coords = False
                self.comboBox_function.setEnabled(True)
            else:
                self.prompts_lab.clear()
                self.is_discern = True
                self.btn_color(self.discern_btn, 'red')
                self.open_camera_btn.setEnabled(True)
                self.image_coord_btn.setEnabled(True)
                self.crawl_btn.setEnabled(True)
                self.btn_color(self.crawl_btn, 'blue')
                self.btn_color(self.open_camera_btn, 'green')
                self.btn_color(self.image_coord_btn, 'green')
                self.show_camera_lab_depth.hide()
                self.show_camera_lab_rgb.hide()
                self.comboBox_function.setEnabled(False)
                algorithm_mode = self.comboBox_function.currentText()
                run_detect = threading.Thread(target=self.start_detect,
                                              args=(algorithm_mode, ))
                run_detect.start()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error('identify anomalies' + str(e))

    def crawl_function(self):
        """
        抓取物体-运行按钮的开关
        Returns: None

        """
        try:
            self.algorithm_mode = self.comboBox_function.currentText()
            if self.is_crawl:
                self.is_crawl = False
                self.btn_color(self.crawl_btn, 'blue')
                if self.algorithm_mode in ['Depalletizing pump', '拆码垛 吸泵']:
                    self.pallet.join()
            else:
                self.is_crawl = True
                self.btn_color(self.crawl_btn, 'red')
                if self.algorithm_mode in ['Depalletizing pump', '拆码垛 吸泵']:
                    algorithm_mode = self.comboBox_function.currentText()
                    self.pallet = threading.Thread(target=self.start_pallet_crawl, args=(algorithm_mode,))
                    self.pallet.start()
                else:
                    self.place_btn.setEnabled(True)
                    self.btn_color(self.place_btn, 'blue')

                    algorithm_mode = self.comboBox_function.currentText()
                    crawl_move = threading.Thread(target=self.robot_pick_move, args=(algorithm_mode,))
                    crawl_move.start()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def place_function(self):
        """
        放置按钮的开关
        Returns: None

        """
        try:
            if self.is_place:
                self.is_place = False
                self.btn_color(self.place_btn, 'blue')
            else:
                self.is_place = True
                # self.btn_color(self.place_btn, 'red')
                self.set_button_color.emit(self.place_btn, 'red')
                algorithm_mode = self.comboBox_function.currentText()
                place_move = threading.Thread(target=self.robot_place_move, args=(algorithm_mode,))
                place_move.start()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def get_current_coords(self):
        """
        获取当前机械臂的坐标，并更新坐标的显示
        Returns: None

        """
        while self.is_current_coords:
            QApplication.processEvents()
            try:
                coord = self.mc.get_coords()
            except Exception as e:
                e = traceback.format_exc()
                coord = []
                self.logger.error(str(e))
                pass
            if coord and len(coord) == 6:
                coord = 'X: {} Y: {} Z: {} Rx: {} Ry: {} Rz: {}'.format(coord[0], coord[1], coord[2], coord[3],
                                                                        coord[4],
                                                                        coord[5])
                if self.is_current_coords:
                    self.current_coord_lab.clear()
                    self.current_coord_lab.setText(str(coord))
            time.sleep(0.2)

    def get_current_coords_btn(self):
        """
        通过点击按钮，显示当前机械臂的坐标开关
        Returns: None

        """
        try:
            if not self.has_mycobot():
                return
            if self.is_current_coords:
                self.is_current_coords = False
                self.btn_color(self.current_coord_btn, 'green')
                self.current_coord_lab.clear()
            else:
                self.is_current_coords = True
                self.btn_color(self.current_coord_btn, 'red')
                get_coord = threading.Thread(target=self.get_current_coords)
                get_coord.start()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def get_img_coords_btn(self):
        """
        获取图像的定位坐标
        Returns: None

        """
        try:
            if self.is_img_coords:
                self.is_img_coords = False
                self.btn_color(self.image_coord_btn, 'green')
                self.img_coord_lab.clear()
            else:
                self.is_img_coords = True
                if self.is_discern:
                    self.btn_color(self.image_coord_btn, 'red')
                    get_img = threading.Thread(target=self.get_img_coords)
                    get_img.start()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def get_img_coords(self):
        while self.is_img_coords:
            QApplication.processEvents()
            try:
                if self.is_discern:
                    if self.is_img_coords:
                        self.img_coord_lab.clear()
                        self.img_coord_lab.setText(str('X: {} Y: {} Z: {}'.format(self.pos_x, self.pos_y, self.pos_z)))
                        time.sleep(0.1)
                else:
                    if self.language == 2:
                        self.img_coord_lab.setText('请先启动识别程序！')
                    else:
                        self.img_coord_lab.setText('Please start the recognition process first!')
            except Exception as e:
                e = traceback.format_exc()
                self.logger.error(str(e))

    def display_open_camera_1(self, detector):
        """
        开启摄像头并将画面显示在界面上（适用于颜色识别、形状识别）
        Args:
            detector: 一个识别算法检测类

        Returns: None

        """
        print('Start Color or Shape......')
        self.algorithm_mode = self.comboBox_function.currentText()
        if not self.is_open_camera:
            self.open_camera = ObbrecCamera()
            self.open_camera.capture()
            self.is_open_camera = True
            while self.is_thread_running:
                self.open_camera.update_frame()
                color_frame = self.open_camera.color_frame()
                depth_frame = self.open_camera.depth_frame()

                if color_frame is None or depth_frame is None:
                    # time.sleep(0.1)
                    continue
                color_frame = crop_frame(color_frame, crop_size, crop_offset)
                depth_frame = crop_frame(depth_frame, crop_size, crop_offset)
                depth_visu_frame = depth_frame.copy()
                color_frame = cv2.resize(color_frame, None, fx=zoom_factor, fy=zoom_factor)
                depth_frame = cv2.resize(depth_frame, None, fx=zoom_factor, fy=zoom_factor)
                if color_frame is not None:
                    depth_visu_frame = depth_visu_frame / np.max(depth_frame) * 255
                    depth_visu_frame = depth_visu_frame.astype(np.uint8)
                    depth_visu_frame = cv2.cvtColor(depth_visu_frame, cv2.COLOR_GRAY2BGR)
                    # Convert BGR to RGB
                    color_frame_qt = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
                    color_frame_qimage = QImage(
                        color_frame_qt.data,
                        color_frame_qt.shape[1],
                        color_frame_qt.shape[0],
                        color_frame_qt.strides[0],
                        QImage.Format.Format_RGB888,
                    )
                    depth_frame_qimage = QImage(
                        depth_visu_frame.data,
                        depth_visu_frame.shape[1],
                        depth_visu_frame.shape[0],
                        depth_visu_frame.strides[0],
                        QImage.Format.Format_RGB888,
                    )
                    # Create QPixmap from QImage
                    color_pixmap = QPixmap.fromImage(color_frame_qimage)
                    depth_pixmap = QPixmap.fromImage(depth_frame_qimage)

                    # Set the QPixmap to QLabel
                    # self.show_camera_lab_rgb.setPixmap(color_pixmap)
                    # self.show_camera_lab_depth.setPixmap(depth_pixmap.scaled(390, 390))
                    self.update_rgb_signal.emit(color_pixmap)
                    self.update_depth_signal.emit(depth_pixmap)

                if color_frame is None:
                    continue
                res = detector.detect(color_frame)
                if res:
                    if self.is_pick:
                        # 获取检测到的颜色名称
                        detector.draw_result(color_frame, res)
                        # Convert BGR to RGB
                        color_frame_qt = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
                        color_frame_qimage = QImage(
                            color_frame_qt.data,
                            color_frame_qt.shape[1],
                            color_frame_qt.shape[0],
                            color_frame_qt.strides[0],
                            QImage.Format.Format_RGB888,
                        )
                        color_pixmap = QPixmap.fromImage(color_frame_qimage)
                        # self.show_camera_lab_rgb.setPixmap(color_pixmap)
                        self.update_rgb_signal.emit(color_pixmap)
                        # interpret result
                        obj_configs = []
                        for obj in res:
                            rect = detector.get_rect(obj)
                            x, y = detector.target_position(obj)
                            obj_configs.append((rect, (x, y)))
                        # pack (depth, pos, angle) together
                        depth_pos_pack = []
                        for obj in obj_configs:
                            rect, (x, y) = obj
                            rect = np.array(rect)
                            target_depth_frame = crop_poly(depth_frame, rect)
                            mean_depth = np.sum(target_depth_frame) / np.count_nonzero(
                                target_depth_frame
                            )
                            depth_pos_pack.append((mean_depth, (x, y)))

                        # find lowest depth (highest in pile)
                        depth, (x, y) = min(depth_pos_pack)
                        if np.isnan(depth):
                            self.logger.error('相机无法正确获取深度信息:{}'.format(depth))
                            continue
                        else:
                            x, y = int(x), int(y)
                            z = int(floor_depth - depth)
                            # transform angle from camera frame to arm frame
                            self.pos_x, self.pos_y, self.pos_z = x, y, z
                            # print(f"Raw pos_x,pos_y,pos_z : {self.pos_x} {self.pos_y} {self.pos_z}") #todo open for detect1
            self.logger.info('Recognition has stopped....')

        else:
            if self.is_open_camera:
                try:
                    self.stop_thread()
                    self.open_camera.release()
                    self.is_open_camera = False
                    self.logger.info('close')
                except Exception as e:
                    e = traceback.format_exc()
                    self.logger.error(str(e))

    def display_open_camera_2(self, detector):
        """
        开启摄像头并将画面显示在界面上（适用于yolov8、拆码垛程序）
        Args:
            detector: 一个识别算法检测类

        Returns: None

        """
        self.algorithm_mode = self.comboBox_function.currentText()
        if not self.is_open_camera:
            self.open_camera = ObbrecCamera()
            self.open_camera.capture()
            self.is_open_camera = True
            while self.is_thread_running:
                self.open_camera.update_frame()
                color_frame = self.open_camera.color_frame()
                depth_frame = self.open_camera.depth_frame()
                if color_frame is None or depth_frame is None:
                    # time.sleep(0.1)
                    continue
                color_frame = crop_frame(color_frame, crop_size, crop_offset)
                depth_frame = crop_frame(depth_frame, crop_size, crop_offset)
                depth_visu_frame = depth_frame.copy()
                color_frame = cv2.resize(color_frame, None, fx=zoom_factor, fy=zoom_factor)
                depth_frame = cv2.resize(depth_frame, None, fx=zoom_factor, fy=zoom_factor)
                if color_frame is not None:
                    depth_visu_frame = depth_visu_frame / np.max(depth_frame) * 255
                    depth_visu_frame = depth_visu_frame.astype(np.uint8)
                    depth_visu_frame = cv2.cvtColor(depth_visu_frame, cv2.COLOR_GRAY2BGR)
                    # Convert BGR to RGB
                    color_frame_qt = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
                    color_frame_qimage = QImage(
                        color_frame_qt.data,
                        color_frame_qt.shape[1],
                        color_frame_qt.shape[0],
                        color_frame_qt.strides[0],
                        QImage.Format.Format_RGB888,
                    )
                    depth_frame_qimage = QImage(
                        depth_visu_frame.data,
                        depth_visu_frame.shape[1],
                        depth_visu_frame.shape[0],
                        depth_visu_frame.strides[0],
                        QImage.Format.Format_RGB888,
                    )
                    # Create QPixmap from QImage
                    color_pixmap = QPixmap.fromImage(color_frame_qimage)
                    depth_pixmap = QPixmap.fromImage(depth_frame_qimage)

                    # Set the QPixmap to QLabel
                    # self.show_camera_lab_rgb.setPixmap(color_pixmap)
                    # self.show_camera_lab_depth.setPixmap(depth_pixmap.scaled(390, 390))
                    self.update_rgb_signal.emit(color_pixmap)
                    self.update_depth_signal.emit(depth_pixmap)
                if color_frame is None:
                    continue
                res = detector.detect(color_frame)
                if res:
                    if self.is_pick:
                        # 获取检测到的类名称
                        for r in res:
                            color_frame = r.plot()
                            # Convert BGR to RGB
                            color_frame_qt = cv2.cvtColor(color_frame, cv2.COLOR_BGR2RGB)
                            color_frame_qimage = QImage(
                                color_frame_qt.data,
                                color_frame_qt.shape[1],
                                color_frame_qt.shape[0],
                                color_frame_qt.strides[0],
                                QImage.Format.Format_RGB888,
                            )
                            color_pixmap = QPixmap.fromImage(color_frame_qimage)
                            # self.show_camera_lab_rgb.setPixmap(color_pixmap)
                            self.update_rgb_signal.emit(color_pixmap)
                        # interpret result
                        obj_configs = []
                        # Multi-target coordinate results
                        coords_res = []
                        for obj in res:
                            rect = detector.get_rect(
                                obj)
                            for coords in detector.target_position(obj):
                                x, y = coords
                                coords_res.append((x, y))
                            coords_res = tuple(coords_res)
                            obj_configs.append((rect, coords_res))
                        # pack (depth, pos, angle) together
                        depth_pos_pack = []
                        # Multiple Target Depth Results
                        depth_res = []
                        for obj in obj_configs:
                            rect = obj[0]
                            coords = obj[1]
                            rect = np.array(rect)
                            for rects in rect:
                                target_depth_frame = crop_poly(depth_frame, rects)
                                mean_depth = np.sum(target_depth_frame) / np.count_nonzero(
                                    target_depth_frame
                                )
                                depth_res.append(mean_depth)
                            depth_list = tuple(depth_res)
                            depth_pos_pack.append((depth_list, coords))
                        # find lowest depth (highest in pile)
                        data = min(depth_pos_pack)
                        # 提取深度值和坐标点
                        depth_values = data[0]
                        coordinate_tuples = data[1]

                        # 创建一个字典来将深度值映射到坐标点
                        depth_coordinate_map = {}
                        # 将深度值和坐标点进行匹配
                        for i, depth in enumerate(depth_values):
                            if i < len(coordinate_tuples):
                                coordinates = coordinate_tuples[i]
                                depth_coordinate_map[depth] = coordinates
                        # 现在您可以通过深度值来查找相应的坐标点
                        depth_to_match = min(depth_values)
                        # self.logger.info(str(depth_values))
                        matched_coordinates = depth_coordinate_map.get(depth_to_match)
                        if np.isnan(depth_to_match):
                            self.logger.error('相机无法正确获取深度信息:{}'.format(depth_to_match))
                            continue
                            # depth_to_match = 320
                        else:
                            x, y, z = 0, 0, 0

                            if matched_coordinates:
                                x, y = matched_coordinates
                                x, y = int(x), int(y)
                                z = int(floor_depth - depth_to_match)
                                print(f"深度值 {depth_to_match} 对应的坐标点是 {matched_coordinates}")

                                # self.logger.info(f"深度值 {depth_to_match} 对应的坐标点是 {matched_coordinates}")

                            else:
                                print(f"未找到深度值 {depth_to_match} 对应的坐标点")
                            self.pos_x, self.pos_y, self.pos_z = x, y, z
                            print(f"Raw pos_x,pos_y,pos_z : {self.pos_x} {self.pos_y} {self.pos_z}")
            self.logger.info('already stop....')

        else:
            if self.is_open_camera:
                try:
                    self.stop_thread()
                    self.open_camera.release()
                    self.is_open_camera = False
                    self.logger.info('close')
                except Exception as e:
                    e = traceback.format_exc()
                    self.logger.error(str(e))

    def stop_thread(self):
        """
        停止摄像头线程
        Returns:

        """
        self.is_thread_running = False

    def display_open_camera_thread(self, detector, mode):
        """
        根据算法功能的下拉框，选择对应的算法程序
        Args:
            detector: 一个识别算法类
            mode: 识别算法名称

        Returns: None

        """
        try:
            # self.choose_function()
            self.choose_function_signal.emit()
            time.sleep(0.05)
            self.algorithm_mode = mode
            if self.algorithm_mode in ['颜色识别 吸泵', 'Color recognition pump', '形状识别 吸泵',
                                       'Shape recognition pump',
                                       '颜色识别 夹爪',
                                       'Color recognition gripper']:
                self.display_open_camera_1(detector)
            else:
                self.display_open_camera_2(detector)
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def start_detect(self, algorithm_mode):
        """
        选择识别算法进行识别
        Returns: None

        """
        try:
            if self.is_discern:
                # self.choose_function()
                self.algorithm_mode = algorithm_mode
                detector = None

                if self.algorithm_mode in ['颜色识别 吸泵', 'Color recognition pump']:
                    detector = ColorDetector()
                elif self.algorithm_mode in ['形状识别 吸泵', 'Shape recognition pump']:
                    detector = ShapeDetector()
                elif self.algorithm_mode in ['yolov8 pump', 'yolov8 吸泵', 'Depalletizing pump', '拆码垛 吸泵',
                                             'yolov8 gripper',
                                             'yolov8 夹爪']:
                    detector = YOLODetector()
                elif self.algorithm_mode in ['颜色识别 夹爪', 'Color recognition gripper']:
                    detector = ColorDetector()
                    detector.area_low_threshold = 5000
                if detector:
                    self.detect_thread = threading.Thread(target=self.display_open_camera_thread,
                                                          args=(detector, algorithm_mode))
                    self.detect_thread.daemon = True
                    self.detect_thread.start()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def camera_checked(self):
        """Bind camera switch"""
        try:
            if self.language == 1:
                txt = 'Open'
            else:
                txt = '打开'
            if self.open_camera_btn.text() == txt:
                self.show_camera()
            else:
                self.close_camera()
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def show_camera(self):
        """
        显示摄像头画面
        Returns: None

        """
        try:
            if self.is_discern:
                self.show_camera_lab_rgb.show()
                self.show_camera_lab_depth.show()
                if self.language == 1:
                    self.open_camera_btn.setText('Close')
                else:
                    self.open_camera_btn.setText('关闭')
                self.btn_color(self.open_camera_btn, 'red')
                self.prompts_lab.clear()
            else:
                if self.language == 1:
                    self.prompts_lab.setText(
                        'The camera failed to open, please check whether the camera connection is correct, please start the recognition program first.')
                else:
                    self.prompts_lab.setText('相机打开失败，请检查摄像头连接是否正确,请先启动识别程序.')

        except Exception as e:
            e = traceback.format_exc()
            self.logger.error('Failed to open camera:' + str(e))
            if self.language == 1:
                self.prompts_lab(
                    'The camera failed to open, please check whether the camera connection is correct, please start the recognition program first.')
            else:
                self.prompts_lab('相机打开失败，请检查摄像头连接是否正确,请先启动识别程序.')
            if self.language == 1:
                self.open_camera_btn.setText('Open')
            else:
                self.open_camera_btn.setText('打开')
            self.btn_color(self.open_camera_btn, 'green')

    def close_camera(self):
        """
        隐藏摄像头画面信息
        Returns: None

        """
        try:
            self.show_camera_lab_rgb.hide()
            self.show_camera_lab_depth.hide()
            if self.language == 1:
                self.open_camera_btn.setText('Open')
            else:
                self.open_camera_btn.setText('打开')
            self.btn_color(self.open_camera_btn, 'green')
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def robot_pick_move(self, algorithm_mode):
        """
        根据识别到的点位信息，进行机械臂的抓取移动(颜色识别、形状识别、yolov8识别）
        Returns: None

        """
        try:
            self.offset_x = int(self.xoffset_edit.text())
            self.offset_y = int(self.yoffset_edit.text())
            self.offset_z = int(self.zoffset_edit.text())
            self.algorithm_mode = algorithm_mode
            if self.algorithm_mode in self.algorithm_pump:
                target_base_pos3d = target_base_pos3d_pump
                arm_pick_hover_angle = arm_pick_hover_angle_pump
            else:
                target_base_pos3d = target_base_pos3d_gripper
                arm_pick_hover_angle = arm_pick_hover_angle_gripper
            coords_transformer = CoordCalc(
                target_base_pos3d,
                (final_frame_size // 2, final_frame_size // 2),
                plane_frame_size_ratio,
            )
            if self.is_crawl and self.is_discern and self.pos_x != 0 and self.pos_y != 0 and self.pos_z != 0:
                self.is_pick = False
                self.mc.send_angles(arm_pick_hover_angle, 50)
                time.sleep(3)
                # get target coord
                coord = coords_transformer.frame2real(self.pos_x, self.pos_y)
                coord = list(coord)
                # adjust final offset
                off_x, off_y, off_z = (self.offset_x, self.offset_y, self.offset_z)

                if self.algorithm_mode in ['颜色识别 吸泵', 'Color recognition pump', '形状识别 吸泵',
                                           'Shape recognition pump']:

                    coord[0] += final_coord_offset[0] + off_x
                    coord[1] += final_coord_offset[1] + off_y
                    coord[2] += final_coord_offset[2] + off_z + self.pos_z

                    coord.extend([179, 0, -75])

                    target_xy_pos3d = coord.copy()[:3]
                    target_xy_pos3d[2] = 50
                    # 运动至物体上方
                    self.logger.info('X-Y move: {}'.format(target_xy_pos3d))

                    position_move(self.mc, *target_xy_pos3d)
                    time.sleep(4)
                    # 运动至物体表面
                    self.logger.info('Target move: {}'.format(coord))
                    self.mc.send_coords(coord, 70, 1)
                    time.sleep(1)
                    while self.mc.is_moving():
                        time.sleep(0.2)
                    time.sleep(1)

                    if self.mc.is_in_position(coord, 1) != 1:
                        self.mc.send_coords(coord, 70, 1)
                    time.sleep(1)
                elif self.algorithm_mode in ['yolov8 pump', 'yolov8 吸泵']:
                    coord[0] += final_coord_offset[0] + off_x + 5
                    coord[1] += final_coord_offset[1] + off_y
                    coord[2] += final_coord_offset[2] + self.pos_z - 20 + off_z

                    coord.extend([179, 0, -75])
                    coord_xy = coord.copy()[:3]
                    coord_xy[2] = 50

                    # self.mc.send_coords(coord_xy, 50)
                    # 运行至物体上方
                    self.logger.info('X-Y move: {}'.format(coord_xy))
                    position_move(self.mc, *coord_xy)
                    time.sleep(4)
                    # 运动至物体表面
                    self.logger.info('Target move: {}'.format(coord))
                    self.mc.send_coords(coord, 70, 1)
                    time.sleep(1)
                    while self.mc.is_moving():
                        time.sleep(0.2)
                    time.sleep(1)

                    if self.mc.is_in_position(coord, 1) != 1:
                        self.mc.send_coords(coord, 70, 1)
                    time.sleep(1)
                elif self.algorithm_mode in ['yolov8 gripper', 'yolov8 夹爪', '颜色识别 夹爪',
                                             'Color recognition gripper']:
                    angle = 0
                    coord[0] += final_coord_offset[0] + off_x
                    coord[1] += final_coord_offset[1] + off_y
                    coord[2] += final_coord_offset[2] + self.pos_z + off_z
                    # rz = 90 + (90 - angle)
                    # rz = 90 + (90 - 10)
                    coord.extend([179, 0, 40])
                    coord_xy = coord.copy()[:3]
                    coord_xy[2] = 70
                    # 运行至物体上方
                    self.logger.info('X-Y move: {}'.format(coord_xy))
                    # self.mc.send_coords(coord_xy, 50)
                    position_move(self.mc, *coord_xy)
                    time.sleep(3)

                if self.algorithm_mode in self.algorithm_pump:
                    self.pump_on()
                    time.sleep(2)
                    self.mc.send_coord(3, 90, 40)
                    time.sleep(3)

                else:
                    open_gripper(self.mc)
                    time.sleep(3)
                    # self.mc.send_coords(coord, 40, 1)
                    self.mc.send_coord(3, off_z, 50)
                    time.sleep(3)
                    close_gripper(self.mc)
                    time.sleep(3)
                    self.mc.send_coord(3, 90, 50)
                    time.sleep(2.5)
                self.is_crawl = False
                # self.btn_color(self.crawl_btn, 'blue')
                self.set_button_color.emit(self.crawl_btn, 'blue')
            else:
                self.logger.error('请先开启识别程序....')
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def pallet_auto_pick(self, algorithm_mode):
        """
        码垛自动抓取,根据识别到的点位信息，进行机械臂的抓取移动
        Returns: None

        """
        try:
            random_number = random.randint(0, 3)

            self.offset_x = int(self.xoffset_edit.text())
            self.offset_y = int(self.yoffset_edit.text())
            self.offset_z = int(self.zoffset_edit.text())
            self.algorithm_mode = algorithm_mode
            if self.algorithm_mode in self.algorithm_pump:
                target_base_pos3d = target_base_pos3d_pump
                arm_pick_hover_angle = arm_pick_hover_angle_pump
            else:
                target_base_pos3d = target_base_pos3d_gripper
                arm_pick_hover_angle = arm_pick_hover_angle_gripper
            coords_transformer = CoordCalc(
                target_base_pos3d,
                (final_frame_size // 2, final_frame_size // 2),
                plane_frame_size_ratio,
            )
            if self.is_crawl and self.pos_x != 0 and self.pos_y != 0 and self.pos_z != 0:
                self.is_pick = False
                self.mc.send_angles(arm_pick_hover_angle, 50)
                time.sleep(3)
                # get target coord
                coord = coords_transformer.frame2real(self.pos_x, self.pos_y)
                coord = list(coord)
                # adjust final offset
                off_x, off_y, off_z = (self.offset_x, self.offset_y, self.offset_z)
                # self.logger.info('坐标参数------>coord:{} offset:{} pos_z: {} off_Z: {}'.format(coord, final_coord_offset, self.pos_z, off_z))
                print('coords param---->', coord, final_coord_offset, self.pos_z, off_x, off_y, off_z)
                coord[0] += final_coord_offset[0] + off_x + 5
                coord[1] += final_coord_offset[1] + off_y
                coord[2] += final_coord_offset[2] + self.pos_z - 20 + off_z

                coord.extend([179, 0, -75])
                coord_xy = coord.copy()[:3]
                coord_xy[2] = 50
                # 运动至物体上方
                # self.logger.info('X-Y move: {}'.format(coord_xy))
                # self.mc.send_coords(coord_xy, 50)
                position_move(self.mc, *coord_xy)
                time.sleep(1)
                # 运行至物体表面

                self.logger.info('Target move to pump: {}'.format(coord))
                print('real pump coords ---------->', coord)
                self.mc.send_coords(coord, 70, 1)
                time.sleep(1)
                while self.mc.is_moving():
                    time.sleep(0.2)
                time.sleep(1)

                if self.mc.is_in_position(coord, 1) != 1:
                    self.mc.send_coords(coord, 70, 1)
                time.sleep(1)

                self.pump_on()
                time.sleep(2)
                self.mc.send_coord(3, 90, 70)
                time.sleep(5)

                self.mc.send_angles(box_position[random_number], 50)
                time.sleep(3)
                self.pump_off()
                time.sleep(1.5)
                self.mc.send_angles(arm_idle_angle, 50)
                time.sleep(4)
                self.pos_x, self.pos_y, self.pos_z = 0, 0, 0
                self.is_pick = True
            else:
                self.logger.error('请开启码垛识别程序!!!')
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def start_pallet_crawl(self, mode):
        """
        开启码垛自动抓取的while循环程序
        Returns:

        """
        try:
            self.algorithm_mode = mode
            while self.is_crawl:
                if self.algorithm_mode in ['Depalletizing pump', '拆码垛 吸泵']:
                    if self.pos_x != 0 and self.pos_y != 0 and self.pos_z != 0:
                        self.pallet_auto_pick(self.algorithm_mode)
                        time.sleep(0.5)
                    else:
                        self.logger.info(
                            '拆码垛程序已抓取完成!!! x-y-z:{} {} {}'.format(self.pos_x, self.pos_y, self.pos_z))
                        self.is_crawl = False
                        # self.btn_color(self.crawl_btn, 'blue')
                        self.set_button_color.emit(self.crawl_btn, 'blue')
                        break
                else:
                    self.logger.info('当前不是拆码垛程序!!!')
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))

    def robot_place_move(self, algorithm_mode):
        """
        选择机械臂投放物体的放置点
        Returns:

        """
        try:
            self.algorithm_mode = algorithm_mode
            if self.is_place:
                print('start place')
                if self.radioButton_A.isChecked():
                    pos_id = 2
                elif self.radioButton_B.isChecked():
                    pos_id = 3
                elif self.radioButton_C.isChecked():
                    pos_id = 1
                else:
                    pos_id = 0
                self.mc.send_angles(box_position[pos_id], 50)
                time.sleep(3)
                if self.algorithm_mode in self.algorithm_pump:
                    self.pump_off()
                    self.mc.send_angles(arm_idle_angle, 50)
                    time.sleep(4)
                else:
                    open_gripper(self.mc)
                    time.sleep(3)
                    self.mc.send_angles(arm_idle_angle, 50)
                    time.sleep(4)
                    release_gripper(self.mc)
                    time.sleep(0.1)
                self.is_place = False
                # self.place_btn.setEnabled(False)
                self.update_btn_state.emit(self.place_btn, False)
                # self.btn_color(self.place_btn, 'gray')
                self.set_button_color.emit(self.place_btn, 'gray')
                time.sleep(1.5)
                self.is_pick = True
            else:
                self.logger.error('放置按钮无响应，请重试！！！')
        except Exception as e:
            e = traceback.format_exc()
            self.logger.error(str(e))


def resource_path(relative_path):
    """
    根据相对路径返回一个资源文件的绝对路径。
    Args:
        relative_path: 相对路径

    Returns: 绝对路径

    """
    # check if Bundle Resource
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


if __name__ == '__main__':
    try:
        libraries_path = resource_path('resources')
        libraries_path = libraries_path.replace("\\", "/")
        print(libraries_path)
        app = QApplication(sys.argv)
        AiKit_window = AiKit_App()
        AiKit_window.show()
    except Exception as e:
        e = traceback.format_exc()
        with open(libraries_path + '/log/message.log', "a+", encoding='utf-8') as f:
            f.write(str(e))
    sys.exit(app.exec())
