// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
}

contract VulnerableAirdrop {
    IERC20 public token;
    uint256 public rewardRate = 10; // كل توكن يمنحك 10 توكنات مكافأة

    constructor(address _token) {
        token = IERC20(_token);
    }

    // 🚨 الثغرة هنا: نحسب المكافأة بناءً على رصيدك "الآن" وليس بناءً على لقطة سابقة
    function claimReward() external {
        uint256 userBalance = token.balanceOf(msg.sender);
        require(userBalance > 0, "You don't hold any tokens");
        
        uint256 reward = userBalance * rewardRate;
        require(token.transfer(msg.sender, reward), "Transfer failed");
    }
}