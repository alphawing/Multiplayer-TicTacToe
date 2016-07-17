import socket
import select
import json
import sys
import getpass
from tictactoe import *
import os
#todo
#send game stats to server
#allow connected users to play another match


def hprint(s):
	rows, col = os.popen('stty size', 'r').read().split()
	print "".join(['-']*int(col))
	print s
	print "".join(['-']*int(col))


#todo
#update winner record  level up
def message(a,**kwargs):
	msg = {}
	if a == 1:	
		#initialize default values of flags
		msg['m'] = 0#move
		msg['e'] = 0#exit
		msg['t'] = 0#information tuple
		msg['i'] = 0#id
		msg['c'] = -1#game winner
		msg['d'] = 0#database operation request
	for key,val in kwargs.iteritems():
		msg[key] = val
	return msg


def getmove():
	print "enter move"
	move = int(raw_input())
	return move




def send(soc,msg):
	data = json.dumps(msg)
	#print "sending ",data
	soc.send(data)




def recv(soc):
	rec = soc.recv(1024)
	#print "received",rec
	data = json.loads(str(rec))
	
	return data




def login():
	print "1. SIGN IN\n2.SIGN UP (new user?)"
	ans = int(raw_input())
	if ans==2:
		r = (0,) + getsignup()
	else:
		#retreive old user
		r = (1,) + getlogin()
	return r
def getsignup():
	print "SIGNUP"
	#create new user
	print "enter user name :"
	uname = str(raw_input())
	print "enter email :"
	email = str(raw_input())
	pw = getpass.getpass()
	#sendmsg({'n':[uname,pw,name,email]})
	r = (uname,email,pw)
	return r
def getlogin():
	print "LOGIN"
	print "enter user name :"
	uname = str(raw_input())
	pw = getpass.getpass()
	#sendmsg({'l':[uname,pw]})
	r = (uname,pw)
	return r

class play_online(object):
	def __init__(self,addr):
		self.player = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.player.connect(addr)
		print >>sys.stderr, 'connected to %s port %s' % (addr)
		data = login()
		self.msg = message(1,m=0,e=0,t=0,i=0,s=0,c=-1)
		self.g = 0
		self.close = 0
		self.turn = 0
		self.won = 0
		self.a=0
		self.b=0
		self.loggedin = 0
		mode = data[0]
		data = data[1:]
		if mode ==1:
			#existing account
			while self.loggedin!=1:
				tosend = message(1,d = 2,t = data)
				send(self.player,tosend)
				#print "listening response"
				response = recv(self.player)
				self.loggedin = response['a']
				if self.loggedin==0:
					if response['o'] == 1:
						print "user already online"
					else:
						print "Wrong Username password combination"
					data = getlogin()
					
		else:
			while self.loggedin!=1:
				#create new account in server db
				tosend = message(1,d = 1,t = data)
				send(self.player,tosend)
				response = recv(self.player)
				self.loggedin = response['a']
				if self.loggedin==0:
					print "User already exists. Try again!"
					data = getsignup()
				pass
			print "logged in successfully"
		self.connect_peer()
		self.play_game()






	def connect_peer(self):
		data = recv(self.player)
		if data['w'] == 1:
			print "waiting for player to join"
			while 1:
				data = recv(self.player)
				if data['w'] != 1:
					break
		print "connected to peer"
		self.msg['i'] = data['i']
		self.turn  = data['t']






	def play_game(self):

		#if player has first move , then send data
		hprint("->game started\n->enter moves as digits from 1 to 9\n->enter -1 to leave game")
		board = tictactoe()
		board.show()
		if self.turn ==1:
			player = 'X'
			hprint ("you are " + player)
		else:
			player = 'O'
			hprint ("you are "+player)
		if self.turn==1:
			print "my turn"
			move = getmove()
			if move == -1:
				self.msg['e'] = 1
				self.close = 1
			else:
				valid = 0
				while valid !=1:
					if not move-1 in board.valid_moves():
						print "invalid move"
						move = getmove()
					else:
						valid = 1
				board.play_move(move-1, player)
				board.show()
				self.msg['m'] = move
				self.g+=1
				#self.a+=1
				send(self.player,self.msg)
		if self.close==1:
			self.player.close()
		else:
			print "opponents turn"
		#get opponnents move and send move
		while self.close!=1 and not board.over():
			data = recv(self.player)
			#print "received ",data
			if data['e'] == 1:
				print "peer disconnected"
				self.player.close()
				break
			print "opponents move :",data['m']
			move = data['m']
			board.play_move(move-1, board.opponent(player))
			board.show()
			self.g+=1
			print "g:",self.g
			self.b+=data['m']
			if board.over():
				hprint("game over !!!")
				self.closegame(board,player)
				break
			else:
				print "your turn"
				move = getmove()
				if move == -1:
					self.msg['e'] = 1
					self.close = 1
				else:
					valid =0
					while valid !=1:
						if not move-1 in board.valid_moves():
							print "invalid move"
							move = getmove()
						else:
							valid = 1
					board.play_move(move-1, player)
					board.show()
					self.msg['m'] = move
				send(self.player,self.msg)
				print "opponents turn"
			if board.over():
				print "game over"
				self.closegame(board,player)
				break
			if self.close==1:
				print "game terminated"
				self.closegame()
				break






	def sendgamestats(self,board,player):
		#print "game stat"
		if board.winner()==player:
			hprint("you won !!")
			#self.msg['c'] = 1
			#print "sending game stat"
			#data = json.dumps(self.msg)
		elif board.winner() == None:
			hprint("its a tie!!")
			#self.msg['c'] = 1
			#print "sending game stat"
			#data = json.dumps(self.msg)
		else:
			hprint("you lost!!")









	def closegame(self,board = None , player = None):
		if (board!=None and player != None):
			self.sendgamestats(board,player)
		print "closing connection"
		self.player.close()
		print "disconnected"





def play_offline():
	board = tictactoe()
	board.show()
	Ai = AIbot('O')
	while not board.over():
		player = 'X'
		move = int(raw_input("Next Move: ")) - 1
		if not move in board.valid_moves():
			print "invalid move"
			continue
		board.play_move(move, player)
		#board.show()
		if board.over():
			break
		computer_move = Ai.makemove(board)
		print computer_move
		board.play_move(computer_move, 'O')
		board.show()
	board.show()
	winner = board.winner()
	if winner == None:
		print "its a tie"
	else:
		print winner,"won"












args = sys.argv[1:]
if args == []:
	play_offline()
else:
	if args[0] == 'o':
		addr = ("",5000)
	else:
		addr = (args[0],args[1])
	newgame = play_online(addr)




