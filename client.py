import socket
import select
import json
import sys
import getpass


def getmove():
	print "enter move"
	move = int(raw_input())
	return move
def login(client):
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
		else:
			#retreive old user
			print "enter user name :"
			uname = str(raw_input())
			print "enter user password :"
			pw = getpass.getpass()
			#sendmsg({'l':[uname,pw]})
msg = {}
msg['m'] = 0
msg['e'] = 0
msg['t'] = 0
msg['i'] = 0
args = sys.argv[1:]
client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect((args[0],int(args[1])))
print >>sys.stderr, 'connected to %s port %s' % (args[0],args[1])

data = json.loads(str(client.recv(1024)))
print "got here",data
if data == 'wait':
	print "waiting for player to join"
	while 1:
		data = json.loads(str(client.recv(1024)))
		if data !='wait':
			break

print "got here",data
msg['i'] = data[0]
if data[1]==1:
	print "my turn"
	msg['m'] = getmove()
	data = json.dumps(msg)
	print "first msg  = ",data
	client.send(data)
else:
	print "opponents turn"

while 1:
	data = json.loads(str(client.recv(1024)))
	print "received data ",data
	print "opponents move :",data['m']
	msg['m'] = getmove()
	data = json.dumps(msg)
	print "msg  = ",data
	client.send(data)
