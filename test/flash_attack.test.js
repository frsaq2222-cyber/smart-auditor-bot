const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("محاكاة الهجوم الحقيقي عبر عقد FlashBorrower", function () {
  it("يجب أن ينجح عقد المهاجم في استغلال التوزيعات وسداد القرض", async function () {
    const [owner, attacker] = await ethers.getSigners();

    // 1. نشر العملة الوهمية (Token)
    const Token = await ethers.getContractFactory("ERC20Mock");
    const token = await Token.deploy("Test Token", "TST", owner.address, ethers.parseEther("20000000"));
    await token.waitForDeployment();
    const tokenAddress = await token.getAddress();

    // 2. نشر عقد التوزيعات الضعيف (الهدف)
    const Airdrop = await ethers.getContractFactory("VulnerableAirdrop");
    const airdrop = await Airdrop.deploy(tokenAddress);
    await airdrop.waitForDeployment();
    const airdropAddress = await airdrop.getAddress();
    
    // إعطاء عقد التوزيعات 10 ملايين توكن
    await token.transfer(airdropAddress, ethers.parseEther("10000000"));

    // 3. نشر منصة القروض الوهمية (المقرض)
    const Lender = await ethers.getContractFactory("MockFlashLender");
    const lender = await Lender.deploy();
    await lender.waitForDeployment();
    const lenderAddress = await lender.getAddress();

    // إعطاء منصة القروض كمية ضخمة من التوكنات لتقرضها لنا
    await token.transfer(lenderAddress, ethers.parseEther("5000000"));

    // 4. نشر عقد المهاجم (FlashBorrower) باستخدام حساب المهاجم
    const Borrower = await ethers.getContractFactory("FlashBorrower");
    // 🎯 التعديل هنا: أضفنا .connect(attacker)
    const borrower = await Borrower.connect(attacker).deploy(lenderAddress, airdropAddress, tokenAddress);
    await borrower.waitForDeployment();
    const borrowerAddress = await borrower.getAddress();

    console.log("\n--- 🛡️ بدء عملية الهجوم ---");
    console.log("💰 رصيد عقد التوزيعات قبل الهجوم:", ethers.formatEther(await token.balanceOf(airdropAddress)));

    // 5. تنفيذ الهجوم!
    console.log("⚔️ عقد المهاجم يطلب قرضاً وميضياً بقيمة 500,000 توكن...");
    await borrower.connect(attacker).executeAttack(ethers.parseEther("500000"));

    // 6. التحقق من النتيجة
    const borrowerFinalBalance = await token.balanceOf(borrowerAddress);
    const lenderFinalBalance = await token.balanceOf(lenderAddress);
    
    console.log("\n--- 🏁 النتيجة بعد انتهاء المعاملة ---");
    console.log("✅ رصيد منصة القروض (يجب أن يكون 5 مليون كما كان):", ethers.formatEther(lenderFinalBalance));
    console.log("🔥 رصيد عقد المهاجم (الربح الصافي!):", ethers.formatEther(borrowerFinalBalance));

    expect(borrowerFinalBalance).to.be.greaterThan(0);
    console.log("🚨 نجح عقد المهاجم في سحب المكافآت وسداد القرض في نفس اللحظة.");
  });
});