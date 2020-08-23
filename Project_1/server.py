"""HANNAN KHAN
1001815455"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

""" This is the (GUI) server-side of a server/client application in which the client can
create MAX_CLIENTS number of sub-clients. Each client will have its own socket,
running on its own thread. The server will then give a countdown timer to a randomly
selected client, which the client will then use to countdown (displayed in client's GUI)."""

__author__ = "Hannan Khan"
__credits__ = ["Hannan Khan"]
__version__ = "1.0"
__maintainer__ = "Hannan Khan"
__email__ = "hannan.khan@mavs.uta.edu"

import sys, socket, threading, time, random
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow

MAX_CLIENTS = 3
PORT_NUMBER = 55556
HOST = socket.gethostname()


class ServerApp(QMainWindow):
    def __init__(self, screen_width: int, screen_height: int):
        super(ServerApp, self).__init__()
        self.WIDTH = 1000
        self.HEIGHT = 563
        self.SCREEN_WIDTH = screen_width
        self.SCREEN_HEIGHT = screen_height
        self.X = int((self.SCREEN_WIDTH / 2) - (self.WIDTH / 2))
        self.Y = int(self.SCREEN_HEIGHT / 10)
        self.setGeometry(self.X, self.Y, self.WIDTH, self.HEIGHT)
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setWindowTitle("Server")

        self.current_font = QtGui.QFont("Consolas", 10)

        self.main_frame = QtWidgets.QFrame()
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.main_inter_layout = QtWidgets.QVBoxLayout()
        self.main_inter_layout.setSpacing(0)
        self.main_inter_layout.setContentsMargins(0, 0, 0, 0)

        self.list_of_all_clients = []
        self.list_of_all_client_sockets = []
        self.list_of_all_threads: [threading.Thread] = []

        self._init_menu()
        self._init_top_layout()
        self._init_middle_layout()
        self._init_bottom_layout()
        self.main_layout.addLayout(self.main_inter_layout)
        self.main_frame.setLayout(self.main_layout)
        self.setCentralWidget(self.main_frame)

        self._init_socket()
        self.listening_bool = True
        self._start_listening_thread()
        self._start_countdowns_thread()

        self.show()

    def _init_menu(self):
        """Creates the menu and the actions/shortcuts associated with each option."""

        self.top_menu_bar = QtWidgets.QMenuBar()
        self.file_menu = self.top_menu_bar.addMenu("&File")

        self.exit_action = QtWidgets.QAction("&Exit", self)
        self.exit_action.setShortcut(QtGui.QKeySequence(Qt.CTRL + Qt.Key_Q))
        self.exit_action.triggered.connect(self.exit_app)

        self.file_menu.addAction(self.exit_action)

        self.main_layout.setMenuBar(self.top_menu_bar)

    def _init_top_layout(self):
        """Sets up the top half of the GUI."""

        self.top_layout = QtWidgets.QHBoxLayout()
        self.top_layout.setSpacing(15)

        self.current_clients_label = QtWidgets.QLabel()
        self.current_clients_label.setText("Current Clients\t\t")
        self.current_clients_label.setFont(self.current_font)

        self.client_status_label = QtWidgets.QLabel()
        self.client_status_label.setText("Client Status")
        self.client_status_label.setFont(self.current_font)

        self.top_layout.addWidget(self.current_clients_label)
        self.top_layout.addWidget(self.client_status_label)

        self.main_inter_layout.addLayout(self.top_layout)

    def _init_middle_layout(self):
        """Sets up the middle of the GUI."""

        self.middle_layout = QtWidgets.QHBoxLayout()
        self.middle_layout.setSpacing(10)

        self.client_list_widget = QtWidgets.QListWidget()
        self.client_list_widget.setFont(self.current_font)

        self.client_status_widget = QtWidgets.QListWidget()
        self.client_status_widget.setFont(self.current_font)

        self.middle_layout.addWidget(self.client_list_widget)
        self.middle_layout.addWidget(self.client_status_widget)

        self.main_inter_layout.addLayout(self.middle_layout)

    def _init_bottom_layout(self):
        """Sets up the bottom of the GUI."""

        self.bottom_layout = QtWidgets.QVBoxLayout()
        self.bottom_layout.setSpacing(10)

        self.status_label = QtWidgets.QLabel()
        self.status_label.setText("Status")
        self.status_label.setFont(self.current_font)

        self.status_box_widget = QtWidgets.QTextEdit()
        self.status_box_widget.setReadOnly(True)
        self.status_box_widget.setFont(self.current_font)

        self.bottom_layout.addWidget(self.status_label)
        self.bottom_layout.addWidget(self.status_box_widget)

        self.main_inter_layout.addLayout(self.bottom_layout)

    def _init_socket(self):
        """Creates a socket to which all clients will bind to."""

        self.update_status("Socket is being created...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((HOST, PORT_NUMBER))
        self.sock.listen(MAX_CLIENTS)
        self.update_status("Socket created.")

    def _start_listening_thread(self):
        """Starts a thread, separate from the MainThread, which will constantly run,
        and be willing to accept connections. Any connections excess of MAX_CLIENTS
        will be dealt with AFTER connecting."""

        # inspiration: https://www.reddit.com/r/learnpython/comments/39bg6m/quick_threading_question_my_program_has_an/
        self.listening_thread = threading.Thread(target=self._start_listening)
        self.listening_thread.daemon = True
        self.listening_thread.start()
        self.list_of_all_threads.append(self.listening_thread)

    def _start_listening(self):
        """This loop will constantly listen for new connections to this socket. Some
        problems it handles are:
        *If MAX_CLIENTS already exist on the socket.
        *If the client_name already exists on the server.
        *If the client is permitted to join and here is where this function will manage
        the client by calling self.manage_client()."""

        self.update_status("Starting to listen now...")
        self.update_status("Thread: %s Started." % threading.current_thread())
        # reference: https://stackoverflow.com/questions/10810249/python-socket-multiple-clients
        while True:
            # we wait for and accept a connection.
            client_socket, address = self.sock.accept()
            self.update_status("%s has established connection." % address[1])
            # we recieve the client name from client.
            client_name = client_socket.recv(1024).decode("utf-8")
            # we check to see if there are too many clients.
            if len(self.list_of_all_clients) < MAX_CLIENTS:
                # we check to see if the client name already exists in the current clients.
                if client_name in self.list_of_all_clients:
                    # we close the connection if the name already exists.
                    client_added_msg = f"SERVER: Client {client_name} already exists."
                    client_socket.send(bytes(client_added_msg, "utf-8"))
                    client_socket.close()
                else:
                    # now we will set a thread to manage this socket, and its countdowns.
                    self.manage_client(client_socket, address, client_name)
            else:
                # here we reject connection if there are too many clients. And update
                # the client that we have rejected it.
                client_added_msg = f"SERVER: Too many clients. {client_name} dropped."
                self.update_status(f"Too many clients. {client_name} has been removed.")
                client_socket.send(bytes(client_added_msg, "utf-8"))
                client_socket.close()

    def update_status(self, msg):
        """Updates the status by adding a line to the status box. It will also keep scrolling
        to the bottom each time it updates."""

        self.status_box_widget.append(msg)
        # reference: https://stackoverflow.com/questions/7778726/autoscroll-pyqt-qtextwidget
        self.status_box_widget.moveCursor(QtGui.QTextCursor.End)

    def manage_client(self, client_socket, address, client_name):
        """This function will take a client as an input, and will update the client list,
        update the status, update all arrays to reflect the new client joining, update
        the client_status_widget with 'Connected', and FINALLY it will send an update
        to the client saying that the client was accepted."""

        # creates an item for the client list widget.
        list_item = QtWidgets.QListWidgetItem()
        list_item.setText(client_name)
        self.client_list_widget.addItem(list_item)
        self.update_status(f"{address[1]} added under {client_name}.")
        # we update all lists with this clients info.
        self.list_of_all_client_sockets.append(client_socket)
        self.list_of_all_clients.append(client_name)
        # we update the client status box with this clients info.
        list_item1 = QtWidgets.QListWidgetItem()
        list_item1.setText("Connected")
        self.client_status_widget.addItem(list_item1)
        # we message the client side to say that the client has been added.
        client_added_msg = f"SERVER: Client {client_name} added."
        client_socket.send(bytes(client_added_msg, "utf-8"))

    def _start_countdowns_thread(self):
        """This func will start the countdowns_thread which will constantly (every 10
        seconds) keep sending a countdown timer to a random client."""

        self.countdowns_thread = threading.Thread(target=self._countdowns_thread_func)
        self.countdowns_thread.daemon = True
        self.countdowns_thread.start()

    def _countdowns_thread_func(self):
        """This function is the main meat of the program. It will keep sending, every
        10 seconds, a countdown timer to a randomly selected client. It will then wait
        for the clients reply (to say that it has finished). This is so that the client can
        abruptly close the countdown, and say that they are finished. The latter part
        of this function is written to handle some WinErrors I kept getting when I was
        deleting clients via the client GUI."""

        # random_client_idx stays an int, while random_num does not (gets made into a string).
        random_client_idx = 0
        random_num = 0
        self.update_status("Countdown thread starting...")
        self.update_status("Current thread started is %s" % threading.current_thread())
        while True:
            # checks to see if there are any clients currently.
            if len(self.list_of_all_clients) > 0:
                # sleeps for the remaining of the 10 seconds.
                time_to_sleep = 10 - int(random_num)
                time.sleep(time_to_sleep)
                # sets the previous clients status to connected.
                self.client_status_widget.item(random_client_idx).setText("Connected")
                # chooses a random client index.
                random_client_idx = random.randrange(0, len(self.list_of_all_clients))
                # updates that clients status to reflect counting down.
                self.client_status_widget.item(random_client_idx).setText("Counting Down...")
                # chooses a random countdown value.
                random_num = str(random.randrange(2, 9))
                # here we get the client socket and name from the lists.
                client_socket = self.list_of_all_client_sockets[random_client_idx]
                client_name = self.list_of_all_clients[random_client_idx]
                try:
                    # we try to send the countdown value and wait for the message.
                    client_socket.send(bytes(random_num, "utf-8"))
                    self.update_status("Sent %s to client %s" % (random_num, client_name))
                    recv_msg = client_socket.recv(1024).decode("utf-8")
                    self.update_status(recv_msg)
                except OSError:
                    # here we will notice if a client has been deleted.
                    self.update_status(f"{client_name}'s connection was closed by client.")
                    self.list_of_all_clients.pop(random_client_idx)
                    # socket for that client will be closed.
                    socket_to_del = self.list_of_all_client_sockets.pop(random_client_idx)
                    socket_to_del.close()
                    # client will be removed from the client list widget.
                    self.client_list_widget.takeItem(random_client_idx)
                    self.client_status_widget.takeItem(random_client_idx)
            else:
                pass

    def get_client_name_idx(self, client_name) -> int:
        """:returns the index of a client in the self.list_of_all_clients.
        This index corresponds across all arrays."""

        for i, name in enumerate(self.list_of_all_clients):
            if client_name == name:
                return i

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        # reference: https://www.qtcentre.org/threads/26554-how-to-catch-close-event-in-this-program-pyqt
        self.exit_app()

    def exit_app(self):
        """At exit, I close all sockets, including the main socket. The threads need not
        be closed as they are all daemon threads, which will terminate with the
        MainThread."""

        print(self.list_of_all_threads)
        for client_socket in self.list_of_all_client_sockets:
            client_socket.close()
        self.sock.close()
        sys.exit(0)


def main():
    app = QApplication(sys.argv)
    screen_size = app.primaryScreen().size()
    GUI = ServerApp(screen_size.width(), screen_size.height())
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
