import sys

from PySide6.QtCore import Qt, QDir
from PySide6.QtGui import QPixmap, QAction, QImage, QPainter, QUndoStack, QFont, QFontDatabase, QColor
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QVBoxLayout, QScrollArea, QLabel, \
    QHBoxLayout, QWidget, QStatusBar, QGraphicsScene, QGraphicsPixmapItem, QSlider, QColorDialog, \
    QComboBox

from custom_widgets import ClickableImgLabel, MyPushButton, PaintGraphicsView
from q_thread import ImageWorker
from util import *


class ImageBrowser(QMainWindow):
    """
    图片浏览器类
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle('hh 图像浏览器')
        self.setGeometry(100, 100, 512, 512)

        self.initResources()
        self.initMenus()
        self.initUI()

    def initUI(self):

        # 主窗口部件和布局
        self.mainWidget = QWidget()
        self.mainLayout = QHBoxLayout()

        self.initToolBar()

        # 左侧的垂直滚动区域
        self.scrollWidget = QWidget()
        self.scrollWidget.setObjectName("scrollWidget")
        self.scrollLayout = QVBoxLayout()
        # 不同缩略图之间有一定的间距
        self.scrollLayout.setSpacing(10)
        self.scrollLayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scrollWidget.setLayout(self.scrollLayout)

        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

        # 右侧的预览图片显示区域
        self.imagePreviewScene = QGraphicsScene(self)
        self.imagePreviewView = PaintGraphicsView(self.imagePreviewScene, self)

        # 底部状态栏
        self.initStatusBar()

        self.mainLayout.addWidget(self.scrollArea, 1)
        self.mainLayout.addWidget(self.imagePreviewView, 3)
        self.mainWidget.setLayout(self.mainLayout)

        self.setCentralWidget(self.mainWidget)

    def initResources(self):
        # 当前的缩略图
        self.current_thumbnail = None
        # 增加图片缩放的缓存
        self.img_resize_cache = {}
        # 预览图缩放比例
        self.zoom_level = 100

    def initMenus(self):
        # 创建菜单栏
        self.file_menu = self.menuBar().addMenu("文件")

        # 创建一个"Open"菜单项
        self.open_action = QAction("打开", self)
        self.open_action.triggered.connect(self.openImageDialog)
        self.file_menu.addAction(self.open_action)

        self.edit_menu = self.menuBar().addMenu('编辑')
        self.color_picker_action = QAction('工具栏', self)
        self.color_picker_action.triggered.connect(self.show_tool_bar)
        self.edit_menu.addAction(self.color_picker_action)

        # 撤销/重做
        self.undoStack = QUndoStack(self)
        self.undo_action = self.undoStack.createUndoAction(self, '撤销')
        self.undo_action.setShortcut('Ctrl+Z')
        self.edit_menu.addAction(self.undo_action)

        self.redo_action = self.undoStack.createRedoAction(self, '重做')
        self.redo_action.setShortcut('Shift+Ctrl+Z')
        self.edit_menu.addAction(self.redo_action)

    def initStatusBar(self):
        # 底部状态栏
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        # Create zoom in/out buttons
        self.zoom_in_button = MyPushButton("resource/icons/zoom_in_icon.png", self)
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_out_button = MyPushButton("resource/icons/zoom_out_icon.png", self)
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.status_bar.addPermanentWidget(self.zoom_in_button)
        self.status_bar.addPermanentWidget(self.zoom_out_button)
        # 可以显示缩放程度的文本
        self.zoom_label = QLabel('100%')
        self.status_bar.addPermanentWidget(self.zoom_label)  # addPermanentWidget 会将 widget 添加到 statusbar 的右侧
        # 可以滑动控制图像缩放的比例
        self.zoom_slider = QSlider(Qt.Horizontal, self)
        self.zoom_slider.setMinimum(5)  # 5% as minimum zoom level
        self.zoom_slider.setMaximum(500)  # 500% as maximum zoom level
        self.zoom_slider.setValue(self.zoom_level)  # 100% as initial zoom level
        self.zoom_slider.valueChanged.connect(self.zoom_slider_moved)
        self.status_bar.addPermanentWidget(self.zoom_slider)

    def initToolBar(self):
        """
        初始化工具栏
        :return:
        """
        # 工具栏
        self.tool_bar = self.addToolBar('工具栏')

        # 在工具栏创建文本编辑按钮，以及显示字体和颜色的标签
        # 文本编辑
        self.text_edit_button = MyPushButton("resource/icons/text_edit_icon.png")
        self.text_edit_button.setCheckable(True)
        self.text_edit_button.clicked.connect(self.select_text_edit)

        self.update_text_edit_font_config()
        # 用于显示颜色的label
        self.color_picker_label = QLabel()

        self.tool_bar.addWidget(self.text_edit_button)
        self.tool_bar.addWidget(self.text_edit_font_combo_box)
        self.tool_bar.addWidget(self.text_edit_font_size_combo_box)
        self.tool_bar.addWidget(self.color_picker_label)

        # 调色盘
        self.color_painter_button = MyPushButton("resource/icons/painter_icon.png")
        self.color_painter_button.setCheckable(True)
        self.color_painter_button.clicked.connect(self.show_painter)

        self.color_picker_button = MyPushButton("resource/icons/color_picker_icon.png")
        self.color_picker_button.clicked.connect(lambda event: self.color_picker.show())

        self.color_picker = QColorDialog(self)
        # 设置默认颜色为黑色
        self.text_edit_color = QColor("black")
        self.color_picker.currentColorChanged.connect(self.change_color)
        self.color_picker.hide()

        self.pen_size_label = QLabel("画笔大小:3")
        self.pen_size_slider = QSlider(Qt.Horizontal, self)
        self.pen_size_slider.setRange(1, 50)
        self.pen_size_slider.setValue(3)
        self.pen_size_slider.valueChanged.connect(self.change_pen_size)

        self.save_image_button = MyPushButton("resource/icons/save_icon.png")
        self.save_image_button.clicked.connect(self.save_preview_image)

        self.reset_image_button = MyPushButton("resource/icons/reset_icon.png")
        self.reset_image_button.clicked.connect(self.reset_all)

        self.tool_bar.addWidget(self.color_picker_button)
        self.tool_bar.addWidget(self.color_painter_button)
        self.tool_bar.addWidget(self.color_picker)
        self.tool_bar.addWidget(self.pen_size_label)
        self.tool_bar.addWidget(self.pen_size_slider)
        self.tool_bar.addWidget(self.save_image_button)
        self.tool_bar.addWidget(self.reset_image_button)

        # 工具栏和调色盘是默认隐藏的
        self.tool_bar.hide()

    def update_text_edit_font_config(self):
        # 字体选择下拉框
        self.text_edit_font_combo_box = QComboBox()
        # 字号选择下拉框
        self.text_edit_font_size_combo_box = QComboBox()
        # 获取系统中所有可用的字体
        self.all_fonts = QFontDatabase().families()
        # 获取可能的字号
        self.all_font_sizes = QFontDatabase.standardSizes()
        # 添加字体和字号到拉列表
        self.text_edit_font_combo_box.addItems(self.all_fonts)
        self.text_edit_font_size_combo_box.addItems(map(str, self.all_font_sizes))  # 需要把字号转换成字符串才能添加到 QComboBox 中
        self.text_edit_font_combo_box.setPlaceholderText("请选择字体")
        self.text_edit_font_combo_box.currentIndexChanged.connect(lambda _: self.reset_text_edit_font())
        self.text_edit_font_size_combo_box.setPlaceholderText("请选择字号")
        self.text_edit_font_size_combo_box.currentIndexChanged.connect(lambda _: self.reset_text_edit_font())
        self.reset_text_edit_font()

    def select_text_edit(self, checked):
        """
        响应选中文本编辑
        :param checked:
        :return:
        """
        self.text_edit_button.setChecked(checked)
        if checked:
            self.show_painter(False)
            # 颜色区分处于选中状态
            self.text_edit_button.setStyleSheet("background-color: yellow")
        else:
            self.text_edit_button.setStyleSheet("background-color: white")

    def reset_text_edit_font(self, font=None, font_size=None):
        """
        重置 text_edit 的字体和字号
        :param font:
        :param font_size:
        :return:
        """
        reset_font = font if font else self.text_edit_font_combo_box.currentText()
        reset_font_size = font_size if font_size else int(self.text_edit_font_size_combo_box.currentText())
        self.text_edit_font = QFont(reset_font, reset_font_size)

    def show_tool_bar(self):
        self.tool_bar.show()

    def show_painter(self, checked):
        self.color_painter_button.setChecked(checked)
        if checked:
            self.select_text_edit(False)
            self.color_painter_button.setStyleSheet("background-color: yellow")
        else:
            self.color_painter_button.setStyleSheet("background-color: white")

    def change_color(self, color):
        """
        更改调色盘颜色
        :param color:
        :return:
        """
        self.text_edit_color = color
        self.imagePreviewView.pen.setColor(color)
        self.color_picker_label.setStyleSheet(f"background-color: {color.name()}")

    def change_pen_size(self, size):
        """
        更改调色盘画笔大小
        :param size:
        :return:
        """
        self.imagePreviewView.pen.setWidth(size)
        # 更改显示画笔大小
        self.set_pen_size_label(size)

    def set_pen_size_label(self, size):
        self.pen_size_label.setText(f"画笔大小:{size}")

    def save_preview_image(self):
        """
        保存预览区的图像
        :return:
        """
        image = QImage(self.imagePreviewScene.sceneRect().size().toSize(), QImage.Format_ARGB32)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        self.imagePreviewScene.render(painter)
        painter.end()

        # 使用文件对话框获取保存的文件名
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(self, "保存图像", "",
                                                   "PNG(*.png);;JPEG(*.jpg *.jpeg);;All Files(*.*) ")

        if file_path:
            image.save(file_path)

    def reset_all(self):
        """
        重置所有设置
        :return:
        """
        self.updatePreviewImage()
        self.zoom_label.setText("100%")
        self.zoom_slider.setValue(100)
        self.select_text_edit(False)
        self.show_painter(False)
        self.reset_text_edit_font(self.all_fonts[0], self.all_font_sizes[0])
        self.text_edit_font_combo_box.setCurrentText(self.all_fonts[0])
        self.text_edit_font_size_combo_box.setCurrentText(str(self.all_font_sizes[0]))
        self.color_picker_label.setStyleSheet("background-color: black")
        self.pen_size_slider.setValue(3)

    def openImageDialog(self):
        # 弹出文件/文件夹选择对话框
        path = QFileDialog.getOpenFileNames(self, 'Open Image Files', QDir.currentPath(),
                                            get_supported_img_suffix_str())

        # If a previous worker is running, stop it
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()  # Wait for the worker thread to finish

        # 重置滚动区域
        for i in reversed(range(self.scrollLayout.count())):
            self.scrollLayout.itemAt(i).widget().deleteLater()

        self.imageList = path[0]
        self.thumbnailLabels = []
        self.loadImages(self.imageList)

    def loadImages(self, paths):
        """
        异步加载图片
        :param paths:
        :return:
        """
        self.worker = ImageWorker(paths)
        self.worker.image_loaded.connect(self.addThumbnail)
        self.worker.start()

    def mk_img_resize_key(self, path, _type, width, height):
        """
        图像尺寸缩放结果缓存key
        :param path:
        :param _type:
        :param width:
        :param height:
        :return:
        """
        return f"{path}_{_type}_{width}_{height}"

    def get_resized_img(self, _type, path, width, height):
        """
        获取缩放调整尺寸之后的图像,每次优先从缓存中取,
        没有的话再新建并且加入缓存
        :param _type: 图像类型 thumbnail/preview
        :param path: 图像路径
        :param width: 图像宽度
        :param height: 图像高度
        :return:
        """
        key = self.mk_img_resize_key(path, _type, width, height)
        if key in self.img_resize_cache:
            return self.img_resize_cache[key]
        else:
            pixmap = QPixmap(path)
            new_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio)
            self.img_resize_cache[key] = new_pixmap
            return new_pixmap

    def addThumbnail(self, path, pixmap):
        """
        滚动区域添加缩略图
        :param path:
        :param pixmap:
        :return:
        """
        if len(path) > 0 and pixmap:
            thumbnail = ClickableImgLabel(path)
            thumbnail.clicked.connect(self.onThumbnailClicked)
            thumbnail.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio))
            self.scrollLayout.addWidget(thumbnail, alignment=Qt.AlignmentFlag.AlignCenter)
            self.thumbnailLabels.append(thumbnail)
        else:
            print("全部图像加载完成!")
            self.updateThumbnails()
        if len(self.thumbnailLabels) == 1:
            self.showPreviewImage(self.imageList[0])

    def onThumbnailClicked(self, path):
        """
        当缩略图被点击时
        :param path: 图像路径
        :return:
        """
        self.showPreviewImage(path)
        sender = self.sender()
        if self.current_thumbnail is not None:
            self.current_thumbnail.is_selected = False
        # 更新当前被选中的缩略图
        self.current_thumbnail = sender
        sender.is_selected = True

    def showPreviewImage(self, path):
        self.currentPreviewImagePath = path
        self.updatePreviewImage()

    def resizeEvent(self, event):
        # 窗口大小变化时，重新显示大图以及小图
        self.updatePreviewImage()
        self.updateThumbnails()

    def updateThumbnails(self):
        if hasattr(self, "thumbnailLabels"):
            for label in self.thumbnailLabels:
                pixmap = self.get_resized_img("thumbnail", label.path, self.scrollArea.width(), self.scrollArea.width())
                label.setPixmap(pixmap)

    def updatePreviewImage(self):
        if self._is_preview_img_ready():
            pixmap = self.get_resized_img("preview", self.currentPreviewImagePath,
                                          self.imagePreviewView.size().width(), self.imagePreviewView.size().height())

            self.imagePreviewScene.clear()
            self.imagePreviewScene.addItem(QGraphicsPixmapItem(pixmap))

    def _is_preview_img_ready(self):
        return hasattr(self, 'currentPreviewImagePath')

    def zoom_slider_moved(self, value):
        # Update zoom level
        self.zoom_level = value
        self.zoom_label.setText(f'{self.zoom_level}%')
        # 需要首先将图像恢复到原始尺寸
        self.imagePreviewView.resetTransform()
        self.zoomPreviewImage(self.zoom_level / 100)

    def zoom_in(self):
        """
        图像放大
        :return:
        """
        # 只有当实际预览图像加载出来时才响应
        if self._is_preview_img_ready():
            self.zoomPreviewImage(1.1)
            self.zoom_level += 10  # increase zoom level by 10%
            self.zoom_slider.setValue(self.zoom_level)
            self.zoom_label.setText(f'{self.zoom_level}%')

    def zoom_out(self):
        """
        图像缩小
        :return:
        """
        # 只有当实际预览图像加载出来时才响应
        if self._is_preview_img_ready():
            self.zoomPreviewImage(0.9)
            self.zoom_level -= 10  # decrease zoom level by 10%
            self.zoom_slider.setValue(self.zoom_level)
            self.zoom_label.setText(f'{self.zoom_level}%')

    def zoomPreviewImage(self, zoom_level):
        """
        缩放预览图的尺寸
        :return:
        """
        self.imagePreviewView.scale(zoom_level, zoom_level)
