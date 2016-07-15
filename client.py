import socket
import select
import json
import sys
import getpass
#todo

#login

#client class

#database

#win notification send msg exit

#loss notification exit

#update winner record  level up

#send game over if win , other will quit auto due to loss

#game class - main class 



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
msg['m'] = 0#move
msg['e'] = 0#exit
msg['t'] = 0#?
msg['i'] = 0#id
msg['s'] = 0#game stat
msg['c'] = -1#game winner
g = 0
close = 0
args = sys.argv[1:]
client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
client.connect((args[0],int(args[1])))
print >>sys.stderr, 'connected to %s port %s' % (args[0],args[1])

data = json.loads(str(client.recv(1024)))
if data['w'] == 1:
	print "waiting for player to join"
	while 1:
		data = json.loads(str(client.recv(1024)))
		if data['w'] != 1:
			break

print "Conencted to peer"
msg['i'] = data['i']
turn  = data['t']
if turn==1:
	print "my turn"
	move = getmove()
	if move == -1:
		msg['e'] = 1
		close = 1
	else:
		msg['m'] = move
		g+=1
	data = json.dumps(msg)
	client.send(data)
	if close==1:
		client.close()
else:
	print "opponents turn"
print "g:",g
while close!=1 and g<9:
	data = json.loads(str(client.recv(1024)))
	if data['e'] == 1:
		print "peer disconnected"
		client.close()
		break
	print "opponents move :",data['m']
	g+=1
	print "g:",g
	if g==9:
		print "game over ,disconnecting"
		break
	else:
		move = getmove()
		if move == -1:
			msg['e'] = 1
			close = 1
		else:
			msg['m'] = move
			g+=1
		data = json.dumps(msg)
		print "msg  = ",data
		client.send(data)
	if close==1:
		client.close()
		break
if g==9 and turn ==1:
	msg['s'] = 1
	msg['c'] = 1
	print "sending game stat"
	data = json.dumps(msg)
	print "disconnecting"
	client.close()

