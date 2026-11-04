import asyncio
import aiohttp
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

# هذا السطر هو الحل لمشكلة شبكة BNB (PoA)
from web3.middleware import ExtraDataToPOAMiddleware 

# 1. إعدادات تليجرام 
TELEGRAM_TOKEN = "9275386025:AAGj8SrkdTDbWv-7aHq0ejg8NCe7zqdbVu4"
TELEGRAM_CHAT_ID = "1822828787"

# 2. إعداد شبكة BNB (تم وضع التوكن الخاص بك من الصورة)
BNB_RPC_URL = "https://special-rough-diagram.bsc.quiknode.pro/482d50162b6ecc13632015e58c3b50b8eaf16149/"
CHAIN_ID = 56  

async def send_telegram_message(message):
    """ إرسال تنبيه فوري إلى جوالك عبر تليجرام """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as response:
                if response.status != 200:
                    print(f"⚠️ تليجرام أرجع استجابة غير طبيعية: {response.status}")
    except Exception as e:
        print(f"⚠️ خطأ أثناء الاتصال بالتليجرام: {e}")

async def check_honeypot(contract_address):
    """ الاتصال بـ API الفحص واستبعاد الاسكام ومصائد الهوني بوت لشبكة BNB """
    url = f"https://api.honeypot.is/v2/IsHoneypot?address={contract_address}&chainID={CHAIN_ID}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    honeypot_data = data.get("honeypotResult", {})
                    is_honeypot = honeypot_data.get("isHoneypot", True)
                    
                    simulation = data.get("simulationResult", {})
                    buy_tax = simulation.get("buyTax", 100) if simulation else 100
                    sell_tax = simulation.get("sellTax", 100) if simulation else 100
                    
                    return {
                        "safe": not is_honeypot, 
                        "buy_tax": buy_tax, 
                        "sell_tax": sell_tax
                    }
    except Exception:
        pass
    return {"safe": False, "buy_tax": 100, "sell_tax": 100}

async def scan_bnb_network():
    """ فحص بلوكات شبكة BNB بشكل مستمر وسريع """
    w3 = AsyncWeb3(AsyncHTTPProvider(BNB_RPC_URL))
    
    # ⬇️ هذا هو السطر السحري الذي يحل مشكلة الخطأ في الصورة (PoA) ⬇️
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    try:
        if not await w3.is_connected():
            print("❌ فشل الاتصال بشبكة BNB. تأكد من صحة الرابط.")
            return
    except Exception as e:
        print(f"⚠️ تعذر فحص اتصال شبكة BNB: {e}")
        return

    print("📡 بدأت مراقبة شبكة [BNB Chain] بنجاح واقتناص الفرص الطازجة...")
    
    try:
        last_block = await w3.eth.block_number
    except Exception:
        last_block = 0

    while True:
        try:
            current_block = await w3.eth.block_number
            
            if current_block > last_block:
                start_block = max(last_block + 1, current_block - 1)
                
                for block_num in range(start_block, current_block + 1):
                    block = await w3.eth.get_block(block_num, full_transactions=True)
                    
                    for tx in block.transactions:
                        to_address = tx.get('to') if isinstance(tx, dict) else getattr(tx, 'to', None)
                        
                        # إذا كان المستلم فارغاً، فهذا عقد ذكي يتم إنشاؤه الآن 🆕
                        if to_address is None: 
                            tx_hash = tx.get('hash') if isinstance(tx, dict) else getattr(tx, 'hash', None)
                            
                            try:
                                receipt = await w3.eth.get_transaction_receipt(tx_hash)
                            except Exception:
                                continue # تخطي إذا لم يتمكن من جلب الإيصال
                                
                            if receipt and receipt.get('contractAddress'):
                                addr = receipt['contractAddress']
                                
                                # تشغيل الفحص الأمني التلقائي
                                audit = await check_honeypot(addr)
                                
                                # الشروط الأمنية: آمنة تماماً والضرائب أقل من 10%
                                if audit["safe"] and audit["buy_tax"] < 10 and audit["sell_tax"] < 10:
                                    msg = (
                                        f"💎 *اكتشاف عملة طازجة ونظيفة على شبكة BNB!*\n\n"
                                        f"🔗 *العقد:* `{addr}`\n"
                                        f"📈 *ضريبة الشراء:* {audit['buy_tax']:.1f}%\n"
                                        f"📉 *ضريبة البيع:* {audit['sell_tax']:.1f}%\n\n"
                                        f"🔍 [اضغط هنا لفتح العملة مباشرة على DexScreener](https://dexscreener.com/bsc/{addr})"
                                    )
                                    print(f"🔥 فرصة نظيفة مطابقة للشروط! جاري إرسالها للتليجرام...")
                                    await send_telegram_message(msg)

                last_block = current_block
            
            await asyncio.sleep(2.0)  # وقت انتظار متوافق مع سرعة بلوكات BNB
            
        except Exception as e:
            print(f"⚠️ خطأ أثناء فحص البلوك: {e}")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(scan_bnb_network())
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت يدوياً.")