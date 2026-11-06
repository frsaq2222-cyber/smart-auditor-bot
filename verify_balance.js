const { ethers } = require("hardhat");

async function main() {
    // عنوان محفظتك
    const USER_WALLET = "0x71623be35A5f9BF91f767A2E8EA9Cc1F9018c595";
    // تنظيف العنوان من أي أخطاء في الحروف الكبيرة والصغيرة
    const TOKEN_ADDRESS_RAW = "0x1afdd7b775110a800bae2c836aadd85b260f77a2";
    const TOKEN_ADDRESS = ethers.getAddress(TOKEN_ADDRESS_RAW);

    const minimalABI = ["function balanceOf(address owner) view returns (uint256)"];
    const token = new ethers.Contract(TOKEN_ADDRESS, minimalABI, ethers.provider);

    console.log("🔍 جاري سؤال شبكة البلوكشين مباشرة عن رصيدك...");
    
    const balance = await token.balanceOf(USER_WALLET);
    
    console.log("==========================================");
    console.log(`💰 الرصيد الحقيقي في محفظتك هو: ${ethers.formatEther(balance)} توكن`);
    console.log("==========================================");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
