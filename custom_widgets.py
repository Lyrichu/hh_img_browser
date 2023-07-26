# -*- coding:utf-8 -*-
# author:lyrichu@foxmail.com
# @Time: 2023/7/24 17:49
"""
自定义相关控件
"""
from PySide6.QtCore import Signal, Qt, QSize, QPointF, QLineF, QRectF
from PySide6.QtGui import QPainter, QPen, QIcon, QUndoCommand, QPainterPath, QTextCursor
from PySide6.QtWidgets import QLabel, QPushButton, QGraphicsView, QGraphicsLineItem, QGraphicsPathItem, \
    QGraphicsTextItem


class MyPushButton(QPushButton):
    """
    自定义 QPushButton
    """

    def __init__(self, icon_path, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QPushButton {border: none;}")
        icon = QIcon(icon_path)
        self.setIcon(icon)

    def resizeEvent(self, event):
        self.setIconSize(QSize(24, 24))
        super().resizeEvent(event)


class ClickableImgLabel(QLabel):
    """
    可点击的 图像 QLabel
    """
    # 定义一个点击事件的信号
    clicked = Signal(str)

    def __init__(self, path, *args, **kwargs):
        """
        :param path: 图像路径
        :param args:
        :param kwargs:
        """
        super(ClickableImgLabel, self).__init__(*args, **kwargs)
        self.path = path
        self._is_selected = False
        self.setFrameShape(QLabel.Box)
        self.setLineWidth(0)

    def mousePressEvent(self, event):
        # 当鼠标点击时，发送 图像路径 作为信号
        self.clicked.emit(self.path)
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self._is_selected = not self._is_selected
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.LeftButton, Qt.RightButton):
            self._is_selected = not self._is_selected
            self.update()

    def _update_line_width(self, width=4):
        if self._is_selected:
            self.setLineWidth(width)
            # 更改样式
            painter = QPainter(self)
            pen = QPen(Qt.gray, 3)  # Change "Qt.black" to "Qt.gray"
            painter.setPen(pen)
            painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        else:
            self.setLineWidth(0)

    def paintEvent(self, event):
        QLabel.paintEvent(self, event)
        self._update_line_width()

    @property
    def is_selected(self):
        return self._is_selected

    @is_selected.setter
    def is_selected(self, value):
        self._is_selected = value
        self.update()


class PaintGraphicsView(QGraphicsView):
    """
    自定义图像展示组件,支持鼠标点击进行画笔操作等功能
    """

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.parent = parent
        self.last_point = QPointF()
        self.pen = QPen(Qt.red, 1)
        self.items = []  # 保存临时的线段对象

    def mousePressEvent(self, event):
        if self.parent.text_edit_button.isChecked():
            self.initial_point = self.mapToScene(event.pos())
            self.text_item = QGraphicsTextItem()
            self.text_item.setPlainText("请输入文字")
            self.text_item.setFont(self.parent.text_edit_font)
            self.text_item.setDefaultTextColor(self.parent.text_edit_color)
            self.text_item.setPos(self.initial_point)
            self.scene().addItem(self.text_item)
            self.text_item.setFocus()  # 使文本框获得焦点以便用户直接输入文本
            # 移动光标到最后
            text_cursor = self.text_item.textCursor()
            text_cursor.movePosition(QTextCursor.End)
            self.text_item.setTextCursor(text_cursor)
        elif self.parent.color_painter_button.isChecked():
            self.last_point = self.mapToScene(event.pos())

    def mouseMoveEvent(self, event):
        if self.parent.text_edit_button.isChecked():
            current_point = self.mapToScene(event.pos())
            width = current_point.x() - self.initial_point.x()
            height = current_point.y() - self.initial_point.y()
            rect = QRectF(self.initial_point.x(), self.initial_point.y(), width, height)
            self.text_item.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)  # make the text editable
            self.text_item.setPos(rect.topLeft())
            self.text_item.setTextWidth(rect.width())
        elif self.parent.color_painter_button.isChecked():
            current_point = self.mapToScene(event.pos())
            line = QGraphicsLineItem(QLineF(self.last_point, current_point))
            line.setPen(self.pen)
            self.scene().addItem(line)  # 实时添加线段到场景
            self.items.append(line)  # 添加线段到列表
            self.last_point = current_point

    def mouseReleaseEvent(self, event):
        if self.parent.text_edit_button.isChecked():
            self.parent.select_text_edit(False)
            command = AddTextCommand(self.scene(), self.text_item)
            self.parent.undoStack.push(command)
        elif self.parent.color_painter_button.isChecked():
            self.parent.show_painter(False)
            # 创建一个新的 AddCommand 并添加到 undoStack
            command = AddPainterCommand(self.scene(), self.items, self.pen)
            self.parent.undoStack.push(command)
            self.items = []  # 清空临时列表


class AddPainterCommand(QUndoCommand):
    def __init__(self, scene, items, pen):
        super().__init__()
        self.scene = scene
        self.items = items  # 保存线段列表和画笔样式
        self.pen = pen

    def undo(self):
        for item in self.items:
            self.scene.removeItem(item)

    def redo(self):
        for item in self.items:
            self.scene.addItem(item)


class AddTextCommand(QUndoCommand):
    def __init__(self, scene, text_item):
        super().__init__()
        self.scene = scene
        self.text_item = text_item

    def undo(self):
        self.scene.removeItem(self.text_item)

    def redo(self):
        self.scene.addItem(self.text_item)
