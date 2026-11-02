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

def extract_vulnerable_function(code, keyword):
    """خوارزمية لقص الدالة المصابة بالكامل"""
    idx = code.find(keyword)
    if idx == -1:
        return None

    # البحث للخلف عن بداية الدالة أو الموديفاير
    start_idx = -1
    for func_type in ['function', 'constructor', 'receive', 'fallback', 'modifier']:
        temp_idx = code.rfind(func_type, 0, idx)
        if temp_idx > start_idx:
            start_idx = temp_idx

    if start_idx == -1:
        return code[max(0, idx-100):min(len(code), idx+300)] # إرجاع سياق قريب إذا لم يجد

    # البحث عن القوس الأول '{'
    open_brace = code.find('{', start_idx)
    if open_brace == -1:
        return None

    # مطابقة الأقواس للعثور على نهاية الدالة بدقة
    brace_count = 1
    end_idx = open_brace + 1
    while end_idx < len(code) and brace_count > 0:
        if code[end_idx] == '{':
            brace_count += 1
        elif code[end_idx] == '}':
            brace_count -= 1
        end_idx += 1

    extracted_code = code[start_idx:end_idx].strip()
    
    # تليجرام له حد أقصى للرسالة، نقص الكود إذا كان ضخماً جداً
    if len(extracted_code) > 3500:
        extracted_code = extracted_code[:3500] + "\n... [تم قص الكود لطوله]"
        
    return extracted_code

async def analyze_code(code, contract_name, address):
    red_flags = []
    snippets = []

    # القاموس الشامل للثغرات (Pattern : Description)
    patterns = {
        "flashLoan": "💰 قروض سريعة (Flash Loan)",
        "executeOperation": "💰 دالة تنفيذ القرض السريع",
        "getAmountsOut": "⚠️ أوراكل ضعيف (DEX Spot Price)",
        "getReserves": "⚠️ قراءة احتياطي DEX (Oracle)",
        "slot0": "⚠️ قراءة سعر Uniswap V3",
        ".call{value:": "🚨 إرسال أموال بدون حماية (Reentrancy)",
        "delegatecall": "🚨 استدعاء خارجي خطير (Delegatecall)",
        "setTax": "🔑 تعديل الضرائب (قد يكون Honeypot)",
        "updateTax": "🔑 تعديل الضرائب (قد يكون Honeypot)",
        "blacklist": "🔑 حظر محافظ (Blacklist)",
        "setMaxTxAmount": "🔑 تحديد حد أقصى للمعاملات",
        "emergencyWithdraw": "🔑 سحب طارئ (قد يكون Scam)",
        "mint(": "🪙 سك عملات جديدة (Mint)",
        "block.timestamp": "🎲 عشوائية ضعيفة (يمكن التلاعب بها)"
    }

    for key, desc in patterns.items():
        if key in code:
            # استثناء بسيط: إذا كان هناك حماية Reentrancy، لا نعتبر .call ثغرة
            if key in [".call{value:", "delegatecall"] and "nonReentrant" in code:
                continue
            
            red_flags.append(desc)
            snippet = extract_vulnerable_function(code, key)
            if snippet:
                snippets.append((key, snippet))

    if red_flags:
        # إزالة التكرار من التنبيهات
        red_flags = list(set(red_flags))
        
        safe_name = html.escape(contract_name)
        safe_address = html.escape(address)
        
        report = f"🔍 <b>تقرير فحص العقد المتقدم:</b> {safe_name}\n"
        report += f"📍 <code>{safe_address}</code>\n\n"
        report += "🚩 <b>المشاكل المكتشفة:</b>\n"
        report += "\n".join(red_flags) + "\n\n"
        
        # إرسال أول دالة مصابة فقط لتجنب تجاوز حدود تليجرام
        if snippets:
            name, snippet = snippets[0] 
            safe_snippet = html.escape(snippet)
            report += f"💻 <b>الكود المصاب (للكلمة: {name}):</b>\n"
            report += f"<pre><code class='language-solidity'>{safe_snippet}</code></pre>"
            
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
    
    print("📡 بوت الفرز الأمني (v3) يعمل الآن ويراقب الشبكة...")
    await send_telegram("✅ بوت الثغرات (v3) بدأ العمل. سيتم إرسال الأكواد المصابة مباشرة.")
    
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
                                            print(f"🔥 تم اكتشاف ثغرة في {name}! إرسال الكود...")
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
        return web.Response(text="Advanced Bot v3 is running!")
    app = web.Application()
    app.router.add_get('/', handle)
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Web server started on port {port}")

async def main():
    await asyncio.gather(bot_logic(), web_server())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت يدوياً.")
