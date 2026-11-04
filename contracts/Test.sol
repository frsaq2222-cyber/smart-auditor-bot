// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Test {
    mapping(address => uint256) public balances;

    function withdraw() public {
        uint256 balance = balances[msg.sender];
        require(balance > 0, "No balance");
        
        // ثغرة إعادة الدخول
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success, "Transfer failed");
        
        balances[msg.sender] = 0; 
    }
}