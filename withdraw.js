const { ethers } = require("hardhat");

async function main() {
    console.log("جاري سحب الأرباح...");
    const [attacker] = await ethers.getSigners();
    console.log(`محفظتك: ${attacker.address}`);

    // عنوان عقد المهاجم الناجح
    const BORROWER_ADDRESS = "0x245591fc2eDE86Cd949C1ab827444F140Ac1cb5f"; 

    const FlashBorrower = await ethers.getContractFactory("FlashBorrower");
    // تنظيف العنوان من أي أخطاء تنسيق
    const safeBorrowerAddress = ethers.getAddress(BORROWER_ADDRESS.toLowerCase());
    const borrower = FlashBorrower.attach(safeBorrowerAddress);

    // جلب عنوان العملة مباشرة من داخل العقد (بدون نسخ ولصق)
    const tokenAddress = await borrower.tokenAddress();
    console.log(`عنوان العملة المكتشف: ${tokenAddress}`);

    console.log("في انتظار تأكيد المعاملة...");
    const tx = await borrower.withdrawProfit(tokenAddress);
    await tx.wait();

    console.log("تم سحب الأرباح بنجاح!");

    // التحقق من رصيدك الجديد
    const tokenContract = await ethers.getContractAt("ERC20Mock", tokenAddress, attacker);
    const balance = await tokenContract.balanceOf(attacker.address);
    console.log(`رصيدك في المحفظة الآن: ${ethers.formatEther(balance)} توكن`);
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
