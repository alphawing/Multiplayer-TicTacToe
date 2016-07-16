
import random

class tictactoe(object):
	winning_moves = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
	def __init__(self,board = []):
		if board == []:
			self.board = [None]*9
		else:
			self.board = board
	def show(self):
		for i in xrange(3):
			print "",
			for l in xrange(6):
				print "-",
			print
			for col,j in enumerate(self.board[3*i:3*(i+1)]):
				print "|",
				if j == None:
					print (i)*3+col+1,
				else:
					print j,
			print "|"
		print "",
		for l in xrange(6):
			print "-",
		print
	def valid_moves(self):
		valid = []
		for i,x in  enumerate(self.board):
			if x == None:
				valid.append(i)
		return valid
	def valid_winmoves(self,player):
		return self.valid_moves() + self.my_moves(player)


	def over(self):
		if None not in self.board :
			return True
		if self.winner()!=None:
			return True
		return False
	def my_moves(self,player):
		return [k for k, v in enumerate(self.board) if v == player]
	def play_move(self,position,player):
		self.board[position] = player
	def winner(self):
		for player in ['X','O']:
			setpos = self.my_moves(player)
			for winmove in self.winning_moves:
				win = True
				for pos in winmove:
					if pos not in setpos:
						win = False
				if win:
					return player
		return
	def opponent(self,player):
		if player == 'X':
			return 'O'
		else:
			return 'X'


class AIbot(object):
	def __init__(self,playersign):
		self.player = playersign
	def minimax_alphabetafull(self,state,dummyplayer,alpha,beta,depth):
		if depth ==0:
			return 0
		if state.over():
			if state.winner() == self.player:
				return 1
			elif state.winner() == None:
				return 0
			elif state.winner() == state.opponent(self.player):
				return -1
		for move in state.valid_moves():
			state.play_move(move,dummyplayer)
			score = self.minimax_alphabetafull(state,state.opponent(dummyplayer),alpha,beta,depth-1)
			state.play_move(move,None)
			if dummyplayer == self.player:
				if score > alpha: #maximise our score
					alpha = score
				if alpha >= beta:
					return beta
			else:
				if score < beta: #minimise opponent's score
					beta = score
				if beta <= alpha:
					return alpha
		if dummyplayer == self.player:
			return alpha
		else:
			return beta
	def makemove(self,state):
		a = -2
		moves = []
		# if initial turn
		if len(state.valid_moves()) == 9:
			return 4
		for move in state.valid_moves():
			state.play_move(move, self.player)
			score = self.minimax_alphabetafull(state , state.opponent(self.player), -2, 2,6)
			state.play_move(move, None)
			#print "move:", move + 1, "causes:", score
			if score > a:
				a = score
				moves = [move]
			elif score == a:
				moves.append(move)
		return random.choice(moves)

