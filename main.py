# -*- coding:utf-8 -*-
# author:lyrichu@foxmail.com
# @Time: 2023/7/26 17:59
import sys

from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from img_browser import ImageBrowser

app = QApplication(sys.argv)
imageBrowser = ImageBrowser()
# with open("styles/stylesheet.qss", "r", encoding="utf-8") as fin:
#     imageBrowser.setStyleSheet(fin.read())
apply_stylesheet(app, theme='light_pink.xml')
imageBrowser.show()
sys.exit(app.exec())
