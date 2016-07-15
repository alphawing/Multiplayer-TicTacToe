import socket
import select
import json
import sys
import getpass
#todo

#login

#done : player class

#win notification send msg exit
#loss notification exit
#send game over if win , other will quit auto due to loss


#database
#update winner record  level up

#game class - main class 

def message(**kwargs):
	msg = {}
	msg['m'] = 0#move
	msg['e'] = 0#exit
	msg['t'] = 0#?
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
	print "sending ",data
	soc.send(data)




def recv(soc):
	data = json.loads(str(soc.recv(1024)))
	return data




def login():
	print "wanna login ?"
	ans = int(raw_input())
	if ans == 0 :
		pass
	else:
		print "new user/existing?"
		ans = int(raw_input())
		if ans==0:
			#create new user
			print "enter user name :"
			uname = str(raw_input())
			print "enter name :"
			name = str(raw_input())
			print "enter email :"
			email = str(raw_input())
			print "enter user :"
			pw = getpass.getpass()
			#sendmsg({'n':[uname,pw,name,email]})
			r = (ans,uname,name,email,pw)
		else:
			#retreive old user
			print "enter user name :"
			uname = str(raw_input())
			print "enter user password :"
			pw = getpass.getpass()
			#sendmsg({'l':[uname,pw]})
			r = (ans,uname,pw)
		return r
	return





class play_online(object):
	def __init__(self,addr,data):
		self.player = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.player.connect(addr)
		print >>sys.stderr, 'connected to %s port %s' % (addr)
		self.msg = message(m=0,e=0,t=0,i=0,s=0,c=-1)
		self.g = 0
		self.close = 0
		self.turn = 0
		self.won = 0
		self.a=0
		self.b=0
		if data[0]==1:
			#existing account
			pass
		else:
			#create new account in server db
			pass
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
		if self.turn==1:
			print "my turn"
			move = getmove()
			if move == -1:
				self.msg['e'] = 1
				self.close = 1
			else:
				self.msg['m'] = move
				self.g+=1
				self.a+=1
				send(self.player,self.msg)
		if self.close==1:
			self.player.close()
		else:
			print "opponents turn"
		#get opponnents move and send move
		while self.close!=1 and self.g<9:
			data = recv(self.player)
			print "received ",data
			if data['e'] == 1:
				print "peer disconnected"
				self.player.close()
				break
			print "opponents move :",data['m']
			self.g+=1
			print "g:",self.g
			self.b+=data['m']
			if self.g==9:
				print "game over ,disconnecting"
				self.closegame()
				break
			else:
				move = getmove()
				if move == -1:
					self.msg['e'] = 1
					self.close = 1
				else:
					self.msg['m'] = move
					self.g+=1
					self.a+=move
				send(self.player,self.msg)
				print "opponrnts turn"
			if self.g==9:
				print "game over ,disconnecting"
				self.closegame()
				break
			if self.close==1:
				print "game terminated"
				self.closegame()
				break






	def sendgamestats(self):
		print "sending game stat"
		if self.a>self.b:
			print "you won !"
			self.msg['c'] = 1
			print "sending game stat"
			data = json.dumps(self.msg)
		else:
			print "you lost"
			self.msg['c'] = 1
			print "sending game stat"
			data = json.dumps(self.msg)










	def closegame(self):
		self.sendgamestats()
		print "closing connection"
		self.player.close()
		print "disconnected"

















addr = ("",5000)
args = sys.argv[1:]
if args:
	addr = (args[0],args[1])
data = login()
if data == None:
	#play offline
	pass
else:
	newgame = play_online(addr,data)




