# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Justin Chung
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


class MyAI( AI ):

	def __init__(self, rowDimension, colDimension, totalMines, startX, startY):

		########################################################################
		#							YOUR CODE BEGINS						   #
		########################################################################
		pass
		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################

		
	def getAction(self, number: int) -> "Action Object":

		########################################################################
		#							YOUR CODE BEGINS						   #
		########################################################################
		return Action(AI.Action.LEAVE)
		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################

    # Helper function: run constraint logic and fill self._queue with deduced moves 
    def _findMoves(self):
		"""
		Iteratively scan every uncovered numbered tile and apply two rules:

		Rule A (safe):  hint - flagged_neighbors == 0
		                → every remaining covered unflagged neighbor is SAFE

		Rule B (mine):  hint - flagged_neighbors == covered_unflagged_count
		                → every covered unflagged neighbor is a MINE

		Loop until no new tiles are identified so that chained deductions
		(flagging a mine reveals a new safe tile on the next pass) are caught
		within a single call.
		"""
		safeTiles  = set()   # tiles are certain are safe to uncover
		mineTiles  = set()   # tiles are certain contain a mine

		changed = True
		while changed:
			changed = False
			for c in range(self._colDimension):
				for r in range(self._rowDimension):
					cell = self._board[c][r]

					# Only process uncovered tiles that have a hint number
					if cell['covered'] or cell['number'] < 0:
						continue

					neighbors = self._getNeighbors(c, r)

					# Covered unflagged neighbors (unknown tiles)
					# Treat tiles already in mineTiles as flagged for counting
					coveredUnflagged = [
						n for n in neighbors
						if self._board[n[0]][n[1]]['covered']
						and not self._board[n[0]][n[1]]['flagged']
						and n not in mineTiles
					]

					# Flagged neighbors + tiles already know are mines
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

		# Queue FLAG actions first (safer to mark mines before uncovering)
		for (c, r) in mineTiles:
			if not self._board[c][r]['flagged']:
				self._queue.append((AI.Action.FLAG, c, r))

		# Then queue UNCOVER actions for safe tiles
		for (c, r) in safeTiles:
			if self._board[c][r]['covered'] and not self._board[c][r]['flagged']:
				self._queue.append((AI.Action.UNCOVER, c, r))

    # Helper function: return all valid (col, row) neighbors of a given title 
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

    # Helper function: pop the next queue action and record it for the next update 
    def _executeNext(self):
		actionType, x, y = self._queue.popleft()
		self._lastAction = actionType
		self._lastX      = x
		self._lastY      = y
		return Action(actionType, x, y)

    # Helper function: when no logical move exist, uncover any cover unflagged tile
    def _guess(self):
		for c in range(self._colDimension):
			for r in range(self._rowDimension):
				if self._board[c][r]['covered'] and not self._board[c][r]['flagged']:
					self._lastAction = AI.Action.UNCOVER
					self._lastX      = c
					self._lastY      = r
					return Action(AI.Action.UNCOVER, c, r)

		# No covered tiles remain —> the game should have ended already
		return Action(AI.Action.LEAVE)
    