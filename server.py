import socket
import select
import json
import Queue
import sys
import random

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
		self.ng = 0
		self.waiting = []
		self.outp = []
		self.msgq = {}
		self.waitq = Q()
		self.clientobj = {}
		self.notready = []
		print "1.server started on %s , port %d " % (addr,port)

	

	def start(self):
		self.srv.listen(5)
		while 1:
			readable,writable,exc = select.select(self.inp,self.outp,self.inp)
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
						self.request(soc,msg)
					else:
						#client left
						if soc in self.outp:
							self.outp.remove(soc)
						self.inp.remove(soc)
						if soc in self.waitq.q:
							self.waitq.remove(soc)
						soc.close()
						del self.msgq[soc]

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
		client,client_addr = self.srv.accept()
		client.setblocking(0)
		self.inp.append(client)
		self.msgq[client] = Queue.Queue()
		if client not in self.outp:
			self.outp.append(client)
		if self.waitq.isempty():
			self.waitq.add(client)
			print "4.client ",client.getpeername(),"told to wait"
			self.msgq[client].put(json.dumps("wait"))
		else:

			opponent = self.waitq.pop()
			print "5.connecting ",opponent.getpeername()," and ",client.getpeername()
			#self.startgame(client,opponent)
			turn = random.randrange(2)
			self.id+=1
			self.games[self.id] = (client,opponent)
			print "a"
			self.sendmsg(client,[self.id,turn])
			print "b"
			self.sendmsg(opponent,[self.id,1-turn])
			#print self.msgq[client],client.getpeername()
			#print self.msgq[opponent],opponent.getpeername()
			#print self.inp
			#print self.outp
			#print "6.messages sent"
	def sendmsg(self,soc,msg):
		if soc not in self.outp:
			self.outp.append(soc)
		self.msgq[soc].put(json.dumps(msg))

    


	def request(self,soc,msg):
		print "reached here*******************"
		msg = json.loads(msg)
		print "7.received msg",msg,"from",soc.getpeername()
		tosend = {}
		tosend['m'] = msg['m']
		tosend['t'] = 1
		tosend['e'] = 0                                          
		id = msg['i']
		players = self.games[id]
		if players[0] == soc:
			opponent = players[1]
		else:
			opponent = players[0]
		if msg['e'] == 1:
			opponent = self.games[id]
			#self.msgq[opponent].put(json.dumps(tosened))
			self.sendmsg(opponent,tosend)
			del self.games[id]
		if msg['m'] != -1:
			tosend['m'] = msg['m']
			tosend['t'] = 1
			#self.msgq[opponent].put(json.dumps(tosend))
			self.sendmsg(opponent,tosend)
	def startgame(self,c,o):
		self.id = self.id+1
		self.games[self.id] = (c,o)
		self.msgq[c].put(json.dumps("start"))
		self.msgq[o].put(json.dumps("start"))
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



