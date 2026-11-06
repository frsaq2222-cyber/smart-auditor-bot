const { ethers } = require("hardhat");

async function main() {
    // عنوان عقد المهاجم الناجح
    const BORROWER_ADDRESS = "0x245591fc2eDE86Cd949C1ab827444F140Ac1cb5f"; 
    
    // الاتصال بالعقد
    const FlashBorrower = await ethers.getContractFactory("FlashBorrower");
    const borrower = FlashBorrower.attach(ethers.getAddress(BORROWER_ADDRESS.toLowerCase()));

    // قراءة عنوان العملة الصحيح من داخل العقد
    const tokenAddress = await borrower.tokenAddress();
    
    console.log("==========================================");
    console.log("✅ عنوان العملة الصحيح 100% هو:");
    console.log(`👉 ${tokenAddress}`);
    console.log("==========================================");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
