fileName = "FrequentFlyerRewardsCalculator.sol"
contractName = "FrequentFlyerRewardsCalculator"
functions = ["AddMiles(miles);",
             "GetMiles();"]

statePreconditions = ["true",
                      "true"]
functionPreconditions = ["msg.sender == Flyer",
                         "true"]

functionVariables = "int[] memory miles"
tool_output = "Found a counterexample"

statesModeState = [[1,0], [0,2]]
statesNamesModeState = ["SetFlyerAndReward", "MilesAdded"]
statePreconditionsModeState = ["State == StateType.SetFlyerAndReward", "State == StateType.MilesAdded"]
txBound = 4