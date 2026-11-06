require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.20",
  networks: {
    sepolia: {
      // خادم Tenderly: مستقر جداً، مؤسسي، ولا يتطلب مفاتيح
      url: "https://sepolia.gateway.tenderly.co", 
      accounts: ["0xf8ac8f25dccb4c605bdc4a8d2e1e3e333d9d3f48fbe283d360caaee4465a5c7b"]
    }
  }
};