// SPDX-License-Identifier: unlicensed
pragma solidity >=0.4.25 <0.9.0;

contract RockPaperScissors {
    address payable player1;
    address payable player2;
    address payable owner;

    int p1Choice = -1;
    int p2Choice = -1;
    uint[3][3] public  payoffMatrix;

    constructor(address payable _player1, address payable _player2, address payable _owner) public {
        player1 = _player1;
        player2 = _player2;
        owner = _owner;

        // Rock - 0, Paper - 1, Scissors - 2
        payoffMatrix[0][0] = 0; // draw
        payoffMatrix[0][1] = 2; // player2 wins
        payoffMatrix[0][2] = 1; // player1 wins
        payoffMatrix[1][0] = 1;
        payoffMatrix[1][1] = 0;
        payoffMatrix[1][2] = 2;
        payoffMatrix[2][0] = 2;
        payoffMatrix[2][1] = 1;
        payoffMatrix[2][2] = 0;
    }

    function choicePlayer1(uint choice) public {
        require(msg.sender == player1);
        require(p1Choice == -1);
        // filter choice using modulo to be in the range of 0-2
        choice = choice % 3;
        int temp = int(choice);
        p1Choice = temp;
    }
    
    function choicePlayer2(uint choice) public {
        require(msg.sender == player2);
        require(p2Choice == -1);
        choice = choice % 3;
        int temp = int(choice);
        p2Choice = temp;
    }
    
    function determineWinner() public {
        require(p1Choice != -1 && p2Choice != -1);
        uint winner = payoffMatrix[uint(p1Choice)][uint(p2Choice)];
        if(winner == 1) {
            // player1.transfer(address(this).balance);
        }
        else if(winner == 2) {
            // player2.transfer(address(this).balance);
        }
        else {
            // owner.transfer(address(this).balance);
        }
    }
}