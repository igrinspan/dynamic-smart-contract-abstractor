fileName = "RockPaperScissorsModulo.sol"
contractName = "RockPaperScissors"
functions = [
"choicePlayer1(choice);",
"choicePlayer2(choice);",
"determineWinner();",
]
statePreconditions = [
"p1Choice == -1",
"p2Choice == -1",
"p1Choice != -1 && p2Choice != -1",
]
functionPreconditions = [
"msg.sender == player1 && (choice >= 0 && choice <= 2)",
"msg.sender == player2 && (choice >= 0 && choice <= 2)",
"true",
]
functionVariables = "uint choice"
tool_output = "Found a counterexample"

statesModeState = [[1,0,0,0,0,0], [0,2,0,0,0,0], [0,0,3,0,0,0], [0,0,0,4,0,0], [0,0,0,0,5,0], [0,0,0,0,0,6]]
statesNamesModeState = ["Sin apuestas", "Solo apuesta 2", "Solo apuesta 1", "Apuestan ambos y gana 1", "Apuestan ambos y gana 2", "Apuestan ambos y gana Owner"]
statePreconditionsModeState = [
"p1Choice == -1 && p2Choice == -1", 
"p1Choice != -1 && p2Choice == -1", 
"p1Choice == -1 && p2Choice != -1", 
"p1Choice != -1 && p2Choice != -1 && payoffMatrix[uint(p1Choice)][uint(p2Choice)] == 1",
"p1Choice != -1 && p2Choice != -1 && payoffMatrix[uint(p1Choice)][uint(p2Choice)] == 2",
"p1Choice != -1 && p2Choice != -1 && payoffMatrix[uint(p1Choice)][uint(p2Choice)] == 0",
]
txBound = 6


# En modo States:
# - hay 6 estados posibles: 1, 2, 3, 4, 5, 6
# - Todos los estados son disjuntos.
# - Es decir, si se cumple la precondición de un estado, es imposible que se cumpla la precondición de otro estado.
