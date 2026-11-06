const { ethers } = require("hardhat");

async function main() {
    // عنوان عقد المهاجم الناجح
    const BORROWER_ADDRESS = "0x245591fc2eDE86Cd949C1ab827444F140Ac1cb5f";
    // عنوان محفظتك
    const USER_WALLET = "0x71623be35A5f9BF91f767A2E8EA9Cc1F9018c595";

    console.log("🔍 جاري الاتصال بعقد المهاجم لقراءة الرصيد الحقيقي...");
    
    // الاتصال بعقد المهاجم
    const FlashBorrower = await ethers.getContractFactory("FlashBorrower");
    const borrower = FlashBorrower.attach(ethers.getAddress(BORROWER_ADDRESS.toLowerCase()));

    // قراءة عنوان العملة من داخل العقد
    const tokenAddress = await borrower.tokenAddress();
    console.log(`✅ عنوان العملة: ${tokenAddress}`);

    // استخدام عقد العملة الأصلي لقراءة الرصيد
    const Token = await ethers.getContractFactory("ERC20Mock");
    const token = Token.attach(tokenAddress);

    // قراءة الرصيد
    const balance = await token.balanceOf(USER_WALLET);
    
    console.log("==========================================");
    console.log(`💰 الرصيد الحقيقي 100% في محفظتك: ${ethers.formatEther(balance)} توكن`);
    console.log("==========================================");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
