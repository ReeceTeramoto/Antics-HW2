import random
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *

##
#getFoodCost
#
#Description: Given a list of ants, get the cost of food to
# make all of those ants
#
#Parameters:
#   antList - the list of ants
#
#Return: cost - the food cost to make them
##
def getFoodCost(antList):
    cost = 0

    # food costs for the different ants
    workerCost = 1
    droneCost = 2
    soldierCost = 3
    rangedSoldierCost = 4

    # add each ant's food cost
    for ant in antList:
        if ant.type == QUEEN:
            continue
        if ant.type == WORKER:
            cost += workerCost
        if ant.type == DRONE:
            cost += droneCost
        if ant.type == SOLDIER:
            cost += soldierCost
        if ant.type == R_SOLDIER:
            cost += rangedSoldierCost

    return cost

##
#getStateValue
#
#Description: Given a state, determines a double value between 0.0 and 1.0.
#   Less than 0.5 means the agent is losing, greater than 0.5 means the
#   agent is winning. 0.5 means that nobody is winning or losing.
#
#Parameters:
#   state - the state of the game
#
#Return: The value of the state
##
def getStateValue(self, currentState):
    # start off at an even state
    rtn = 0.5
    weight = 0.125

    myId = self.playerId
    otherId = 0
    if myId == 1:
        otherId = 0
    if myId == 0:
        otherId = 1
    
    # Idea: find the differences in queen health, anthill health, food,
    # and antFoodCost (cost of food used to produce all of the ants
    # on a player's side.
    # Each of these is divided by the total to get a fraction,
    # multiplied by 0.125, then added to the rtn value.
    # Note that a negative difference will subtract.

    # get both players' queens
    myInv = getCurrPlayerInventory(currentState)
    myQueen = myInv.getQueen()
    myQueenHealth = myQueen.health
    otherQueen= getAntList(currentState, otherId, [QUEEN])[0]
    otherQueenHealth = otherQueen.health

    # if one queen is dead, that player loses
    if myQueenHealth == 0:
        return 0
    if otherQueenHealth == 0:
        return 1

    # from the queen health difference, change the score of the state
    queenHealthDiff = myQueenHealth - otherQueenHealth
    queenHealthTotal = myQueenHealth + otherQueenHealth
    rtn += weight * queenHealthDiff / queenHealthTotal

    # get both players' anthills
    myAnthill = getConstrList(currentState, myId, [ANTHILL])[0]
    otherAnthill = getConstrList(currentState, otherId, [ANTHILL])[0]
    anthillHealthDiff = myAnthill.captureHealth - otherAnthill.captureHealth
    anthillHealthTotal = myAnthill.captureHealth + otherAnthill.captureHealth

    # if one anthill is dead, that player loses
    if myAnthill.captureHealth == 0:
        return 0
    if otherAnthill.captureHealth == 0:
        return 1

    # anthill health difference changes the score of the state
    rtn += weight * anthillHealthDiff / anthillHealthTotal

    # get the food difference
    myGameState = currentState.fastclone()
    myFood = myGameState.inventories[myId].foodCount
    otherFood = myGameState.inventories[otherId].foodCount
    foodDiff = myFood - otherFood
    foodTotal = myFood + otherFood

    # if one person has 11 food, that person wins
    if myFood == 11:
        return 1
    if otherFood == 11:
        return 0

    # the food difference affects the score of the state
    if foodTotal != 0:
        rtn += weight * foodDiff / foodTotal

    # get the food cost difference (food cost of all my ants)
    myAnts = getAntList(currentState, myId, [QUEEN, WORKER, DRONE, SOLDIER, R_SOLDIER])
    otherAnts = getAntList(currentState, otherId, [QUEEN, WORKER, DRONE, SOLDIER, R_SOLDIER])

    # find the total food cost of my ants (queens don't count)
    myAntsCost = getFoodCost(myAnts)
    otherAntsCost= getFoodCost(otherAnts)
    antsFoodCostDiff = myAntsCost - otherAntsCost
    antsFoodCostTotal = myAntsCost + otherAntsCost

    # the ants' food cost difference affects the score of the state
    if antsFoodCostTotal != 0:
        rtn += weight * antsFoodCostDiff / antsFoodCostTotal

    return rtn


##
#Node
#Description: Creates a class that will represent a node in the
#   search tree. The node references the parent node. A move that
#   can be taken from the parent node. The state of the game after
#   the move is finished. The value of the state that was just reached.
#
##
class Node(object):
    def __init__(self, newMove = None, newState = None, newParent = None, newVal = None):
        self.move = newMove
        self.state = newState
        self.parent = newParent
        self.val = newVal

    def __str__(self):
        return str(self.move)
    
