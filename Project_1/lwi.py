#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" This is the extra class of a server/client application in which the client can
create MAX_CLIENTS number of sub-clients. Each client will have its own socket,
running on its own thread. The server will then give a countdown timer to a randomly
selected client, which the client will then use to countdown (displayed in client's GUI).
This class is used to define the QListWidgetItem that is used to display the clients.
Each client is a QListWidgetItem within the QListWidget. Created due to clients
usually having a unique countdown label associated with them."""

__author__ = "Hannan Khan"
__credits__ = ["Hannan Khan"]
__version__ = "1.0"
__maintainer__ = "Hannan Khan"
__email__ = "hannan.khan@mavs.uta.edu"

import PyQt5
from PyQt5.QtWidgets import QListWidgetItem, QLabel

class ClientWidgetItem(QListWidgetItem):
    def __init__(self, text: str = "", associated_countdown_label: QLabel = None):
        super(ClientWidgetItem, self).__init__()
        self.setText(text)
        self.associated_countdown_label = associated_countdown_label
