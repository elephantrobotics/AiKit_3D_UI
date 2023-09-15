#!/usr/bin/python
# -*- coding:utf-8 -*-
# @File    : logfile.py
# @Author  : Wang Weijian
# @Time    :  2023/09/12 09:49:53
# @function: the script is used to do something
# @version : V1

import logging
import time
import os


class MyLogging:

    def __init__(self):
        timestr = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
        lib_path = os.path.split(os.path.abspath(__file__))
        filename = lib_path[0] + '/message.log'  # 日志文件的地址
        # print(filename)
        self.logger = logging.getLogger()  # 定义对应的程序模块名name，默认为root
        self.logger.setLevel(logging.DEBUG)  # 必须设置，这里如果不显示设置，默认过滤掉warning之前的所有级别的信息
        # 设置格式对象
        formatter = logging.Formatter(
            "%(asctime)s %(filename)s[line:%(lineno)d]%(levelname)s - %(message)s")  # 定义日志输出格式

        sh = logging.StreamHandler()  # 日志输出到屏幕控制台
        sh.setLevel(logging.INFO)  # 设置日志等级
        sh.setFormatter(formatter)  # 设置handler的格式对象

        fh = logging.FileHandler(filename=filename, encoding='utf-8')  # 向文件filename输出日志信息
        fh.setLevel(logging.INFO)  # 设置日志等级
        fh.setFormatter(formatter)  # 设置handler的格式对象

        # 将handler增加到logger中
        self.logger.addHandler(sh)
        self.logger.addHandler(fh)

