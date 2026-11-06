const { ethers } = require("ethers");

async function main() {
    // 🌟 استخدام خادم PublicNode الثابت (لن ينقطع)
    const provider = new ethers.JsonRpcProvider("https://ethereum-sepolia-rpc.publicnode.com");
    
    // محفظتك (المفتاح الخاص)
    const wallet = new ethers.Wallet("f8ac8f25dccb4c605bdc4a8d2e1e3e333d9d3f48fbe283d360caaee4465a5c7b", provider);
    
    // 🎯 استخدام getAddress لضمان قبول العنوان مهما كانت حالة الحروف
    const tokenAddress = ethers.getAddress("0x1afdd7b775110a800bae2c836aadd85b260f77a2");
    
    const tokenABI = [
        "function balanceOf(address) view returns (uint256)",
        "function transfer(address to, uint256 amount) returns (bool)"
    ];
    
    const token = new ethers.Contract(tokenAddress, tokenABI, wallet);

    console.log("🔍 جاري الاتصال بالشبكة وقراءة الرصيد الحقيقي...");
    
    try {
        const balance = await token.balanceOf(wallet.address);
        console.log(`💰 رصيدك الحقيقي 100%: ${ethers.formatEther(balance)} TST`);

        if (balance === 0n) {
            console.log("❌ الرصيد صفر! تأكد من المحفظة.");
            return;
        }

        console.log("⏳ جاري إرسال 1000 توكن لمحفظة الحرق (لإجبار MetaMask على التحديث)...");
        // إجبار الشبكة على استخدام غاز كافٍ
        const tx = await token.transfer("0x000000000000000000000000000000000000dEaD", ethers.parseEther("1000"), { gasLimit: 100000 });
        
        console.log("في انتظار التأكيد...");
        await tx.wait();
        
        console.log("🎉 تم التحويل بنجاح!");
        console.log(`🔗 المعاملة: https://sepolia.etherscan.io/tx/${tx.hash}`);
        console.log("👉 اذهب الآن إلى MetaMask (تأكد أنك على شبكة Sepolia)، واضغط Refresh (سحب للأسفل).");
    } catch (error) {
        console.error("حدث خطأ أثناء الاتصال بالشبكة:", error.message);
    }
}

main();
