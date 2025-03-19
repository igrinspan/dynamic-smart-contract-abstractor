fileName = "CrowdfundingTesis.sol"
contractName = "Crowdfunding"
functions = [
"Donate();",
"GetFunds();",
"Claim();",
"t();"
]
statePreconditions = [
"(max_block > blockNumber)",
"(blockNumber > max_block && goal <= balance)",
"(blockNumber > max_block && !funded && goal > balance && countBackers > 0)",
"true"
]
functionPreconditions = [
"backers[msg.sender] == 0",
"msg.sender == owner",
"backers[msg.sender] != 0",
"true"
]
functionVariables = ""
tool_output = "Found a counterexample"

statesModeState = [[1,0,0,0,0], [0,2,0,0,0], [0,0,3,0,0], [0,0,0,4,0], [0,0,0,0,5]]
statesNamesModeState = ["Vacio sin balance", "Vacio con balance", "Donate", "Funds", "Claim"]
statePreconditionsModeState1 = [
"(!(max_block > blockNumber) && !(max_block < blockNumber && goal <= balance) && !(blockNumber > max_block && !funded && goal > balance && countBackers != 0) && balance == 0 && max_block < blockNumber)", 
"(!(max_block > blockNumber) && !(max_block < blockNumber && goal <= balance) && !(blockNumber > max_block && !funded && goal > balance && countBackers != 0) && balance > 0 && max_block < blockNumber)", 
"(max_block > blockNumber) && !(max_block < blockNumber && goal <= balance) && !(blockNumber > max_block && !funded && goal > balance && countBackers != 0)", 
"!(max_block > blockNumber) && (max_block < blockNumber && goal <= balance) && !(blockNumber > max_block && !funded && goal > balance && countBackers != 0)",
"!(max_block > blockNumber) && !(max_block < blockNumber && goal <= balance) && (blockNumber > max_block && !funded && goal > balance && countBackers != 0)",
]
statePreconditionsModeState = [
    "!(max_block > blockNumber) && !(max_block < blockNumber && goal <= balance) && !(max_block < blockNumber && !funded && goal > balance && countBackers > 0) && balance == 0",
    "!(max_block > blockNumber) && !(max_block < blockNumber && goal <= balance) && !(max_block < blockNumber && !funded && goal > balance && countBackers > 0) && balance > 0",
    "(max_block > blockNumber) && !(max_block < blockNumber && goal <= balance) && !(max_block < blockNumber && !funded && goal > balance && countBackers > 0)",
    "!(max_block > blockNumber) && (max_block < blockNumber && goal <= balance) && !(max_block < blockNumber && !funded && goal > balance && countBackers > 0)",
    "!(max_block > blockNumber) && !(max_block < blockNumber && goal <= balance) && (max_block < blockNumber && !funded && goal > balance && countBackers > 0)"
]

txBound = 10