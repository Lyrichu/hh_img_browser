# -*- coding:utf-8 -*-
# author:lyrichu@foxmail.com
# @Time: 2023/7/25 10:06
"""
通用工具类
"""
from PySide6.QtGui import QImageReader


def get_supported_img_suffix_list():
    """
    获取系统支持的图像文件后缀
    :return:
    """
    return [v.data().decode("utf-8") for v in QImageReader.supportedImageFormats()]


def get_supported_img_suffix_str():
    return f"Images ({' '.join(['*.' + suffix for suffix in get_supported_img_suffix_list()])})"
