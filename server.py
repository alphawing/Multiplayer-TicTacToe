import socket
import select
import json
import Queue
import sys
import random
import sqlite3
import os
#to do
#game stats
#update db of winner



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
def hprint(s):
	rows, col = os.popen('stty size', 'r').read().split()
	print "".join(['-']*int(col))
	print s
	print "".join(['-']*int(col))

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
	def __init__(self,addr):
		self.srv = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.srv.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		self.srv.setblocking(0)
		self.srv.bind(addr)
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
			hprint( "database loaded")
		hprint( "server started on " +str(addr))
	

	def start(self):
		self.srv.listen(5)
		while 1:
			try:			
				readable,writable,exc = select.select(self.inp,self.outp,self.inp)
				for soc in readable:
					if soc is self.srv:
						#new connection requested
						self.newcon()
					else:
						data = soc.recv(2048)
						if data:
							#client has some data
							#msg = json.loads(str(data))
							msg = str(data)
							#process client request messages
							self.request(soc,msg)
						else:
							#client left
							hprint(str(soc.getpeername()) + "left")
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
							id = self.getid[soc]
							del self.getid[soc]
							self.online.remove(id)
							#disconnect soc's oponent
							if soc in self.pairs.keys():
								#get opponent of soc (todo : find better way)
								opponent = self.pairs[soc]
								del self.pairs[soc]
								del self.pairs[opponent]
								id = self.getid[opponent]
								del self.getid[opponent]
								self.online.remove(id)
								self.inp.remove(opponent)
								#not deleting from output list to relay message that peer has left 
								msg = message(e = 1)
								self.sendmsg(opponent,msg)
								hprint( str(opponent.getpeername())+"left")
								#not closing connection ??? because opponent does it itself


				for soc in writable:
					#hprint( "in write :" + str(soc.getpeername()))
					pass
					try:
						next_msg = self.msgq[soc].get_nowait()
					except Queue.Empty:
						# No messages waiting so stop checking for writability.
						#hprint('removing '+str(soc.getpeername())+' from writable')
						self.outp.remove(soc)
					else:
						hprint( 'sending ' + next_msg +"\nto " + str(soc.getpeername()))
						soc.send(next_msg)
				    # Handle "exceptional conditions"

				for soc in exc:
					hprint('handling exceptional condition for' + str(soc.getpeername()))
					# Stop listening for input on the connection
					self.inp.remove(soc)
					if soc in self.outp:
					    self.outp.remove(soc)
					soc.close()
					# Remove message queue
					del self.msgq[soc]
			except KeyboardInterrupt:
					hprint( "closing server")
					#close client connections
					for client in self.inp:
						client.close()
					self.srv.close()
					sys.exit()


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
		#print "sending to ",soc.getpeername()
		#print json.dumps(msg)
		self.msgq[soc].put(json.dumps(msg))

    


	def request(self,soc,msg):
		
		hprint( "received from "+str(soc.getpeername()) + '\n' + str(msg))
		msg = json.loads(msg)
		#print "received",msg,"from",soc.getpeername()
		
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
				#print "opponent disconnected"
				#self.msgq[opponent].put(json.dumps(tosened))
				#print "send disc msg to opp"
				tosend['e'] = 1
				self.sendmsg(opponent,tosend)
				#print "del game"
				del self.games[id]
				del self.pairs[soc]
				uid = self.getid[soc]
				del self.getid[soc]
				self.online.remove(uid)
				del self.pairs[opponent]
				uid = self.getid[opponent]
				del self.getid[opponent]
				self.online.remove(uid)
				#print "yes"
				self.inp.remove(soc)
				self.inp.remove(opponent)


			#forward game moves
			if msg['m'] != -1:
				#self.msgq[opponent].put(json.dumps(tosend))
				self.sendmsg(opponent,tosend)
	


	def	auth_client(self,soc,msg):
		#print "loging in .."
		tup = msg['t']
		loggedin = 0
		userid = -1
		if msg['d'] == 1:
			#create new user
			sql = "select count(1) from users where uname = ?"
			existing = self.con.execute(sql,(tup[0],)).fetchall()[0][0]
			if existing == 1:
				#user exists already send retry
				tosend = message(a = 0)
				self.sendmsg(soc,tosend)
				hprint( "user already exists")

			else:
				#add record and log in and send auth
				sql = "insert into users(uname,email,password,tgames,wgames) values(?,?,?,0,0);"
				self.con.execute(sql,tup)
				self.con.commit()
				loggedin = 1
				tosend = message(a = 1)
				self.sendmsg(soc,tosend)
				hprint( "new user added to db")
				sql = "select id from users where uname = ?"
				userid = self.con.execute(sql,(tup[0],)).fetchall()[0][0]
		if msg['d']==2:
			#log in existing user
			sql = "select count(1) from users where uname = ?"
			existing = self.con.execute(sql,(tup[0],)).fetchall()[0][0]
			#print "existing",existing
			if existing == 1:
				sql = "select id from users where uname = ?"
				userid = self.con.execute(sql,(tup[0],)).fetchall()[0][0]
				#print "userid",userid
				sql = "select password from users where uname = ?;"
				password = self.con.execute(sql,(tup[0],)).fetchall()[0][0]
				#print "password",password,"entered",tup[1]
				if userid in self.online:
					tosend = message(a = 0,o = 1)
					self.sendmsg(soc,tosend)
				
				elif tup[1] == password :
					#password matched send an auth
					tosend = message(a = 1,o=0)
					self.sendmsg(soc,tosend)
					loggedin  = 1
				else:
					#send retry
					tosend = message(a = 0,o=0)
					#print tosend
					self.sendmsg(soc,tosend)
				
			else:
				#send retry
				tosend = message(a = 0,o=0)
				#print tosend
				self.sendmsg(soc,tosend)


		#putting elif to send one message at a time 
		#if logged in add to wait list
		if loggedin == 1 :
			hprint( str(soc.getpeername()) +" logged in successfully")
			self.getid[soc] = userid
			self.online.append(userid)
			if self.waitq.isempty():
				#if no one is availabe , tell client to wait
				self.waitq.add(soc)
				hprint( "client " + str(soc.getpeername()) + "told to wait")
				msg = message(w = 1)
				self.sendmsg(soc,msg)
			else:
				#remove one from  wait list and pair
				opponent = self.waitq.pop()
				hprint( "connecting " + str(opponent.getpeername()) + " and " + str(soc.getpeername()))
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




if __name__ == "__main__":
	if sys.argv[1:] == []:
		addr = ("",5000)
		hprint( "starting server on default address")
	else:
		try:
			args = sys.argv[1:]
			addr = (args[0],int(args[1]))
		except:
			hprint( "usage : arg1 = hostname , arg2 = port ")
			sys.exit()
	gameserver = server(addr)
	gameserver.start()