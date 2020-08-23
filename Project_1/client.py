"""HANNAN KHAN
1001815455"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

""" This is the (GUI) client-side of a server/client application in which the client can create
MAX_CLIENTS number (defined in server.py) of sub-clients. Each client will have its
own socket, running on its own thread. The server will then give a countdown timer to
a randomly selected client, which the client will then use to countdown (displayed in GUI)."""

__author__ = "Hannan Khan"
__credits__ = ["Hannan Khan"]
__version__ = "1.0"
__maintainer__ = "Hannan Khan"
__email__ = "hannan.khan@mavs.uta.edu"

import sys, socket, threading, time
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, QMessageBox
from lwi import ClientWidgetItem

PORT_NUMBER = 55556
HOST = socket.gethostname()


class ClientApp(QMainWindow):
    def __init__(self, screen_width: int, screen_height: int):
        super(ClientApp, self).__init__()
        self.WIDTH = 1000
        self.HEIGHT = 563
        self.SCREEN_WIDTH = screen_width
        self.SCREEN_HEIGHT = screen_height
        self.X = int((self.SCREEN_WIDTH / 2) - (self.WIDTH / 2))
        self.Y = int(self.SCREEN_HEIGHT / 10) + 625
        self.setGeometry(self.X, self.Y, self.WIDTH, self.HEIGHT)
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setWindowTitle("Client")

        self.main_frame = QtWidgets.QFrame()
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.main_inter_layout = QtWidgets.QVBoxLayout()
        self.main_inter_layout.setSpacing(0)
        self.main_inter_layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout.addLayout(self.main_inter_layout)

        self.current_font = QFont("Consolas", 10)

        self._init_menu()
        self._init_top_layout()
        self._init_middle_layout()

        # this var has the index for the current selected client.
        self.selected_client_idx = None
        # these arrays keep track of all clients' labels, threads, and sockets.
        self.list_of_all_countdown_labels = []
        self.list_of_all_threads = []
        self.list_of_all_sockets = []

        # finishing the setup of the GUI here.
        self.status_label = QtWidgets.QLabel()
        self.status_label.setFont(self.current_font)
        self.status_label.setText("Status Box")
        self.main_inter_layout.addWidget(self.status_label)
        self.status_box = QtWidgets.QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setFont(self.current_font)
        self.main_inter_layout.addWidget(self.status_box)

        self.main_frame.setLayout(self.main_layout)
        self.setCentralWidget(self.main_frame)
        self.show()

    def _init_menu(self):
        """Creates the menu and the actions/shortcuts associated with each option."""

        self.top_menu_bar = QtWidgets.QMenuBar()
        self.file_menu = self.top_menu_bar.addMenu("&File")

        self.add_client_action = QtWidgets.QAction("&Add New Client", self)
        self.add_client_action.setShortcut(QtGui.QKeySequence(Qt.CTRL + Qt.Key_A))
        self.add_client_action.triggered.connect(self.add_new_client)

        self.delete_client_action = QtWidgets.QAction("&Delete Selected Client", self)
        self.delete_client_action.setShortcut(QtGui.QKeySequence(Qt.Key_Delete))
        self.delete_client_action.triggered.connect(self.delete_client)

        self.exit_action = QtWidgets.QAction("&Exit", self)
        self.exit_action.setShortcut(QtGui.QKeySequence(Qt.CTRL + Qt.Key_Q))
        self.exit_action.triggered.connect(self.exit_app)

        self.file_menu.addActions([self.add_client_action, self.delete_client_action, self.exit_action])
        self.main_layout.setMenuBar(self.top_menu_bar)

    def _init_top_layout(self):
        """Sets up the top half of the GUI."""

        self.top_layout = QtWidgets.QHBoxLayout()
        self.top_layout.setSpacing(15)

        self.client_label = QtWidgets.QLabel()
        self.client_label.setText("Clients")
        self.client_label.setFont(self.current_font)

        self.add_client_button = QtWidgets.QPushButton()
        self.add_client_button.setFont(self.current_font)
        self.add_client_button.setText("Add New Client")
        self.add_client_button.clicked.connect(self.add_new_client)

        self.delete_client_button = QtWidgets.QPushButton()
        self.delete_client_button.setFont(self.current_font)
        self.delete_client_button.setText("Delete Selected Client")
        self.delete_client_button.clicked.connect(self.delete_client)

        self.stop_countdown_button = QtWidgets.QPushButton()
        self.stop_countdown_button.setFont(self.current_font)
        self.stop_countdown_button.setText("Stop Countdown")
        self.stop_countdown_button.clicked.connect(self.stop_countdown_of_selected_client)

        self.top_layout.addWidget(self.client_label)
        self.top_layout.addWidget(self.add_client_button)
        self.top_layout.addWidget(self.delete_client_button)
        self.top_layout.addWidget(self.stop_countdown_button)

        self.main_inter_layout.addLayout(self.top_layout)

    def _init_middle_layout(self):
        """Sets up the middle of the GUI."""

        self.middle_layout = QtWidgets.QHBoxLayout()
        self.middle_layout.setSpacing(10)

        self.client_list_widget = QtWidgets.QListWidget()
        self.client_list_widget.setFont(self.current_font)
        self.client_list_widget.setFixedSize(540, 220)
        self.client_list_widget.itemClicked.connect(self.show_selected_client_countdown)

        self.countdown_frame = QtWidgets.QFrame()

        self.middle_layout.addWidget(self.client_list_widget)
        self.middle_layout.addWidget(self.countdown_frame)

        self.main_inter_layout.addLayout(self.middle_layout)

    def add_new_client(self):
        """Allows for the creation of a new client within the GUI. The client is created
        regardless of a duplicate existing. The client is then assigned a socket, via its
        own thread. It is within this thread that the server will be contacted, and
        duplicity determined."""

        boo = True
        client_exists = False
        msg_box = QInputDialog()
        text, boo = msg_box.getText(self, "Add New Client", "Insert New Client Name")
        while boo and not text:
            text, boo = msg_box.getText(self, "Add New Client", "Insert New Client Name\nClient name cannot be empty.")

        if boo and not client_exists:
            # create an associated countdown label for this client, and append it to the list:
            new_countdown_label = QtWidgets.QLabel()
            new_countdown_label.setFont(QFont("Consolas", 25))
            new_countdown_label.setText("0")
            self.list_of_all_countdown_labels.append(new_countdown_label)
            self.middle_layout.addWidget(new_countdown_label)
            self.show_selected_client_countdown()

            # create a new client widget item. This will have the countdown label association.
            new_client_widget_item = ClientWidgetItem(text=text, associated_countdown_label=new_countdown_label)
            self.client_list_widget.addItem(new_client_widget_item)
            self.client_list_widget.setCurrentItem(self.client_list_widget.item(self.client_list_widget.count() - 1))
            self.update_selected_client_idx()
            client_idx = self.get_client_idx(text)
            # Here we start to create the socket for the client, in its own thread.
            self.create_socket_with_thread(text, new_client_widget_item, client_idx)

    def delete_client(self):
        """Deletes the client that is currently selected in the client_list_widget. This func
        will close the appropriate socket, join the appropriate thread (with timeout since
        join() is a blocking call), and then it will delete the appropriate countdown label."""

        # check for if a client has been selected or not.
        if self.client_list_widget.currentItem() is None:
            msg_box = QMessageBox(QMessageBox.Information, "Error", "You must select a client to delete.")
            msg_box.exec()
        else:
            client_idx = self.get_client_idx(self.client_list_widget.item(self.client_list_widget.currentRow()).text())
            self.update_status("Deleting %s..." % self.client_list_widget.item(client_idx).text())
            client_to_be_deleted = self.client_list_widget.takeItem(self.client_list_widget.currentRow())
            try:
                # we delete the socket, thread, and the label.
                sock_to_be_deleted = self.list_of_all_sockets.pop(client_idx)
                sock_to_be_deleted.close()
                thread_to_be_closed: threading.Thread = self.list_of_all_threads.pop(client_idx)
                # thread is deleted with timeout.
                thread_to_be_closed.join(0.3)
                countdown_label_to_be_deleted = self.list_of_all_countdown_labels.pop(client_idx)
                del countdown_label_to_be_deleted
                self.client_list_widget.setCurrentItem(self.client_list_widget.item(0))
                # self.update_selected_client_idx()
                self.show_selected_client_countdown()
            except ValueError:
                pass
            del client_to_be_deleted

    def create_socket_with_thread(self, client_name, client_widget_item, client_idx):
        """This function will create a socket, and a thread, attaching both to the
        client_name, via the arrays that keep track of everything. The thread that is
        started is a daemon, as I would want it to end with the program (harder to do
        with 'while True' loops, and no daemon thread)."""

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        t = threading.Thread(target=self.add_client_socket, args=(sock, client_name, client_widget_item, client_idx))
        t.daemon = True
        self.list_of_all_sockets.append(sock)
        self.list_of_all_threads.append(t)
        t.start()

    def add_client_socket(self, sock: socket.socket, client_name: str, client_widget_item: ClientWidgetItem,
                          client_idx):
        """This function will handle the majority of client communication with the server.

        It will first connect and send the client_name to the server, then await response.
         the client_add_msg is the response, and can be one of the following:
         *Client already exists.
         *Client added.
         *Too many clients. Client dropped.
         If the client was denied, then add_client_socket_denied() will be called.
         Otherwise, the client will enter a 'while True' loop in which it will keep listening
         for a message from the server which will contain the countdown_time.
         Then it will enter a loop to iterate through the decrements of countdown_time."""

        countdown_time = 0
        sock.connect((HOST, PORT_NUMBER))
        sock.send(bytes(client_name, "utf-8"))
        client_added_msg = sock.recv(1024).decode("utf-8")
        # we check to see if we have received anything at all.
        if client_added_msg:
            self.update_status(client_added_msg)
            if client_added_msg == f"SERVER: Too many clients. {client_name} dropped.":
                self.add_client_socket_denied(sock, client_name, client_widget_item, client_idx)
                return
            if client_added_msg == f"SERVER: Client {client_name} already exists.":
                self.add_client_socket_denied(sock, client_name, client_widget_item, client_idx)
                return
            else:
                # here we have a while loop that handles the countdown, and waits for it.
                while True:
                    countdown_time = int(sock.recv(1024).decode("utf-8"))
                    countdown_copy = countdown_time
                    self.update_status(f"{client_name} has recieved {countdown_time}.")
                    print("list index is client idx %d" % client_idx)
                    # we update the countdown label to match the value of countdown time.
                    self.list_of_all_countdown_labels[client_idx].setText(str(countdown_time))
                    # client_widget_item.associated_countdown_label.setText(str(countdown_time))
                    while countdown_time >= 0:
                        # first we check to see if it is 0 or not. If it is, we send finish message.
                        if int(self.list_of_all_countdown_labels[client_idx].text()) == 0:
                            sock.send(bytes(f"CLIENT: {client_name} finished", "utf-8"))
                            break
                        # sleep for 1 sec. This is like pseudo-pause for python thread.
                        time.sleep(1)
                        self.update_client_countdown_value(client_idx)
                        countdown_time = countdown_time - 1

    def add_client_socket_denied(self, sock: socket.socket, client_name: str, client_widget_item: ClientWidgetItem,
                                 client_idx):
        """This function will handle if a client has been denied a socket connection from
        the server. It is practically the same as deleting a client, however, a client does
        not have to be selected from the client_list_widget."""

        self.update_status(f"Removing {client_name} from list...")
        item_to_be_deleted = self.client_list_widget.takeItem(self.client_list_widget.count() - 1)
        self.update_status("Closing %s's socket..." % client_name)
        # update the socket, and the current thread.
        self.list_of_all_sockets.remove(sock)
        # thread is a daemon, it will close with the application process, or when the target func has returned.
        self.list_of_all_threads.remove(threading.current_thread())
        self.list_of_all_countdown_labels.pop(client_idx)
        sock.close()

    def get_client_idx(self, client_name: str) -> int:
        """:returns the index of a client in the self.client_list_widget.
        This index corresponds across all arrays."""

        for i in range(0, self.client_list_widget.count()):
            item = self.client_list_widget.item(i)
            if item.text() == client_name:
                return i

    def update_selected_client_idx(self):
        """Updates the self.selected_client_idx based on which client is selected in the
        self.client_list_widget."""

        for i in range(0, self.client_list_widget.count()):
            item = self.client_list_widget.item(i)
            if item.isSelected():
                self.selected_client_idx = i
                break

    def show_selected_client_countdown(self):
        """Displays the correct countdown label based on which client is selected in the
        self.client_list_widget. Hides all other labels."""

        self.update_selected_client_idx()
        if len(self.list_of_all_countdown_labels) == 0:
            return
        if (self.client_list_widget.count() == 0) and (len(self.list_of_all_countdown_labels) > 0):
            for i, label in enumerate(self.list_of_all_countdown_labels):
                label.hide()
        else:
            for i, label in enumerate(self.list_of_all_countdown_labels):
                if i == self.selected_client_idx:
                    label.show()
                else:
                    label.hide()

    def update_client_countdown_value(self, client_idx):
        """Updates the countdown label value for a certain client."""

        current_text = int(self.list_of_all_countdown_labels[client_idx].text())
        if current_text >= 1:
            current_text = str(current_text - 1)
            self.list_of_all_countdown_labels[client_idx].setText(current_text)

    def stop_countdown_of_selected_client(self):
        """Helper function to stop the countdown of a selected client. Does this by
        setting the countdown value to 0. The while loop that the thread runs will check
        for this condition every time, and will send a message everytime a countdown
        has terminated."""

        self.update_selected_client_idx()
        client_list_item = self.client_list_widget.item(self.selected_client_idx)
        current_countdown_value = int(self.list_of_all_countdown_labels[self.selected_client_idx].text())
        if current_countdown_value > 0:
            self.list_of_all_countdown_labels[self.selected_client_idx].setText("0")

    def update_status(self, msg):
        """Updates the status by adding a line to the status box. It will also keep scrolling
        to the bottom each time it updates."""

        self.status_box.append(msg)
        # reference: https://stackoverflow.com/questions/7778726/autoscroll-pyqt-qtextwidget
        self.status_box.moveCursor(QtGui.QTextCursor.End)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        # reference: https://www.qtcentre.org/threads/26554-how-to-catch-close-event-in-this-program-pyqt
        self.exit_app()

    def exit_app(self):
        """Closes all sockets before terminating the application. The threads need not be
        terminated/joined since they are all daemon threads."""

        for sock in self.list_of_all_sockets:
            sock.close()
        sys.exit(0)


def main():
    app = QApplication(sys.argv)
    screen_size = app.primaryScreen().size()
    GUI = ClientApp(screen_size.width(), screen_size.height())
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
