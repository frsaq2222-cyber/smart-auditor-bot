import asyncio
import os
import aiohttp
from aiohttp import web
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

# ==========================================
# ⚙️ 1. الإعدادات الأساسية
# ==========================================
RPC_URL = os.getenv("BNB_RPC_URL", "https://bsc-dataseed.binance.org/")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# عناوين بروتوكول Venus (BSC Mainnet)
VENUS_COMPTROLLER = "0xfD36E2c2a6789Db23113685031d7F16329158384"
POOL_LENS = "0x4912c6d8cA7f7F8cA3c7A5d5A5A5A5A5A5A5A5A5" # عنوان تجريبي (يجب استبداله بالعنوان الحقيقي)
# قائمة بالـ vTokens (مثال: vUSDT, vUSDC, vBUSD)
VTOKENS = [
    "0xfD5840Cd36d94D7229439859C0112a4185BC0255", # vUSDT
    "0xeca88125a5adbe82614ffc12d0db554e2e2867c8", # vUSDC
]

# ABI المبسط لـ PoolLens (vTokenBalancesAll)
POOL_LENS_ABI = [{"constant": True, "inputs": [{"internalType": "address[]", "name": "vTokens", "type": "address[]"}, {"internalType": "address", "name": "account", "type": "address"}], "name": "vTokenBalancesAll", "outputs": [{"internalType": "uint256[]", "name": "", "type": "uint256[]"}], "payable": False, "stateMutability": "view", "type": "function"}]

# ==========================================
# 📱 2. دالة إرسال التليجرام
# ==========================================
async def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(url, json=payload)
    except Exception as e:
        print(f"⚠️ فشل إرسال التليجرام: {e}")

# ==========================================
# 🔍 3. دالة فحص الحساب
# ==========================================
async def check_account_health(w3, account_address):
    """يفحص صحة الحساب باستخدام PoolLens"""
    try:
        pool_lens = w3.eth.contract(address=w3.to_checksum_address(POOL_LENS), abi=POOL_LENS_ABI)
        # جلب أرصدة الـ vTokens للحساب
        balances = await pool_lens.functions.vTokenBalancesAll(VTOKENS, account_address).call()
        
        # منطق مبسط: إذا كانت جميع الأرصدة صفراً، فتجاهل الحساب
        if all(b == 0 for b in balances):
            return
            
        # في الواقع، تحتاج إلى جلب الأسعار وحساب السيولة بدقة
        # هذا مجرد هيكل للتوضيح
        print(f"🔍 فحص الحساب: {account_address} | الأرصدة: {balances}")
        
        # إذا اكتشفت أن الحساب غير صحي (نقص سيولة > 0)
        # يمكنك إرسال إشعار
        # await send_telegram(f"🚨 حساب معرض للتصفية: {account_address}")
        
    except Exception as e:
        print(f"⚠️ خطأ في فحص الحساب: {e}")

# ==========================================
# 🚀 4. الحلقة الرئيسية
# ==========================================
async def bot_logic():
    print("📡 جاري الاتصال بشبكة BNB...")
    w3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))
    
    try:
        from web3.middleware import ExtraDataToPOAMiddleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except ImportError:
        from web3.middleware import async_geth_poa_middleware
        w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)

    print("✅ البوت يعمل الآن! جاري مراقبة الحسابات...")
    await send_telegram("✅ <b>بوت التصفية (الاحترافي)</b> يعمل الآن ويراقب الحسابات غير الصحية...")

    # الحصول على قائمة الحسابات (في الواقع، يجب أن تأتي من الأحداث)
    # هنا نستخدم حساباً وهمياً للتجربة
    test_account = "0x0000000000000000000000000000000000000000" # عنوان فارغ للتجربة
    
    while True:
        try:
            # فحص الحساب
            await check_account_health(w3, test_account)
            
            # انتظار قبل الفحص التالي
            await asyncio.sleep(10) # فحص كل 10 ثوانٍ (يمكنك تعديله)

        except Exception as e:
            print(f"⚠️ خطأ في الحلقة الرئيسية: {e}")
            await asyncio.sleep(5)

# ==========================================
# 🌐 5. سيرفر الويب
# ==========================================
async def web_server():
    async def handle(request):
        return web.Response(text="Venus Liquidation Bot (Pro) is running perfectly!")

    app = web.Application()
    app.router.add_get('/', handle)
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Web server started on port {port}")

# ==========================================
# ▶️ 6. نقطة البداية
# ==========================================
async def main():
    await asyncio.gather(
        bot_logic(),
        web_server()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass