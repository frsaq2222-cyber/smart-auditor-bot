// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

interface IERC3156FlashBorrower {
    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external returns (bytes32);
}

contract MockFlashLender {
    uint256 public constant FEE = 0; // لا توجد رسوم في بيئة الاختبار المحلية

    // دالة إقراض وهمية تحاكي منصة حقيقية
    function flashLoan(
        IERC3156FlashBorrower receiver,
        address token,
        uint256 amount,
        bytes calldata data
    ) external returns (bool) {
        IERC20(token).transfer(address(receiver), amount);

        require(
            receiver.onFlashLoan(msg.sender, token, amount, FEE, data) ==
                keccak256("ERC3156FlashBorrower.onFlashLoan"),
            "Invalid callback return value"
        );

        // استرداد المبلغ (بدون فائدة)
        IERC20(token).transferFrom(address(receiver), address(this), amount + FEE);
        return true;
    }
}