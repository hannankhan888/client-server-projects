# client-server-projects
Various client-server projects created for class projects.

# Project 1
Consists of a client and server application with a GUI written in PyQt5. These applications' purpose is to have multiple clients connect to the server (multi-threaded), and have a randomly selected client receive a countdown timer. When the client finishes, after a total of 10 seconds have passed, another client is selected by the server.
### Issues faced
 - Deleting a client correctly seems to be a large issue to handle for. My guess is, it is due to the way I have wrote the code. A recreation would most likely be written using simpler code.
 - One of the sub-issues with deleting a client is the recognition of that deletion from the server. The server will only notice a client has disconnected when it randomly selects that client again. In the recreation, I would implement an explicit disconnect message to the server, so that it may handle the deletion of a client immedietly.

# Project 2
Consists of a client and server application with a GUI written in PyQt5. These applications' purpose is to have multiple clients connect to a server with persistent storage. Any client has the option of uploading a message (a double) to any one of 3 queues in the server. Any other client can access any queue and retrieve the messages in that queue. The messages in the queue are the conversions of that double into the numerous units defined in repository.txt.
## This project aimed to utilize a message-broker system.
The functions that could be considered as part of the message broker (server-side) are:
 - _init_repository_dict()
 - _init_all_queues()
 - add_to_queue()
 - update_all_queues_file()

The queues are converted into lists, serialized, and stored in a binary file via Python's pickle module. The conversion to lists is done due to the fact that queues in Python are thread-safe objects, and cannot be serialized. The binary file is created upon use: all_queues.p.
These applications are also multi-threaded to support multiple clients.
