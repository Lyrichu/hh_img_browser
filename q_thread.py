# -*- coding:utf-8 -*-
# author:lyrichu@foxmail.com
# @Time: 2023/7/24 17:52
"""
Qt 多线程 相关
"""
from PySide6.QtCore import QThread, Signal, QMutex
from PySide6.QtGui import QPixmap, QImage


class ImageWorker(QThread):
    """
    图像加载工具类
    """
    # (图像路径,加载完的img_pixel)
    image_loaded = Signal(str, QPixmap)

    def __init__(self, paths):
        """
        :param paths: 图像路径列表
        """
        super().__init__()
        self.paths = paths
        # 确保线程安全
        self.mutex = QMutex()
        # 是否正在加载图片
        self._isRunning = True

    def run(self):
        for path in self.paths:
            self.mutex.lock()
            if not self._isRunning:
                self.mutex.unlock()
                break
            img = QImage(path)
            pixmap = QPixmap.fromImage(img)
            self.image_loaded.emit(path, pixmap)
            self.mutex.unlock()
        # 当全部图像加载完成之后,发送一个完成信号
        self.image_loaded.emit("", None)

    def stop(self):
        self.mutex.lock()
        self._isRunning = False
        self.mutex.unlock()
