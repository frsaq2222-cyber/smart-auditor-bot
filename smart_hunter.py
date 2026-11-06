import asyncio
import aiohttp
import os
import re
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware # 🎯 إضافة مهمة لشبكة BSC

# ==========================================
# ⚙️ 1. إعدادات الشبكات والمفاتيح
# ==========================================
NETWORKS = {
    "BSC": {
        "rpc": "https://bsc-rpc.publicnode.com",
        "api_url": "https://api.bscscan.com/api",
        "api_key": os.getenv("BSCSCAN_API_KEY", "2RNPCUD5UHI78SMH5EBWZRACFX4J8U9WBI")
    },
    "BASE": {
        "rpc": "https://base-rpc.publicnode.com",
        "api_url": "https://api.basescan.org/api",
        "api_key": os.getenv("BASESCAN_API_KEY", "2RNPCUD5UHI78SMH5EBWZRACFX4J8U9WBI") 
    },
    "ETH": {
        "rpc": "https://ethereum-rpc.publicnode.com",
        "api_url": "https://api.etherscan.io/api",
        "api_key": os.getenv("ETHERSCAN_API_KEY", "2RNPCUD5UHI78SMH5EBWZRACFX4J8U9WBI")
    }
}

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "9275386025:AAGj8SrkdTDbWv-7aHq0ejg8NCe7zqdbVu4")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1822828787")

# ==========================================
# 📱 2. إرسال الإشعارات
# ==========================================
async def send_telegram(session, message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        await session.post(url, json=payload)
    except Exception:
        pass

# ==========================================
# 🛡️ 3. فحص الثغرات
# ==========================================
async def check_vulnerability(session, contract_address, network_name, config):
    source_code = ""
    contract_name = "Unknown"
    
    # 1. محاولة جلب الكود من Sourcify
    try:
        sourcify_url = f"https://sourcify.dev/server/files/any/{contract_address}"
        async with session.get(sourcify_url, timeout=5) as resp:
            if resp.status == 200:
                data = await resp.json()
                if isinstance(data, list):
                    for file in data:
                        if file.get("name", "").endswith(".sol"):
                            source_code += file.get("content", "") + "\n"
                            contract_name = file.get("name", "").split("/")[-1].replace(".sol", "")
    except Exception:
        pass

    # 2. إذا فشل Sourcify، استخدم مستكشف الكتل
    if not source_code:
        try:
            api_url = f"{config['api_url']}?module=contract&action=getsourcecode&address={contract_address}&apikey={config['api_key']}"
            async with session.get(api_url, timeout=10) as resp:
                data = await resp.json()
                if data.get("status") == "1" and data["result"][0]["SourceCode"] != "":
                    source_code = data["result"][0]["SourceCode"]
                    contract_name = data["result"][0]["ContractName"]
        except Exception:
            pass

    if not source_code:
        return False

    # 3. الأنماط الموسعة
    vuln_patterns = [
        r"function\s+(claim|reward|distribute|extract|harvest|release)\w*\s*\([^)]*\)[^{]*\{[^}]*?(balanceOf|totalSupply|getReserves)\s*\([^)]*\).*?\}",
        r"function\s+extractReward\s*\([^)]*\)[^{]*\{[^}]*?balanceOf.*?\}",
        r"function\s+burnToHolder\s*\([^)]*\)[^{]*\{[^}]*?(balanceOf|totalSupply).*?\}",
        r"function\s+releasePayment\s*\([^)]*\)[^{]*\{[^}]*?(balanceOf|totalSupply).*?\}",
        r"function\s+(stake|deposit|withdraw)\s*\([^)]*\)[^{]*\{[^}]*?balanceOf.*?\}"
    ]

    for pattern in vuln_patterns:
        matches = re.finditer(pattern, source_code, re.DOTALL | re.IGNORECASE)
        for match in matches:
            function_code = match.group(0)
            if not any(safe in function_code.lower() for safe in ["snapshot", "merkle", "timelock", "lockup", "lastclaim"]):
                msg = f"🚨 <b>تم اكتشاف ثغرة محتملة!</b>\n\n"
                msg += f"🌐 <b>الشبكة:</b> {network_name}\n"
                msg += f"📜 <b>اسم العقد:</b> {contract_name}\n"
                msg += f"🔗 <b>العنوان:</b> <code>{contract_address}</code>\n"
                msg += f"⚙️ <b>الدالة المصابة:</b> <code>{match.group(1)}</code>\n"
                explorer = "bscscan.com" if network_name == "BSC" else ("basescan.org" if network_name == "BASE" else "etherscan.io")
                msg += f"🔍 <a href='https://{explorer}/address/{contract_address}#code'>رابط الكود</a>"
                
                await send_telegram(session, msg)
                print(f"\n🚨 [{network_name}] اصطياد: {contract_address} ({contract_name})")
                return True
    
    return False

# ==========================================
# 🦅 4. حلقة المراقبة لكل شبكة
# ==========================================
async def monitor_network(network_name, config):
    w3 = AsyncWeb3(AsyncHTTPProvider(config["rpc"]))
    
    # 🎯 إضافة دعم شبكات PoA مثل BSC
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    print(f"🦅 بدء المراقبة على شبكة: {network_name} ...")
    
    async with aiohttp.ClientSession() as session:
        await send_telegram(session, f"✅ <b>بوت الصيد يعمل الآن على {network_name}!</b>")
        
        last_block = await w3.eth.block_number
        while True:
            try:
                current_block = await w3.eth.block_number
                if current_block > last_block:
                    block = await w3.eth.get_block(current_block, full_transactions=True)
                    for tx in block.transactions:
                        if tx.to is None:
                            receipt = await w3.eth.get_transaction_receipt(tx.hash)
                            contract_address = receipt.contractAddress
                            if contract_address:
                                await check_vulnerability(session, contract_address, network_name, config)
                                await asyncio.sleep(1) 
                    last_block = current_block
                await asyncio.sleep(3)
            except Exception as e:
                print(f"⚠️ خطأ في {network_name}: {e}")
                await asyncio.sleep(5)

# ==========================================
# 🌐 5. سيرفر الويب الصامت
# ==========================================
async def web_server():
    from aiohttp import web
    async def handle(request):
        return web.Response(text="Multi-Chain Hunter Bot is running!")
    app = web.Application()
    app.router.add_get('/', handle)
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    tasks = [monitor_network(name, cfg) for name, cfg in NETWORKS.items()]
    tasks.append(web_server())
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass