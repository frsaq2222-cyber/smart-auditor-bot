import asyncio
import aiohttp
from aiohttp import web
import html
import os
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

# ⚙️ الإعدادات الأساسية
TELEGRAM_TOKEN = "9275386025:AAGj8SrkdTDbWv-7aHq0ejg8NCe7zqdbVu4"
TELEGRAM_CHAT_ID = "1822828787"
BNB_RPC_URL = "https://special-rough-diagram.bsc.quiknode.pro/482d50162b6ecc13632015e58c3b50b8eaf16149/"

async def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ خطأ في إرسال التليجرام: {e}")

async def fetch_source_code(session, address):
    url = f"https://sourcify.dev/server/files/any/56/{address}"
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                source_code = ""
                contract_name = "Unknown"
                if isinstance(data, list):
                    for file in data:
                        if file.get("name", "").endswith(".sol"):
                            source_code += file.get("content", "") + "\n"
                            contract_name = file.get("name", "").split("/")[-1].replace(".sol", "")
                elif isinstance(data, dict) and "content" in data:
                    source_code = data.get("content", "")
                    contract_name = data.get("name", "").split("/")[-1].replace(".sol", "")
                if source_code:
                    return source_code, contract_name
    except Exception:
        pass
    return None, None

async def analyze_code(code, contract_name, address):
    red_flags = []
    if "getAmountsOut" in code or "getReserves" in code:
        red_flags.append("⚠️ يستخدم سعر فوري من DEX (Spot Price) - ثغرة أوراكل محتملة!")
    if "flashLoan" in code or "executeOperation" in code:
        red_flags.append("💰 يحتوي على وظيفة قروض سريعة (Flash Loan).")
    if ".call{value:" in code and "nonReentrant" not in code:
        red_flags.append("🚨 إرسال أموال (call) بدون حماية من إعادة الدخول (Reentrancy)!")
    if "setPrice" in code or "updatePrice" in code:
        red_flags.append("🔑 يحتوي على دالة لتحديث السعر يدوياً (Centralized Oracle)!")

    if red_flags:
        safe_name = html.escape(contract_name)
        safe_address = html.escape(address)
        report = f"🔍 <b>تقرير فحص العقد:</b> {safe_name}\n"
        report += f"📍 <code>{safe_address}</code>\n\n"
        report += "\n".join(red_flags)
        return report
    return None

async def bot_logic():
    w3 = AsyncWeb3(AsyncHTTPProvider(BNB_RPC_URL))
    try:
        from web3.middleware import ExtraDataToPOAMiddleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except ImportError:
        from web3.middleware import async_geth_poa_middleware
        w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)
    
    print("📡 بوت الفرز الأمني يعمل الآن ويراقب الشبكة عبر Sourcify...")
    last_block = await w3.eth.block_number

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                current_block = await w3.eth.block_number
                if current_block > last_block:
                    block = await w3.eth.get_block(current_block, full_transactions=True)
                    for tx in block.transactions:
                        if tx.get('to', None) is None: 
                            try:
                                receipt = await w3.eth.get_transaction_receipt(tx.hash)
                                address = receipt.get('contractAddress')
                                if address:
                                    print(f"⏳ جاري فحص عقد: {address}")
                                    source, name = await fetch_source_code(session, address)
                                    if source:
                                        print(f"🔎 تم جلب الكود من Sourcify: {name}")
                                        report = await analyze_code(source, name, address)
                                        if report:
                                            print(f"🔥 تم اكتشاف نقاط ضعف في {name}! إرسال التقرير...")
                                            await send_telegram(report)
                            except Exception:
                                continue 
                    last_block = current_block
                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"⚠️ خطأ في الشبكة: {e}")
                await asyncio.sleep(3)

async def web_server():
    async def handle(request):
        return web.Response(text="Bot is running perfectly!")
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
