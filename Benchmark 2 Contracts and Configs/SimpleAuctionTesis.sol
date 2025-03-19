// SPDX-License-Identifier: GPL-3.0
// Es SimpleAuction pero sin los comentarios

pragma solidity >=0.4.25 <0.9.0;

contract SimpleAuction {    
    uint public auctionStart;
    uint public biddingTime;
    address payable beneficiary;

    // bool ended;
    address public highestBidder = address(0x0);
    uint public highestBid;
    mapping(address => uint) pendingReturns;
    uint pendingReturnsCount = 0;
    uint time;

    event HighestBidIncreased(address bidder, uint amount);
    event AuctionEnded(address winner, uint amount);
    
    address payable _beneficiary = payable(address(0xb23397f97715118532c8c1207F5678Ed4FbaEA6c));
    
    constructor(uint _time, uint _biddingTime, uint _auctionStart) public
    {
        auctionStart = _auctionStart;
        biddingTime = _biddingTime;
        beneficiary = _beneficiary;
        time = _time;
    }

    function bid() public payable {
        require(time >= auctionStart);
        require(time <= (auctionStart + biddingTime));
        require(msg.value > highestBid);

        if (highestBidder != address(0x0)) {
            if (pendingReturns[highestBidder] == 0){
                pendingReturnsCount += 1;
            }
            pendingReturns[highestBidder] += highestBid;
        }
        highestBidder = msg.sender;
        highestBid = msg.value;
        // t();
    }

    function withdraw() public returns (bool) {
        require(time >= auctionStart);
        require(pendingReturnsCount > 0);
        uint amount = pendingReturns[msg.sender];
        if (amount > 0) {
            pendingReturns[msg.sender] = 0;
            pendingReturnsCount = pendingReturnsCount - 1;
        }
        // t();
        return true;
    }

    function auctionEndTime() internal view returns (uint256) {
        return auctionStart + biddingTime;
    }
    
    function auctionEnd() public {
        require(time >= auctionStart);
        require(time > (auctionStart + biddingTime));
        // require(!ended);
        // ended = true;
        // t();
    }

    function t() public {
        time = time + 1;
    }
}
