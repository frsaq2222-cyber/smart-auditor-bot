import asyncio
import aiohttp
import os
from aiohttp import web

# ==========================================
# ⚙️ 1. الإعدادات الأساسية (قراءة آمنة من السيرفر)
# ==========================================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BNB_RPC_URL = os.getenv("BNB_RPC_URL", "https://bsc-dataseed.binance.org/")

# ==========================================
# 📱 2. دالة إرسال الرسائل إلى تليجرام
# ==========================================
async def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ خطأ: توكن التليجرام أو الآي دي غير موجود في المتغيرات!")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    print(f"⚠️ فشل إرسال رسالة التليجرام: {response.status}")
    except Exception as e:
        print(f"⚠️ خطأ في الاتصال بتليجرام: {e}")

# ==========================================
# 🔍 3. دالة جلب كود العقد الذكي (من Sourcify)
# ==========================================
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
                
                return source_code, contract_name
    except Exception as e:
        print(f"⚠️ خطأ أثناء جلب الكود للعقد {address}: {e}")
    
    return None, None

# ==========================================
# 🤖 4. الحلقة الرئيسية للبوت (المراقبة)
# ==========================================
async def bot_logic():
    print("🚀 بدء تشغيل بوت التدقيق (Advanced Bot v3)...")
    await send_telegram("✅ البوت يعمل الآن على السيرفر ويراقب الشبكة بنجاح.")
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # هنا تضع منطق البوت الخاص بك (مثلاً جلب العقود الجديدة وفحصها)
                # مجرد مثال بسيط لطباعة رسالة كل دقيقة
                print("🔍 جاري فحص العقود الجديدة...")
                await asyncio.sleep(60) # الانتظار 60 ثانية قبل الفحص مرة أخرى
                
            except Exception as e:
                print(f"⚠️ خطأ في الحلقة الرئيسية: {e}")
                await asyncio.sleep(10)

# ==========================================
# 🌐 5. سيرفر الويب (ضروري لكي تعمل خدمة Render مجاناً)
# ==========================================
async def web_server():
    async def handle(request):
        return web.Response(text="Advanced Auditor Bot v3 is running perfectly!")

    app = web.Application()
    app.router.add_get('/', handle)
    
    # Render يحدد المنفذ تلقائياً عبر المتغير PORT
    port = int(os.environ.get("PORT", 8080))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Web server started on port {port}")

# ==========================================
# ▶️ 6. نقطة البداية (تشغيل البوت والسيرفر معاً)
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
        print("\n🛑 تم إيقاف البوت يدوياً.")
