
# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Jordan Pham, Van Khoa Vu
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
#				agent in this file. You will write the 'getAction' function,
#				the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
#				- DO NOT MAKE CHANGES TO THIS FILE.
# ==============================CS-199==================================
from AI import AI
from Action import Action
from collections import deque


class MyAI( AI ):

	def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
		########################################################################
		#							YOUR CODE BEGINS						   #
		########################################################################
		self._rowDimension = rowDimension
		self._colDimension = colDimension
		self._totalMines   = totalMines
		# Internal board: _board[col][row] is a dict with three fields:
		#   'covered'  - True if the tile has not been uncovered yet
		#   'number'   - the hint number once uncovered (-1 while still covered)
		#   'flagged'  - True if we have placed a flag on this tile
		self._board = [
			[{'covered': True, 'number': -1, 'flagged': False}
			 for _ in range(rowDimension)]
			for _ in range(colDimension)
		]
		self._lastAction = AI.Action.UNCOVER
		self._lastX      = startX
		self._lastY      = startY
		self._queue      = deque()
		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################

	def getAction(self, number: int) -> "Action Object":
		########################################################################
		#							YOUR CODE BEGINS						   #
		########################################################################
		# Update the internal board with the result of the last action
		if self._lastAction == AI.Action.UNCOVER:
			self._board[self._lastX][self._lastY]['covered'] = False
			self._board[self._lastX][self._lastY]['number']  = number
		elif self._lastAction == AI.Action.FLAG:
			self._board[self._lastX][self._lastY]['flagged'] = True
		elif self._lastAction == AI.Action.UNFLAG:
			self._board[self._lastX][self._lastY]['flagged'] = False

		# If there are already queued actions, execute the next one
		if self._queue:
			return self._executeNext()

		# Global mine count checks
		covered_unflagged = [
			(c, r) for c in range(self._colDimension)
			for r in range(self._rowDimension)
			if self._board[c][r]['covered'] and not self._board[c][r]['flagged']
		]
		total_flagged = sum(
			1 for c in range(self._colDimension)
			for r in range(self._rowDimension)
			if self._board[c][r]['flagged']
		)
		remaining_mines = self._totalMines - total_flagged
		if remaining_mines == 0:
			for (c, r) in covered_unflagged:
				self._queue.append((AI.Action.UNCOVER, c, r))
		elif remaining_mines == len(covered_unflagged):
			for (c, r) in covered_unflagged:
				self._queue.append((AI.Action.FLAG, c, r))
		if self._queue:
			return self._executeNext()

		# Apply constraint logic to find safe tiles and known mines
		self._findMoves()
		if self._queue:
			return self._executeNext()

		# Apply advanced subset logic
		self._applyConstraintSubsets()
		if self._queue:
			return self._executeNext()

		# No logical move found, make a probability-based guess
		return self._guess()
		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################

	def _findMoves(self):
		safeTiles = set()
		mineTiles = set()
		changed = True
		while changed:
			changed = False
			for c in range(self._colDimension):
				for r in range(self._rowDimension):
					cell = self._board[c][r]
					if cell['covered'] or cell['number'] < 0:
						continue
					neighbors = self._getNeighbors(c, r)
					coveredUnflagged = [
						n for n in neighbors
						if self._board[n[0]][n[1]]['covered']
						and not self._board[n[0]][n[1]]['flagged']
						and n not in mineTiles
					]
					knownMines = [
						n for n in neighbors
						if self._board[n[0]][n[1]]['flagged'] or n in mineTiles
					]
					remaining = cell['number'] - len(knownMines)
					# Rule A: all remaining covered neighbors are safe
					if remaining == 0:
						for n in coveredUnflagged:
							if n not in safeTiles:
								safeTiles.add(n)
								changed = True
					# Rule B: all remaining covered neighbors are mines
					if remaining > 0 and remaining == len(coveredUnflagged):
						for n in coveredUnflagged:
							if n not in mineTiles:
								mineTiles.add(n)
								changed = True
		for (c, r) in mineTiles:
			if not self._board[c][r]['flagged']:
				self._queue.append((AI.Action.FLAG, c, r))
		for (c, r) in safeTiles:
			if self._board[c][r]['covered'] and not self._board[c][r]['flagged']:
				self._queue.append((AI.Action.UNCOVER, c, r))

	def _getNeighbors(self, c, r):
		neighbors = []
		for dc in [-1, 0, 1]:
			for dr in [-1, 0, 1]:
				if dc == 0 and dr == 0:
					continue
				nc, nr = c + dc, r + dr
				if 0 <= nc < self._colDimension and 0 <= nr < self._rowDimension:
					neighbors.append((nc, nr))
		return neighbors

	def _executeNext(self):
		actionType, x, y = self._queue.popleft()
		self._lastAction = actionType
		self._lastX      = x
		self._lastY      = y
		return Action(actionType, x, y)

	def _applyConstraintSubsets(self):
		constraints = []
		for c in range(self._colDimension):
			for r in range(self._rowDimension):
				cell = self._board[c][r]
				if cell['covered'] or cell['number'] <= 0:
					continue
				neighbors = self._getNeighbors(c, r)
				covered = frozenset(
					n for n in neighbors
					if self._board[n[0]][n[1]]['covered']
					and not self._board[n[0]][n[1]]['flagged']
				)
				flagged = sum(1 for n in neighbors if self._board[n[0]][n[1]]['flagged'])
				remaining = cell['number'] - flagged
				if covered and remaining >= 0:
					constraints.append((covered, remaining))

		to_uncover = set()
		to_flag = set()
		for i in range(len(constraints)):
			for j in range(len(constraints)):
				if i == j:
					continue
				tiles_i, mines_i = constraints[i]
				tiles_j, mines_j = constraints[j]
				if tiles_i < tiles_j:
					diff = tiles_j - tiles_i
					diff_mines = mines_j - mines_i
					if diff_mines == 0:
						for (c, r) in diff:
							if self._board[c][r]['covered'] and not self._board[c][r]['flagged']:
								to_uncover.add((c, r))
					elif diff_mines == len(diff):
						for (c, r) in diff:
							if not self._board[c][r]['flagged']:
								to_flag.add((c, r))
		for (c, r) in to_flag:
			self._queue.append((AI.Action.FLAG, c, r))
		for (c, r) in to_uncover:
			self._queue.append((AI.Action.UNCOVER, c, r))

	def _guess(self):
		covered_tiles = [
			(c, r) for c in range(self._colDimension)
			for r in range(self._rowDimension)
			if self._board[c][r]['covered'] and not self._board[c][r]['flagged']
		]
		if not covered_tiles:
			return Action(AI.Action.LEAVE)

		mine_probs = {}
		for c in range(self._colDimension):
			for r in range(self._rowDimension):
				cell = self._board[c][r]
				if cell['covered'] or cell['number'] <= 0:
					continue
				neighbors = self._getNeighbors(c, r)
				covered = [
					n for n in neighbors
					if self._board[n[0]][n[1]]['covered']
					and not self._board[n[0]][n[1]]['flagged']
				]
				flagged = sum(1 for n in neighbors if self._board[n[0]][n[1]]['flagged'])
				remaining = cell['number'] - flagged
				if covered:
					prob = remaining / len(covered)
					for tile in covered:
						mine_probs[tile] = max(mine_probs.get(tile, 0), prob)

		total_covered = len(covered_tiles)
		total_flagged = sum(
			1 for c in range(self._colDimension)
			for r in range(self._rowDimension)
			if self._board[c][r]['flagged']
		)
		global_prob = (self._totalMines - total_flagged) / total_covered if total_covered else 1.0

		best, best_prob = None, float('inf')
		for tile in covered_tiles:
			prob = mine_probs.get(tile, global_prob)
			if prob < best_prob:
				best_prob = prob
				best = tile

		c, r = best
		self._lastAction = AI.Action.UNCOVER
		self._lastX, self._lastY = c, r
		return Action(AI.Action.UNCOVER, c, r)
