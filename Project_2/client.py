"""HANNAN KHAN
1001815455"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

""" This is the (GUI) client-side of a server/client application in which the client can create
a number of sub-clients. Each client will have its own socket, and multithreading is used
to allow clients to send/receive messages from the server simultaneously. A thread
is created whenever a client wishes to upload or check for messages. Maintenance of
the queues is done completely on the server side."""

__author__ = "Hannan Khan"
__credits__ = ["Hannan Khan"]
__version__ = "1.0"
__maintainer__ = "Hannan Khan"
__email__ = "hannan.khan@mavs.uta.edu"

import socket
import sys
import threading

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, QMessageBox

import utils
from utils import UploadCheckDialog


HOST = socket.gethostname()
PORT = 55557


class ClientApp(QMainWindow):
    def __init__(self, screen_width, screen_height):
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

        self.current_font = QtGui.QFont("Consolas", 10)
        # tracks currently selected client.
        self.selected_client_idx = -1
        # stores all sockets
        self.all_sockets: [socket.socket] = []
        # stores all threads
        self.all_threads: [threading.Thread] = []
        # stores all possible queues.
        self.all_queues = ["A", "B", "C"]

        self._init_menu()
        self._init_top_layout()
        self._init_middle_layout()
        self._init_bottom_layout()

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
        self.top_layout.setSpacing(10)

        self.client_label = QtWidgets.QLabel()
        self.client_label.setText("Clients")
        self.client_label.setFont(self.current_font)

        self.add_client_button = QtWidgets.QPushButton()
        self.add_client_button.setFont(self.current_font)
        self.add_client_button.setText("Add")
        self.add_client_button.clicked.connect(self.add_new_client)

        self.delete_client_button = QtWidgets.QPushButton()
        self.delete_client_button.setFont(self.current_font)
        self.delete_client_button.setText("Delete Selected")
        self.delete_client_button.clicked.connect(self.delete_client)

        self.upload_message_btn = QtWidgets.QPushButton()
        self.upload_message_btn.setFont(self.current_font)
        self.upload_message_btn.setText("Upload Message")
        self.upload_message_btn.clicked.connect(self.upload_handler)

        self.check_messages_btn = QtWidgets.QPushButton()
        self.check_messages_btn.setFont(self.current_font)
        self.check_messages_btn.setText("Check Messages")
        self.check_messages_btn.clicked.connect(self.check_handler)

        self.top_layout.addWidget(self.client_label)
        self.top_layout.addWidget(self.add_client_button)
        self.top_layout.addWidget(self.delete_client_button)
        self.top_layout.addWidget(self.upload_message_btn)
        self.top_layout.addWidget(self.check_messages_btn)

        self.main_inter_layout.addLayout(self.top_layout)

    def _init_middle_layout(self):
        """Sets up the middle of the GUI."""

        self.middle_layout = QtWidgets.QHBoxLayout()
        self.middle_layout.setSpacing(10)

        self.client_list_widget = QtWidgets.QListWidget()
        self.client_list_widget.setFont(self.current_font)
        # self.client_list_widget.setFixedSize(540, 220)

        self.middle_layout.addWidget(self.client_list_widget)

        self.main_inter_layout.addLayout(self.middle_layout)

    def _init_bottom_layout(self):
        """Sets up the bottom of the GUI."""

        self.status_label = QtWidgets.QLabel()
        self.status_label.setFont(self.current_font)
        self.status_label.setText("Status Box")
        self.main_inter_layout.addWidget(self.status_label)
        self.status_box = QtWidgets.QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setFont(self.current_font)
        self.main_inter_layout.addWidget(self.status_box)

    def add_new_client(self):
        """This function adds a new client to the list, and gives user option of connecting
        to either upload, or check for messages."""

        boo = True
        client_name = ""
        qstn_box = QInputDialog(self, Qt.WindowSystemMenuHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        client_name, boo = qstn_box.getText(self, "Add New Client", "Insert New Client Name:")
        while boo and not client_name:
            client_name, boo = qstn_box.getText(self, "Add New Client", "Insert New Client Name.\nClient name cannot "
                                                                        "be empty.")

        if boo and client_name:
            # we add the client to the list of clients to display
            new_client_widget_item = QtWidgets.QListWidgetItem()
            new_client_widget_item.setFont(self.current_font)
            new_client_widget_item.setText(client_name)
            self.client_list_widget.addItem(new_client_widget_item)
            self.client_list_widget.setCurrentItem(self.client_list_widget.item(self.client_list_widget.count() - 1))
            self.update_selected_client_idx()
            client_idx = utils.get_client_idx(self, client_name)
            client_sock = self.create_client_socket(client_name, new_client_widget_item, client_idx)
            # check for if the user wants to upload or check for new messages.
            self.ask_user_upload_check(client_name, client_sock, client_idx)

    def ask_user_upload_check(self, client_name, client_sock, client_idx):
        """Asks the newly created client if they want to upload a message, or check a
        queue for messages.
        Uses custom UploadCheckDialog (located in utils.py)."""

        qstn_box = UploadCheckDialog(self.current_font, client_name, client_idx)
        qstn_box.exec_()
        if qstn_box.selection == -1:
            # close button selected.
            pass
        elif qstn_box.selection == 0:
            # Here we carry out the upload option.
            self.upload_handler(client_name, client_sock, client_idx)
        elif qstn_box.selection == 1:
            # Here we carry out the Check for messages option.
            self.check_handler(client_name, client_sock, client_idx)

    def create_client_socket(self, client_name, new_client_widget_item, client_idx) -> socket.socket:
        """Creates the sockets for each client, and then sends the client name to the server.
        If the client is added, It will return the client socket back to add_new_client().
        Otherwise, if the server is not running, the client socket is closed and the client
        is deleted."""

        client_added_msg = ""

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.all_sockets.append(sock)

        try:
            sock.connect((HOST, PORT))
            sock.send(bytes(client_name, "utf-8"))
            client_added_msg = sock.recv(1024).decode("utf-8")
        except Exception as e:
            # handles for if the server is NOT running currently.
            self.update_status(e.__str__())
            self.update_status(f"The socket for {client_name} could not connect.")
            self.update_status(f"Deleting {client_name}.")
            self.delete_client(client_name, client_idx, sock)

        if client_added_msg == f"SERVER: {client_name} added.":
            # handle the addition of a client here.
            self.update_status(client_added_msg)
            return sock

    def update_selected_client_idx(self):
        """Updates the self.selected_client_idx based on which client is selected in the
        self.client_list_widget."""

        if self.client_list_widget.count() == 0:
            self.selected_client_idx = -1
            return

        for i in range(0, self.client_list_widget.count()):
            item = self.client_list_widget.item(i)
            if item.isSelected():
                self.selected_client_idx = i
                break

    def delete_client(self, client_name: str = "", client_idx: int = -1, sock: socket.socket = None):
        """Deletes a client. If a client has been given in parameters, then it will delete
        that client. Otherwise, it will delete the client that is currently selected in the
        client list widget."""

        if (not client_name) and (client_idx == -1) and (not sock) and (self.client_list_widget.currentItem() is None):
            # handles for no clients existing.
            msg_box = QMessageBox(QMessageBox.Information, "Error", "You must select a client to delete.")
            msg_box.exec_()
            return
        elif (not client_name) and (client_idx == -1) and (not sock):
            # Here we handle if a user has clicked the delete button.
            # we handle by getting operating on the currently selected client in the client list
            client_widget_to_delete = self.client_list_widget.item(self.client_list_widget.currentRow())
            client_name = client_widget_to_delete.text()
            client_idx = utils.get_client_idx(self, client_name)
            sock = self.all_sockets[client_idx]

        # here the client will be sending the 'END CONNECTION' message to the server.
        sock.send(bytes("END CONNECTION", "utf-8"))
        self.update_status(f"Closing and removing {client_name}'s socket...")
        sock.close()
        self.all_sockets.remove(sock)
        self.update_status(f"Removing {client_name} from list.")
        self.client_list_widget.takeItem(client_idx)
        self.update_status(f"Deleted client: {client_name}.")
        self.update_selected_client_idx()

    def upload_handler(self, client_name: str = "", client_sock: socket.socket = None,
                       client_idx: int = -1):
        """Creates a thread to handle upload a message via a client.
        Asks user for meters and which queue to upload to...
        Starts a thread to upload from that particular client."""

        if (not client_name) and (not client_sock) and (client_idx == -1):
            # Here we handle if a user has clicked the button.
            # we handle by getting operating on the currently selected client in the client list
            if self.client_list_widget.currentItem() is None:
                msg_box = QMessageBox(QMessageBox.Information, "Error",
                                      "You must select a client to be able to upload.")
                msg_box.exec_()
                return
            new_client_widget = self.client_list_widget.currentItem()
            client_name = new_client_widget.text()
            client_idx = utils.get_client_idx(self, client_name)
            client_sock = self.all_sockets[client_idx]

        # We get the METERS input from the user:
        num, boo = QInputDialog.getDouble(self, "User Input", "Enter Meters:")
        if boo:
            boo = False
            # Now we get the queue to upload to...
            q, boo = QInputDialog.getItem(self, "Select Queue",
                                          f"{client_name}:\nWhich queue would you like to upload to?",
                                          self.all_queues, 0, False)
            if boo:
                # we handle by creating a thread to operate via the clients socket (should have already been created).
                t = threading.Thread(name=client_name, target=self.upload, args=(client_name,
                                                                                 client_sock, num, q), daemon=True)
                t.start()

    def upload(self, client_name: str = "", client_sock: socket.socket = None, meters: float = 0.0, q: str = ""):
        """Uploads the meters and queue to the server, where the message broker will
        take care of conversion and storage into the correct queue.
        Each thread that runs this function will terminate after this function is complete."""

        server_msg = ""

        # we prep the server for upload with this message.
        client_sock.send(bytes("UPLOAD", "utf-8"))

        # keep sending until server responds with 'METERS RECEIVED'
        while server_msg != "METERS RECEIVED":
            # Now we send the meters input...
            client_sock.send(bytes(str(meters), "utf-8"))
            # We wait for ACK message
            server_msg = client_sock.recv(1024).decode("utf-8")

        # Now we send the queue to upload to...
        while server_msg != "QUEUE RECEIVED":
            client_sock.send(bytes(q, "utf-8"))
            server_msg = client_sock.recv(1024).decode("utf-8")

        # Now we wait for conformation from the Message Broker saying that the input
        # has been converted and uploaded to the right queue.
        server_msg = client_sock.recv(1024).decode("utf-8")
        if server_msg == f"SERVER: {client_name} has uploaded {meters} to Queue {q}.":
            self.update_status(server_msg)
        elif server_msg == f"SERVER: Error - {client_name} could not upload to Queue {q}":
            self.update_status(server_msg)
            self.update_status("Upload failed. Please try again.")

    def check_handler(self, client_name: str = "", client_sock: socket.socket = None,
                      client_idx: int = -1):
        """Asks the user which queue to check and creates a thread to handle the checking
        of messages via a client."""

        if (not client_name) and (not client_sock) and (client_idx == -1):
            # Here we handle if a user has clicked the button.
            if self.client_list_widget.currentItem() is None:
                msg_box = QMessageBox(QMessageBox.Information, "Error", "You must select a client to be able to check.")
                msg_box.exec_()
                return
            # we handle by getting operating on the currently selected client in the client list
            new_client_widget = self.client_list_widget.currentItem()
            client_name = new_client_widget.text()
            client_idx = utils.get_client_idx(self, client_name)
            client_sock = self.all_sockets[client_idx]

        boo = False
        q = ""

        # Now we get which queue the user to check...
        q, boo = QInputDialog.getItem(self, "Select Queue", f"{client_name}:\nWhich queue would you like to check?",
                                      self.all_queues, 0, False)

        if boo and q:
            # we handle by creating a thread to operate via the clients socket (has already been created).
            t = threading.Thread(name=client_name, target=self.check, args=(client_name,
                                                                            client_sock, q), daemon=True)
            t.start()

    def check(self, client_name, client_sock, q):
        """Preps the server for a check operation.
        Sends the queue selection (already done in check_handler()).
        Receives conformation of whether messages exist in that queue.
        If messages, downloads and stores in temporary var messages, displays to user.
        if no messages, informs user and terminates the thread."""

        messages = []

        server_msg = ""

        # we will prep the server for a check operation.
        client_sock.send(bytes("CHECK", "utf-8"))

        while server_msg != "QUEUE SELECTION RECEIVED":
            client_sock.send(bytes(q, "utf-8"))
            server_msg = client_sock.recv(1024).decode("utf-8")

        # now we seek conformation that there exists messages for us to receive.
        server_msg = client_sock.recv(1024).decode("utf-8")

        if server_msg == f"SERVER: Messages available in Queue {q}.":
            # tell server we are ready for the download.
            client_sock.send(bytes("READY", "utf-8"))
            # download the messages here.
            while server_msg != "ALL MESSAGES SENT.":
                server_msg = client_sock.recv(1024).decode("utf-8")
                if server_msg != "ALL MESSAGES SENT.":
                    messages.append(server_msg)
            self.update_status(f"\nMESSAGE RECEIVED FROM QUEUE {q}:::::::::::::")
            # display messages to user via GUI.
            for message in messages:
                self.update_status(message.strip())
            self.update_status("END MESSAGE::::::::::::::::::::\n")
        elif server_msg == f"SERVER: NO MESSAGES IN QUEUE {q}.":
            # Handle here. terminate the thread by returning.
            self.update_status(server_msg)
            return

    def update_status(self, status_message):
        """Updates the status by adding a line to the status box. It will also keep scrolling
        to the bottom each time it updates."""

        self.status_box.append(status_message)
        # reference: https://stackoverflow.com/questions/7778726/autoscroll-pyqt-qtextwidget
        self.status_box.moveCursor(QtGui.QTextCursor.End)
        self.update()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.exit_app()

    def exit_app(self):
        """Closes all sockets and exits the app. Threads are all set to Daemon, they need
        not be joined() before exiting."""

        for sock in self.all_sockets:
            sock.close()

        # no need to handle the threads as they are all set to daemon.
        sys.exit(0)


def main():
    app = QApplication(sys.argv)
    screen_size = app.primaryScreen().size()
    GUI = ClientApp(screen_size.width(), screen_size.height())
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