##
#findOverallScore
#Description: called to evaluate the score of a list of nodes.
#
#Parameters:
#   nodeList - The list of nodes down a ceratin path
##
def findOverallScore(nodeList):
    #iterate through the list
    #take the nodes value from getStateValue
    #average the scores of all the nodes
    total = 0
    for node in nodeList:
        sub = total
        score = node.val
        total = score + sub
    avg = (total)/(len(nodeList))
    return avg

##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "Ohta_Teramoto AI")
        

    ##
    #searchTree
    #
    #Description: Given a state and the current depth, get all possible moves and states that result
    # from each move. Assess the overall value of each list of nodes.
    #
    #Parameters:
    #   state - a GameState object
    #   depth - the current depth
    #   depthLim - the depth limit that determines when we stop searching into the future
    #   node - the current node being passed down
    #
    #Return: The overall value of the entire list of nodes
    ##
    def searchTree(self, state, depth, depthLim, node = None):
        # generate a list of all possible moves that could be made from the given state
        allMoves = listAllLegalMoves(state)

        if node is None:
            node = Node()

        # discard the END_TURN move
        endTurnMove = Move(END, None, None)
        if endTurnMove in allMoves:
            allMoves.remove(endTurnMove)

        # generate a list of GameState objects that will result from making each move
        allChildren = []
        for move in allMoves:
            newState = getNextState(state, move)
            newStateVal = getStateValue(self, state)
            newNode = Node(move, newState, node, newStateVal)
            allChildren.append(newNode)

        # recursive case: if the depth limit has not been reached, make a recursive
        # call for each state in the list and use the result of the call as the new value
        # for this node
        if depth < depthLim:
            for child in allChildren:
                child.val = self.searchTree(child.state, depth + 1, depthLim)

        # assess overall value of entire list of nodes
        overallVal = findOverallScore(allChildren)
        print "overall val: " + str(overallVal)

        # return the overall value if depth > 0
        if depth > 0:
            return overallVal
        # otherwise, return the Move object from the node that has the
        # highest evaluation score
        else:
            allEvalScores = [child.val for child in allChildren]
            idxOfHighestScore = allEvalScores.index(max(allEvalScores))
            return allChildren[idxOfHighestScore].move
        
    ##
    #getPlacement
    #
    #Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    #Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        numToPlace = 0
        #implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:    #stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:   #stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]
    
    ##
    #getMove
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The Move to be made
    ##
    def getMove(self, currentState):
        
        depthLim = 2
        return self.searchTree(currentState, 0, depthLim)
        '''
        moves = listAllLegalMoves(currentState)
        selectedMove = moves[random.randint(0,len(moves) - 1)];

        print "current game state value: " + str(getStateValue(self, currentState))

        #don't do a build move if there are already 3+ ants
        numAnts = len(currentState.inventories[currentState.whoseTurn].ants)
        while (selectedMove.moveType == BUILD and numAnts >= 3):
            selectedMove = moves[random.randint(0,len(moves) - 1)];
            
        return selectedMove
        '''
    
    ##
    #getAttack
    #Description: Gets the attack to be made from the Player
    #
    #Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        #Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]
    
#Unittesting

#Player IDs
testID = AIPlayer(1)
testID2 = AIPlayer(0)
#creation of certain ants
ant1 = Ant((0,0), WORKER, testID)
ant2 = Ant((0,1), QUEEN, testID)
ant3 = Ant((0,9), WORKER, testID2)
ant4 = Ant((0,8), QUEEN, testID2)
#3 inventories needed for a game state
testInv = Inventory(testID, [ant1, ant2], 0, 0)
testInv2 = Inventory(testID2, [ant3, ant4], 0, 0)
testInv3 = Inventory(0,0,0,0)
#game states
state1 = GameState(0, (testInv, testInv2, testInv3), 0, testID)
#Tests to see if getFoodCost gives a value of 1 for a worker ant
antList = getAntList(state1, testID, [WORKER])
if(getFoodCost(antList) != 1):
    print("getFoodCost is not working")
    

#testing to see if findOverallScore finds the average score
node1 = Node(0,0,0,0.5)
node2 = Node(0,0,0,0.7)
nodeList = (node1, node2)
if(findOverallScore(nodeList) != 0.6):
    print("findOverallScore does not work")    
