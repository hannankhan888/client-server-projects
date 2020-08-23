"""HANNAN KHAN
1001815455"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""This is the utility module for the client/server application. It contains a dialog class
which will prompt the user to select an action (Upload/Check).
It also contains any and all functions that are shared between the server and the
client."""

__author__ = "Hannan Khan"
__credits__ = ["Hannan Khan"]
__version__ = "1.0"
__maintainer__ = "Hannan Khan"
__email__ = "hannan.khan@mavs.uta.edu"

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt


class UploadCheckDialog(QtWidgets.QDialog):
    def __init__(self, current_font: QtGui.QFont, client_name: str, client_idx: int):
        super(UploadCheckDialog, self).__init__()

        # reference:
        # https://stackoverflow.com/questions/81627/how-can-i-hide-delete-the-help-button-on-the-title-bar-of-a-qt-dialog
        self.setWindowFlags(Qt.WindowCloseButtonHint | Qt.WindowTitleHint | Qt.WindowSystemMenuHint)
        self.setWindowTitle("Action Needed")
        self.setFont(current_font)
        self.selection = -1

        self.client_name = client_name
        self.client_idx = client_idx

        self.client_name_label = QtWidgets.QLabel()
        self.client_name_label.setText(self.client_name + ":")

        self.upload_btn = QtWidgets.QPushButton()
        self.upload_btn.setText("Upload Message")
        self.upload_btn.clicked.connect(lambda: self.change_selection(0))

        self.check_btn = QtWidgets.QPushButton()
        self.check_btn.setText("Check For Messages")
        self.check_btn.clicked.connect(lambda: self.change_selection(1))

        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addWidget(self.client_name_label)
        self.main_layout.addWidget(self.upload_btn)
        self.main_layout.addWidget(self.check_btn)

        self.setLayout(self.main_layout)

    def change_selection(self, n):
        """Changes the value of selection based on which button was pressed:
        Window Close == -1
        Upload Message == 0
        Check For Messages == 1"""

        if n == 0:
            self.selection = 0
        elif n == 1:
            self.selection = 1
        else:
            self.selection = -1

        self.close()


def get_client_idx(self: QMainWindow = None, client_name: str = "") -> int:
    """Gets the clients index in the list based on its name.
    This func is used in both client.py and server.py."""

    for i in range(0, self.client_list_widget.count()):
        item = self.client_list_widget.item(i)
        if item.text() == client_name:
            return i

    return -1
