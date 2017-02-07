

path = createPathToward(currentState, pos, dest, ant.movement)

for coord in path:
    ant = getAntAt(currentState, coord)
    if (coord == pos) continue;  //skip myself
    if ant is not None:
        options = listAllMovementPaths(currentState, pos, ant.movement)
        path = random.choice(options)
