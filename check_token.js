const { ethers } = require("hardhat");

async function main() {
    console.log("🔍 جاري فحص العناوين الحقيقية للعقود...");

    // عنوان عقد المهاجم الناجح
    const BORROWER_ADDRESS = "0x245591fc2eDE86Cd949C1ab827444F140Ac1cb5f"; 
    
    const FlashBorrower = await ethers.getContractFactory("FlashBorrower");
    const borrower = FlashBorrower.attach(ethers.getAddress(BORROWER_ADDRESS.toLowerCase()));

    // قراءة عنوان العملة من داخل العقد
    const tokenAddress = await borrower.tokenAddress();
    const targetAddress = await borrower.airdropContract();

    console.log("==========================================");
    console.log("✅ عنوان العملة الحقيقي هو:");
    console.log(`👉 ${tokenAddress}`);
    console.log("==========================================");

    // فحص الرصيد الموجود فعلياً في محفظتك
    const [attacker] = await ethers.getSigners();
    const tokenContract = await ethers.getContractAt("ERC20Mock", tokenAddress, attacker);
    const balance = await tokenContract.balanceOf(attacker.address);

    console.log(`💰 رصيد محفظتك الحقيقي من هذا التوكن: ${ethers.formatEther(balance)} توكن`);
    console.log("==========================================");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
