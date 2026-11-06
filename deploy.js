const { ethers } = require("hardhat");

async function main() {
    console.log("🚀 جاري بدء نشر العقود على شبكة الاختبار (Sepolia)...");
    
    const [deployer] = await ethers.getSigners();
    console.log(`👤 الناشر: ${deployer.address}`);

    // 1. نشر العملة الوهمية
    console.log("⏳ جاري نشر العملة (Token)...");
    const Token = await ethers.getContractFactory("ERC20Mock");
    const token = await Token.deploy("Test Token", "TST", deployer.address, ethers.parseEther("20000000"));
    await token.waitForDeployment();
    const tokenAddress = await token.getAddress();
    console.log(`✅ تم نشر العملة على: ${tokenAddress}`);

    // 2. نشر عقد التوزيعات الضعيف (الاسم هنا تم تصحيحه)
    console.log("⏳ جاري نشر عقد التوزيعات (Airdrop)...");
    const Airdrop = await ethers.getContractFactory("VulnerableAirdrop"); 
    const airdrop = await Airdrop.deploy(tokenAddress);
    await airdrop.waitForDeployment();
    const airdropAddress = await airdrop.getAddress();
    console.log(`✅ تم نشر التوزيعات على: ${airdropAddress}`);
    
    // إعطاء عقد التوزيعات 10 ملايين توكن
    console.log("💸 جاري تحويل الأموال لعقد التوزيعات...");
    await (await token.transfer(airdropAddress, ethers.parseEther("10000000"))).wait();

    // 3. نشر منصة القروض الوهمية
    console.log("⏳ جاري نشر منصة القروض (Lender)...");
    const Lender = await ethers.getContractFactory("MockFlashLender");
    const lender = await Lender.deploy();
    await lender.waitForDeployment();
    const lenderAddress = await lender.getAddress();
    console.log(`✅ تم نشر منصة القروض على: ${lenderAddress}`);
    
    // إعطاء منصة القروض 5 ملايين توكن
    console.log("💸 جاري تحويل الأموال لمنصة القروض...");
    await (await token.transfer(lenderAddress, ethers.parseEther("5000000"))).wait();

    console.log("\n==================================================");
    console.log("🎯 انسخ العناوين التالية:");
    console.log(`TOKEN_ADDRESS="${tokenAddress}"`);
    console.log(`TARGET_ADDRESS="${airdropAddress}"`);
    console.log(`LENDER_ADDRESS="${lenderAddress}"`);
    console.log("==================================================\n");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});