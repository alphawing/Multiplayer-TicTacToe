import socket
import select
import json
import Queue
import sys
import random
import sqlite3
import os

#update db of winner
#game class #playwith ai or playwith opp
#minmax AI
#login accounts
#different functions for diff requests


#message meanings :
#e : exit
#i : game id
#m : move info
#t : info tuple
#w : wait
#s : start
#t : turn
#u : unique username
#a : authorised
#n : new user?
#o : user online
def message(**kwargs):
	msg = {}
	msg['e'] = 0
	msg['i'] = 0
	msg['m'] = 0
	msg['t'] = 0
	msg['w'] = 0
	msg['s'] = 0
	msg['u'] = 0
	msg['a'] = 0
	for key,val in kwargs.iteritems():
		msg[key] = val
	return msg


class Q(object):
	def __init__(self):
		self.q = []
	def add(self,a):
		self.q.append(a)
	def pop(self):
		if len(self.q) == 0:
			return None
		else:
			p = self.q[0]
			if len(self.q)>1:
				self.q = self.q[1:]
			else:
				self.q = []
		return p
	def isempty(self):
		if self.q == []:
			return True
		else:
			return False
	def remove(self,a):
		self.q.remove(a)

class server(object):
	def __init__(self,addr,port):
		self.srv = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		self.srv.setblocking(0)
		self.srv.bind((addr,port))
		self.inp = [self.srv]
		self.games = {}
		self.id=0
		self.waiting = []
		self.outp = []
		self.msgq = {}
		self.waitq = Q()
		self.pairs = {}
		self.online = []
		self.getid = {}
		if not os.path.exists("data.db"):
			#create database,add table
			self.con = sqlite3.connect("data.db")
			sql = "create table users(id integer primary key autoincrement,uname varchar,password varchar,email varchar,tgames integer,wgames integer)"
			self.con.execute(sql)
			self.con.commit()
			print "Database created"
		else:
			#just connect
			self.con = sqlite3.connect("data.db")
			print "database loaded"
		print "1.server started on %s , port %d " % (addr,port)

	

	def start(self):
		self.srv.listen(5)
		while 1:
			readable,writable,exc = select.select(self.inp,self.outp,self.outp)
			for soc in readable:
				if soc is self.srv:
					#new connection requested
					self.newcon()
				else:
					data = soc.recv(1024)
					if data:
						#client has some data
						#msg = json.loads(str(data))
						msg = str(data)
						#process client request messages
						self.request(soc,msg)
					else:
						#client left
						print soc.getpeername(),"left"
						#remov soc from output list
						if soc in self.outp:
							self.outp.remove(soc)
						#remov soc from input list
						self.inp.remove(soc)
						#remove if waiting
						if soc in self.waitq.q:
							self.waitq.remove(soc)
						soc.close()
						#delete soc's output message queue
						del self.msgq[soc]
						#disconnect soc's oponent
						if soc in self.pairs.keys():
							#get opponent of soc (todo : find better way)
							opponent = self.pairs[soc]
							del self.pairs[soc]
							id = self.getid[soc]
							del self.getid[soc]
							self.online.remove(id)
							del self.getid[soc]
							del self.pairs[opponent]
							id = self.getid[opponent]
							del self.getid[opponent]
							self.online.remove(id)
							del self.getid[opponent]


							self.inp.remove(opponent)
							#not deleting from output list to relay message that peer has left 
							msg = message(e = 1)
							self.sendmsg(opponent,msg)
							print opponent.getpeername(),"left"
							#not closing connection ??? because opponent does it itself


			for soc in writable:
				print "in write :",soc.getpeername()
				try:
					next_msg = self.msgq[soc].get_nowait()
				except Queue.Empty:
					# No messages waiting so stop checking for writability.
					print >>sys.stderr, '2.output queue for', soc.getpeername(), 'is empty'
					self.outp.remove(soc)
				else:
					print >>sys.stderr, '3.sending "%s" to %s' % (next_msg, soc.getpeername())
					soc.send(next_msg)
			    # Handle "exceptional conditions"

			for soc in exc:
				print >>sys.stderr, 'handling exceptional condition for', soc.getpeername()
				# Stop listening for input on the connection
				self.inp.remove(soc)
				if soc in self.outp:
				    self.outp.remove(soc)
				soc.close()
				# Remove message queue
				del self.msgq[soc]


	def newcon(self):
		#assign opponent if available or keep item in waitlist
		client,client_addr = self.srv.accept()
		client.setblocking(0)#reason ??? not to block so that only select blocks
		self.inp.append(client)#append to readable
		self.msgq[client] = Queue.Queue()#q for outgoing msgs
		#if client not in self.outp:# ***resolved*** removing this ? causes client to ask for one more move after peer disconnect
		self.outp.append(client)
		

	
	def sendmsg(self,soc,msg):
		if soc not in self.outp:
			self.outp.append(soc)
		self.msgq[soc].put(json.dumps(msg))

    


	def request(self,soc,msg):
		msg = json.loads(msg)
		print "received",msg,"from",soc.getpeername()
		
		#database operation : (login/auth/player stat (from gamestats))
		if msg['d']!=0:
			self.auth_client(soc,msg)

		else:
			#get game id , pair,opponent
			tosend = message(m = msg['m'],t = 1)                      
			id = msg['i']
			players = self.games[id]
			if players[0] == soc:
				opponent = players[1]
			else:
				opponent = players[0]

			#handle close requests , when msg['e'] = 1
			
			if msg['e'] == 1:
				print "opponent disconnected"
				#self.msgq[opponent].put(json.dumps(tosened))
				print "send disc msg to opp"
				tosend['e'] = 1
				self.sendmsg(opponent,tosend)
				print "del game"
				del self.games[id]
				del self.pairs[soc]
				del self.pairs[opponent]
				print "yes"
				self.inp.remove(soc)
				self.inp.remove(opponent)

			#forward game moves
			if msg['m'] != -1:
				#self.msgq[opponent].put(json.dumps(tosend))
				self.sendmsg(opponent,tosend)
	


	def	auth_client(self,soc,msg):
		print "loging in ..."
		tup = msg['t']
		loggedin = 0
		sql = "select id from users where uname = ?"
		userid = self.con.execute(sql,(tup[0],)).fetchall()[0][0]
		if msg['d'] == 1:
			#create new user
			sql = "select count(1) from users where uname = ?"
			existing = self.con.execute(sql,(tup[0],)).fetchall()[0][0]
			if existing == 1:
				#user exists already send retry
				tosend = message(a = 0)
				self.sendmsg(soc,tosend)
				print "user already exists"

			else:
				#add record and log in and send auth
				sql = "insert into users(uname,password,email,tgames,wgames) values(?,?,?,0,0);"
				self.con.execute(sql,tup)
				loggedin = 1
				tosend = message(a = 1)
				self.sendmsg(soc,tosend)
				print "new user added to db"
		elif msg['d']==2:
			#log in existing user
			sql = "select count(1) from users where uname = ?"
			existing = self.con.execute(sql,(tup[0],)).fetchall()[0][0]
			sql = "select password from users where uname = ?;"
			password = self.con.execute(sql,(tup[0],)).fetchall()
			if password != []:
				(password,) = password[0]
				print password
			print tup
			print "user enetered",tup[1],"existing ?",existing
			if userid in self.online:
				tosend = message(a = 0,o = 1)
				self.sendmsg(soc,tosend)
				print "user already online"
			elif tup[1] == password and existing == 1:
				#password matched send an auth
				tosend = message(a = 1,o=0)
				self.sendmsg(soc,tosend)
				loggedin  = 1
				print "details matched logging in "
				
			else:
				#send retry
				print "not logged in /pass"
				tosend = message(a = 0,o=0)
				print tosend
				self.sendmsg(soc,tosend)
				print "wrong uname pass combo"
		#if logged in add to wait list
		if loggedin == 1 :
			print "logged in successfully"
			self.getid[soc] = userid
			self.online.append(userid)
			if self.waitq.isempty():
				#if no one is availabe , tell client to wait
				self.waitq.add(soc)
				print "4.client ",soc.getpeername(),"told to wait"
				msg = message(w = 1)
				self.msgq[soc].put(json.dumps(msg))
			else:
				#remove one from  wait list and pair
				opponent = self.waitq.pop()
				print "5.connecting ",opponent.getpeername()," and ",soc.getpeername()
				#find  a better way
				self.pairs[soc] = opponent
				self.pairs[opponent] = soc
				#self.startgame(client,opponent)
				#generate random turn
				turn = random.randrange(2)
				#assign a game id
				self.id+=1
				self.games[self.id] = (soc,opponent)
				#send message to stop waiting and initialize game env
				msg = message(i = self.id,t = turn)
				self.sendmsg(soc,msg)
				msg = message(i = self.id,t = 1-turn)
				self.sendmsg(opponent,msg)


	def startgame(self,c,o):
		self.id = self.id+1
		self.games[self.id] = (c,o)
		msg = message(s=1)
		self.msgq[c].put(json.dumps(msg))
		self.msgq[o].put(json.dumps(msg))
	



	def endgame(self):
		pass

	



	def disconnectop(self,soc):
		#players = self.games[id]
		#if players[0] == soc:
		#	opponent = players[1]
		#	self.msgq[o].put(json.dumps("wait"))
		pass




if sys.argv == []:
	print >>sys.stderr, '8.enter hostname and port for server'
else:
	args = sys.argv[1:]
gameserver = server(args[0],int(args[1]))
gameserver.start()