pragma solidity >=0.4.25 <0.9.0;

contract Crowdfunding {
    address payable owner;
    uint max_block;
    uint goal;
    uint blockNumber;
    
    mapping ( address => uint ) backers;
    uint countBackers = 0;
    bool funded = false;
    uint balance = 0;

    constructor ( address payable _owner , uint _max_block , uint _goal, uint _blockNumber, uint _balance) public {
        owner = _owner;
        max_block = _max_block;
        goal = _goal;
        balance = _balance;
        blockNumber = _blockNumber;
    }

    function Donate () public payable {
        // max_block > blockNumber && backers [msg.sender] == 0
        require ( max_block > blockNumber);
        require ( backers [msg.sender] == 0);
        backers [msg.sender] = msg.value;
        countBackers += 1;
        balance = balance + msg.value;
    }

    function GetFunds () public {
        // max_block < blockNumber && goal <= balance && msg.sender == owner
        require (max_block < blockNumber);
        require (goal <= balance);
        require (msg.sender == owner);
        funded = true;
        balance = 0;
    }

    function Claim () public {
        // max_block < blockNumber && !funded && goal > balance && countBackers > 0 && backers [msg.sender] > 0
        require (max_block < blockNumber);
        require(!funded);
        require (goal > balance);
        require (countBackers > 0);
        require (backers[msg.sender] > 0);
        uint val = backers[msg.sender];
        backers[msg.sender] = 0;
        countBackers -= 1;
        balance = balance - val;
    }

    function t() public {
        blockNumber = blockNumber + 1;
    }
 }