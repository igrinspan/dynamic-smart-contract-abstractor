fileName = "SimpleAuctionTesis.sol"
contractName = "SimpleAuction"
functions = [
    "bid();",
    "withdraw();",
    "auctionEnd();",
    "t();"
]
statePreconditions = [
    "time <= (auctionStart + biddingTime)",
    "pendingReturnsCount > 0",
    "time >= (auctionStart + biddingTime)",
    "true"
]
functionPreconditions = [
    "msg.value > highestBid",
    "true",
    "true",
    "true"
]
functionVariables = "address refundee"

# Para modo States:
statesModeState = [
    [1,0,0,0,0,0], 
    [0,2,0,0,0,0], 
    [0,0,3,0,0,0], 
    [0,0,0,4,0,0],
    [0,0,0,0,5,0],
    [0,0,0,0,0,6]
]
statesNamesModeState = [
    "En espera",
    "En curso, sin ofertas realizadas", 
    "Finalizada sin ofertas", 
    "En curso, con ofertas", 
    "Finalizada con ofertas (sin retiros pendientes)",
    "Finalizada con ofertas (con retiros pendientes)"
]
statePreconditionsModeState = [
    "highestBidder == address(0x0) && pendingReturnsCount == 0 && time < auctionStart && time <= (auctionStart + biddingTime)", 
    "highestBidder == address(0x0) && pendingReturnsCount == 0 && time >= auctionStart && time <= (auctionStart + biddingTime)", 
    "highestBidder == address(0x0) && pendingReturnsCount == 0 && time >= auctionStart && time > (auctionStart + biddingTime)", 
    "highestBidder != address(0x0) && time >= auctionStart && time <= (auctionStart + biddingTime)",
    "highestBidder != address(0x0) && time >= auctionStart && time > (auctionStart + biddingTime) && pendingReturnsCount == 0",
    "highestBidder != address(0x0) && time >= auctionStart && time > (auctionStart + biddingTime) && pendingReturnsCount != 0",

]