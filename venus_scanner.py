import asyncio
import aiohttp
from aiohttp import web
import os
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

# رابط NodeReal الخاص بك
RPC_URL = "https://bsc-mainnet.nodereal.io/v1/f0a6f89f70fc4d9eafc072f4f879bfdd"

VENUS_COMPTROLLER = "0xfD36E2c2a6789Db23113685031d7F16329158384"
VTOKEN_USDT = "0xfD5840Cd36d94D7229439859C0112a4185BC0255"

COMPTROLLER_ABI = [{"constant": True, "inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "getAccountLiquidity", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}, {"internalType": "uint256", "name": "", "type": "uint256"}, {"internalType": "uint256", "name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"}]
VTOKEN_ABI = [{"anonymous": False, "inputs": [{"indexed": False, "internalType": "address", "name": "borrower", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "borrowAmount", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "accountBorrows", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "totalBorrows", "type": "uint256"}], "name": "Borrow", "type": "event"}]

async def check_liquidity(w3, comptroller, wallet_address):
    try:
        result = await comptroller.functions.getAccountLiquidity(wallet_address).call()
        if result[0] == 0 and result[2] > 0:
            print(f"🚨🚨 [هدف ثمين] محفظة معرضة للتصفية: {wallet_address} | العجز: {result[2]}")
    except Exception:
        pass

async def bot_logic():
    print("📡 جاري الاتصال بشبكة BNB عبر NodeReal...")
    w3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))
    
    try:
        from web3.middleware import ExtraDataToPOAMiddleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except ImportError:
        from web3.middleware import async_geth_poa_middleware
        w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)

    comptroller = w3.eth.contract(address=w3.to_checksum_address(VENUS_COMPTROLLER), abi=COMPTROLLER_ABI)
    vtoken_usdt = w3.eth.contract(address=w3.to_checksum_address(VTOKEN_USDT), abi=VTOKEN_ABI)

    last_block = await w3.eth.block_number
    print(f"✅ البوت يعمل الآن! نبدأ المراقبة من البلوك: {last_block}")
    print("⏳ ننتظر عمليات الاقتراض الجديدة...")

    while True:
        try:
            current_block = await w3.eth.block_number
            if current_block > last_block:
                start_block = last_block + 1
                end_block = current_block
                try:
                    events = await vtoken_usdt.events.Borrow.get_logs(from_block=start_block, to_block=end_block)
                    if events:
                        print(f"🎯 تم العثور على {len(events)} عملية اقتراض في البلوك {end_block}!")
                        for event in events:
                            borrower = event['args']['borrower']
                            await check_liquidity(w3, comptroller, borrower)
                except Exception:
                    pass
                last_block = current_block
            await asyncio.sleep(1)
        except Exception as e:
            print(f"⚠️ خطأ في الشبكة: {e}")
            await asyncio.sleep(3)

# سيرفر الويب الوهمي لإرضاء Render وإبقاء البوت مستيقظاً
async def web_server():
    async def handle(request):
        return web.Response(text="Venus Liquidation Bot is running perfectly!")
    app = web.Application()
    app.router.add_get('/', handle)
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Web server started on port {port}")

async def main():
    await asyncio.gather(
        bot_logic(),
        web_server()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت يدوياً.")
