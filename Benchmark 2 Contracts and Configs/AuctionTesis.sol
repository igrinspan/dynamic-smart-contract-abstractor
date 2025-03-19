pragma solidity >=0.4.25 <0.9.0;

// bugs:
// 1. Auction can never end
// 2. highest bidder can never be refunded their highest bid

contract Auction {
    uint auctionStart;
    uint biddingTime;
    address payable beneficiary;

    bool ended = false;
    address payable highestBidder = payable(address(0x0));
    address payable A = payable(address(0x0));
    uint highestBid = 0;
    mapping(address => uint) pendingReturns;
    uint pendingReturnsCount = 0;
    uint blockNumber;

    constructor(uint _auctionStart, uint _biddingTime, address payable _beneficiary,  uint _blockNumber) public {
        auctionStart = _auctionStart;
        biddingTime = _biddingTime;
        beneficiary = _beneficiary;
        blockNumber = _blockNumber;
    }

    function Bid() public payable {
        uint end = auctionStart + biddingTime;
        require(end >= blockNumber);
        require(!ended);
        require(msg.value > highestBid);

        if (highestBidder != address(0x0) && pendingReturns[highestBidder] == 0) {
            pendingReturnsCount += 1;
        }
        pendingReturns[highestBidder] += highestBid;
        highestBidder = payable(msg.sender);
        highestBid = msg.value;

        // t();
    }

    function Withdraw() public {
        require(pendingReturns[msg.sender] != 0 && pendingReturnsCount > 0);
        uint pr = pendingReturns[msg.sender];
        pendingReturns[msg.sender] = 0;
        pendingReturnsCount -= 1;
        payable(msg.sender).transfer(pr);  
        // t();
    }

    function AuctionEnd() public {
        uint end = auctionStart + biddingTime;
        require(blockNumber > end);
        require(ended); // ended is a bug (should be !ended)

        ended = true;
        beneficiary.transfer(highestBid);

        // t();
    }

    function t() public {
        blockNumber = blockNumber + 1;
    }
}