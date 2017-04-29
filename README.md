# Multiplayer-TicTacToe
Multiplayer TicTacToe is based on socket module in python.
The server is implemented via asynchronous event driven approach using select module.
Server communicates with clients to see if they are ready to join a game and adds the client to a wait list , 2 clients are paired and a game is initiated between them.Server acts as middleware and handles messages between the paired clients.
Server is implemented with asynchronous management of logins and disconnects and basic authorization using username and password.It starts a game between twoo connected clients.It supports any number of simultaneous games.

Added AI player based on the minimax algo

# Usage
First start the server , then connect client to that server 
Run the surver with default hostname and port

```
python server.py
```

Run the server with custom host and port

```
python server.py 'host' 'port'
```

Run client in offline mode (to play with ai)

```
python client.py
```

Run the client in online mode with default host and port

```
python client.py o
```

Run the client with custom host and port

```
python client.py host port
```

The tic tac toe board is represented as a grid and moves are represented by numbers written in the cells. Enter the corresponding number to make a move.

## Todo
* implement a GUI
* saving game stats on server
* assign rating to players according to total matches won
* Add an AI player that does not play optimally (introduce random errors in current ai)
* p2p communication for clients
