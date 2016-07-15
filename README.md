# Multiplayer-TicTacToe
Multiplayer TicTacToe is based on socket module in python.
The server is implemented via asynchronous event driven approach using select module
Server communicates with clients to see if they are ready to join a game and adds the client to a wait list , 2 clients are paired and a game is initiated between them.
Server acts as middleware and handles messages between the paired clients.

