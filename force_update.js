const { ethers } = require("hardhat");

async function main() {
    const [attacker] = await ethers.getSigners();
    // العنوان بأحرف صغيرة لتجنب خطأ الـ checksum
    const TOKEN_ADDRESS = "0x1afdd7b775110a800bae2c836aadd85b260f77a2"; 
    const DEAD_ADDRESS = "0x000000000000000000000000000000000000dEaD";

    const token = await ethers.getContractAt("ERC20Mock", TOKEN_ADDRESS, attacker);
    
    // التأكد من الرصيد قبل التحويل
    const balance = await token.balanceOf(attacker.address);
    console.log(`💰 رصيدك قبل التحويل: ${ethers.formatEther(balance)} TST`);

    if (balance === 0n) {
        console.log("❌ الرصيد صفر! تأكد أنك على شبكة Sepolia.");
        return;
    }

    console.log("⏳ جاري تحويل 1000 توكن إلى محفظة حرق...");
    const tx = await token.transfer(DEAD_ADDRESS, ethers.parseEther("1000"));
    await tx.wait();
    console.log("✅ تم التحويل بنجاح!");
    console.log("الآن اذهب إلى MetaMask واضغط على Refresh (سحب للأسفل) وستجد الرصيد ظهر.");
}
main().catch((error) => console.error(error));
