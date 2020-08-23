"""HANNAN KHAN
1001815455"""

# !/usr/bin/env python
# -*- coding: utf-8 -*-

""" This is the (GUI) server-side of a server/client application in which the client can
create a number of sub-clients. Each client will have its own socket, running on its own
thread. The server will then listen infinitely to each client, allowing them to upload messages,
check for messages, or end the connection.

The message-broker portion of the server is integrated within this class. The message
broker takes care of maintaining/updating the queue storage file, updating the queue,
and adding messages to the correct output queue.

The functions that could be considered as part of the message broker are:
    _init_repository_dict()
    _init_all_queues()
    add_to_queue()
    update_all_queues_file()"""

__author__ = "Hannan Khan"
__credits__ = ["Hannan Khan"]
__version__ = "1.0"
__maintainer__ = "Hannan Khan"
__email__ = "hannan.khan@mavs.uta.edu"

import pickle
import queue
import socket
import sys
import threading
import time

from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow

import utils

HOST = socket.gethostname()
PORT = 55557
MAX_CLIENTS = 3


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

        # stores the conversion rules of each unit.
        self.repository_dict = {}
        # stores the units for queue a
        self.a_units = []
        # stores the units for queue b
        self.b_units = []
        # stores the units for queue c
        self.c_units = []
        self.current_font = QtGui.QFont("Consolas", 10)
        # stores all client names
        self.all_clients: [str] = []
        # stores all client sockets.
        self.all_client_sockets: [socket.socket] = []
        # stores all threads
        self.all_threads = []
        # keeps track of all active threads. Gets updated based on all_threads.
        self.active_threads = []

        self.main_frame = QtWidgets.QFrame()
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.main_inter_layout = QtWidgets.QVBoxLayout()
        self.main_inter_layout.setSpacing(0)
        self.main_inter_layout.setContentsMargins(0, 0, 0, 0)

        self._init_menu()
        self._init_top_layout()
        self._init_middle_layout()
        self._init_bottom_layout()
        self.main_layout.addLayout(self.main_inter_layout)
        self.main_frame.setLayout(self.main_layout)
        self.setCentralWidget(self.main_frame)

        self._init_repository_dict()
        self._init_all_queues()
        self._init_socket()
        self._start_listening_thread()

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
        self.client_list_widget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.client_list_widget.setFont(self.current_font)

        self.client_status_widget = QtWidgets.QListWidget()
        self.client_status_widget.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
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

    def _init_repository_dict(self):
        """Opens the repository text file, and loads the conversion rules into memory.
        Assumes that the file already exists, so the application can run.
        The first 3 lines of the repository contain the units of each queue.
        The rest of the lines contain a unit and its conversion rules.
        This way, the repository can be modified and still run."""

        try:
            with open("repository.txt", "r") as file:
                self.a_units.extend(file.readline().strip().split())
                self.b_units.extend(file.readline().strip().split())
                self.c_units.extend(file.readline().strip().split())

                for line in file.readlines():
                    segments = line.split(" ")
                    unit, conversion_rule = (segments[0], segments[1].strip())
                    self.repository_dict[unit] = conversion_rule
        except FileNotFoundError as e:
            print(e)
            print("No repository file found.\nApplication cannot run without a repository file.")
            sys.exit(1)

    def _init_all_queues(self):
        """Initializes all the queues, and loads the serialized versions into volatile memory.
        Will create a queue storage file if none exists."""

        self.a_queue = queue.Queue()
        self.b_queue = queue.Queue()
        self.c_queue = queue.Queue()

        try:
            try:
                # reference: https://stackoverflow.com/questions/6568007/how-do-i-save-and-restore-multiple-variables-in-python
                all_queues = pickle.load(open("all_queues.p", "rb"))
                # we put all of the lists' items into our volatile memory queues.
                for i, each_queue in enumerate(all_queues):
                    for item in each_queue:
                        if i == 0:
                            self.a_queue.put(item)
                        elif i == 1:
                            self.b_queue.put(item)
                        elif i == 2:
                            self.c_queue.put(item)
                self.update_status("Queues loaded into volatile memory.")
            except EOFError:
                self.update_status("EOF ERROR: The queue storage is currently empty.")
        except FileNotFoundError:
            # we create the file here if it does not exist.
            # keep in mind all queues are already initialized to null, no need to fill them.
            self.update_status("No queue storage file exists. Creating one...")
            file = open("all_queues.p", "wb")
            file.close()

    def _init_socket(self):
        """Creates the socket to which all clients will bind to."""

        self.update_status("Socket is being created...")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((HOST, PORT))
        self.sock.listen(MAX_CLIENTS)
        self.update_status("Socket created, now listening.")

    def _start_listening_thread(self):
        """Starts the thread used for listening for incoming clients."""

        self.listening_thread = threading.Thread(target=self._start_listening)
        self.listening_thread.setDaemon(True)
        self.listening_thread.setName("listening_thread")
        self.listening_thread.start()
        self.all_threads.append(self.listening_thread)

    def _start_listening(self):
        """Listens for incoming clients in infinite loop."""

        self.update_status("Starting listening...")
        self.update_status("Thread Started: %s" % threading.current_thread())

        while True:
            # make sure we have an up-to-date active threads list before accepting new client.
            self.update_active_threads_list()
            client_socket, address = self.sock.accept()
            self.update_status("%s has established connection." % address[1])
            client_name = client_socket.recv(1024).decode("utf-8")
            # Here is what we do if a client is accepted.
            self.update_status(f"{client_name} accepted.")
            self.new_client_handler(client_socket, address, client_name)

    def add_to_queue(self, meters: float = 0.0, q: str = "") -> str:
        """:returns the results in a string to be shown in our server GUI.

        Converts the meters input into the units specified in the selected q.
        Places the results into the related queue file (non-volatile mem.)."""

        selected_units = []
        selected_queue = None
        all_results = []

        if q == "A":
            selected_units = self.a_units
            selected_queue = self.a_queue
        elif q == "B":
            selected_units = self.b_units
            selected_queue = self.b_queue
        elif q == "C":
            selected_units = self.c_units
            selected_queue = self.c_queue

        for unit in selected_units:
            # Here we convert the meters into the units for the queue.
            result = eval(str(meters) + self.repository_dict[unit])
            # Now we add the result to the selected queue.
            all_results.append(str(result))

        # concatenate all strings to get our results_string.
        results_string = " ".join([st for st in all_results])

        # puts the string into our queue.
        selected_queue.put(results_string)
        # updates our queue storage file to match what is in our volatile memory.
        self.update_all_queues_file()

        return results_string

    def update_all_queues_file(self):
        """Updates the queues storage file with the most up-to-date values.
        The queues are converted into lists then serialized and stored into 'all_queues.p'
        file.
        List conversion is done because queue.Queue() objects cannot be serialized
        as they utilize thread locks."""

        # reference: https://stackoverflow.com/questions/8196254/how-to-iterate-queue-queue-items-in-python
        a_contents = list(self.a_queue.queue)
        b_contents = list(self.b_queue.queue)
        c_contents = list(self.c_queue.queue)

        # reference: https://stackoverflow.com/questions/6568007/how-do-i-save-and-restore-multiple-variables-in-python
        pickle.dump([a_contents, b_contents, c_contents], open("all_queues.p", "wb"))

    def new_client_handler(self, client_socket: socket.socket = None, address: tuple = (), client_name: str = ""):
        """Handles the addition of new clients to the server GUI.
        First - it will add the client to the list of clients.
        Second - It will update the current list of all clients.
        Third - It will update the client status list.
        Fourth - Server will send a client added message to the client as confirmation.
        The infinite loop thread for that client will also get started."""

        list_item = QtWidgets.QListWidgetItem()
        list_item.setFont(self.current_font)
        list_item.setText(client_name)
        self.client_list_widget.addItem(list_item)
        self.update_status(f"{address[1]} added under {client_name}.")

        self.all_clients.append(client_name)
        self.all_client_sockets.append(client_socket)

        status_item = QtWidgets.QListWidgetItem()
        status_item.setFont(self.current_font)
        status_item.setText("Connected")
        self.client_status_widget.addItem(status_item)

        client_added_msg = f"SERVER: {client_name} added."
        client_socket.send(bytes(client_added_msg, "utf-8"))

        # Start the thread that wil listen to this client infinitely.
        self.start_client_thread(client_socket, client_name)

    def start_client_thread(self, client_socket: socket.socket = None, client_name: str = ""):
        """Starts the infinite loop thread for each client. Keeps track of this thread by
        appending it to self.all_threads."""

        t = threading.Thread(name=client_name, target=self.listen_to_client, args=(client_socket, client_name),
                             daemon=True)
        self.all_threads.append(t)
        t.start()

    def listen_to_client(self, client_socket: socket.socket = None, client_name: str = ""):
        """The infinite loop that will run in a separate thread for each client. While running,
        it will check for incoming messages from the client. The message contents will
        determine the action taken by the server. (before each action, the client_idx is updated.)

        UPLOAD:: receives the meters and which queue to upload to (sends conformation
        for each received). Converts the input. Adds converted string to the queue.
        Displays the current conversion on the server GUI (under status).

        CHECK:: receives the queue to check for messages and returns with conformation.
        If queue has no messages, it will let the client know. If there are messages, it
        will let the client know, to which the client will respond 'READY'. Finally it will send
        the messages.

        END CONNECTION:: receives that a client has been deleted via the client GUI.
        To cope, it will first update the status of the client to 'Disconnected' to notify
        the user. It will re-set the client index (in case multiple clients are being deleted
        at once). It will close the socket and remove the client from the GUI. The thread
        is terminated when 'return' is called. The list of active threads is updated in the
        infinite loop that is running on the MainThread."""

        while True:
            # Get message and update client idx.
            msg = client_socket.recv(1024).decode("utf-8").upper()
            client_idx = utils.get_client_idx(self, client_name)

            if msg == "UPLOAD":
                self.update_status(f"{client_name} wants to upload.")
                # Handle here for the upload message, recv the length in meters and the queue to upload from.
                meters = float(client_socket.recv(1024).decode("utf-8"))
                server_msg = "METERS RECEIVED"
                client_socket.send(bytes(server_msg, "utf-8"))

                q = client_socket.recv(1024).decode("utf-8")
                server_msg = "QUEUE RECEIVED"
                client_socket.send(bytes(server_msg, "utf-8"))

                self.update_status("Converting...")

                all_results = self.add_to_queue(meters, q)

                # If all went smoothly, server sends a upload successful message.
                server_msg = f"SERVER: {client_name} has uploaded {meters} to Queue {q}."
                client_socket.send(bytes(server_msg, "utf-8"))
                self.client_status_widget.item(client_idx).setText("Connected")
                self.update_status(f"{client_name} has uploaded {meters} to Queue {q}:")
                self.update_status(all_results)
            elif msg == "CHECK":
                self.client_status_widget.item(client_idx).setText("Checking...")
                # handle here for the check messages portion. Get which queue to check for. See if it is empty.
                q = client_socket.recv(1024).decode("utf-8")
                server_msg = "QUEUE SELECTION RECEIVED"
                client_socket.send(bytes(server_msg, "utf-8"))
                self.update_status(f"{client_name} wants to check for messages in Queue {q}.")

                # check if messages are available in that queue. Send conformation.
                if self.queue_has_messages(q):
                    server_msg = f"SERVER: Messages available in Queue {q}."
                    client_socket.send(bytes(server_msg, "utf-8"))
                    # We wait to see if client can start receiving...
                    client_msg = client_socket.recv(1024).decode("utf-8")
                    if client_msg == "READY":
                        self.client_status_widget.item(client_idx).setText("Downloading...")
                        # start sending the messages.
                        self.send_messages_from_queue(client_socket, q)
                        client_socket.send(bytes("ALL MESSAGES SENT.", "utf-8"))
                        self.client_status_widget.item(client_idx).setText("Connected")
                else:
                    # If empty reply Queue empty. IF not then keep replying with the values of the queue.
                    server_msg = f"SERVER: NO MESSAGES IN QUEUE {q}."
                    client_socket.send(bytes(server_msg, "utf-8"))
                    self.client_status_widget.item(client_idx).setText("Connected")
            elif msg == "END CONNECTION":
                # Delete client from all vars and end loop thereby ending thread.
                self.client_status_widget.item(client_idx).setText("Disconnected")
                self.update()
                self.update_status(f"{client_name} has ended connection.")

                # Gives the GUI time to refresh.
                time.sleep(5)
                # RE-SET the client index, in case multiple users are deleted at once.
                client_idx = utils.get_client_idx(self, client_name)

                self.update_status(f"Closing and removing {client_name}...")
                self.all_client_sockets.remove(client_socket)
                client_socket.close()
                self.client_list_widget.takeItem(client_idx)
                self.client_status_widget.takeItem(client_idx)
                self.all_clients.remove(client_name)

                return

    def queue_has_messages(self, q: str = "") -> int:
        """Checks whether a queue has messages in it. Returns zero or one correspondingly.
        Used in lieu of the queue.empty() function since I am using a FOR-loop iteration,
        and not a while loop iteration, for iterating over items in the queue."""

        selected_queue = None

        if q == "A":
            selected_queue = self.a_queue
        elif q == "B":
            selected_queue = self.b_queue
        elif q == "C":
            selected_queue = self.c_queue

        if selected_queue.qsize() > 0:
            return 1
        return 0

    def send_messages_from_queue(self, client_socket, q):
        """Sends messages from queue q to the client socket.
        This function is operated by the individual client threads."""

        selected_queue = None

        if q == "A":
            selected_queue = self.a_queue
        elif q == "B":
            selected_queue = self.b_queue
        elif q == "C":
            selected_queue = self.c_queue

        for i in range(0, selected_queue.qsize()):
            item_to_send = selected_queue.get()
            client_socket.send(bytes(item_to_send, "utf-8"))

        # update the queue storage file to match what we have in our memory.
        self.update_all_queues_file()

    def update_active_threads_list(self):
        """"Updates active threads based on if they are alive or not."""

        # reference: https://stackoverflow.com/questions/4067786/checking-on-a-thread-remove-from-list
        self.active_threads = [thread for thread in self.all_threads if thread.is_alive()]

    def update_status(self, status_message):
        """Updates the status by adding a line to the status box. It will also keep scrolling
        to the bottom each time it updates.
        POSSIBLE ERROR:: at times, this function, when run by threads can exhibit loss
        of characters to be displayed. The entire message is never lost, only certain characters.
        Occurs intermittently."""

        self.status_box_widget.append(str(status_message))
        # reference: https://stackoverflow.com/questions/7778726/autoscroll-pyqt-qtextwidget
        self.status_box_widget.moveCursor(QtGui.QTextCursor.End)
        self.update()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """Used to override the closeEvent() integrated GUI function."""

        self.exit_app()

    def exit_app(self):
        """Closes all sockets and exits the app."""

        for client_socket in self.all_client_sockets:
            client_socket.close()

        self.sock.close()
        print(self.all_threads)
        sys.exit(0)


def main():
    app = QApplication(sys.argv)
    screen_size = app.primaryScreen().size()
    ServerApp(screen_size.width(), screen_size.height())
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
