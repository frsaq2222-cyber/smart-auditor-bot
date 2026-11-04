import asyncio
import os
import aiohttp
from web3 import AsyncWeb3
from web3.providers import AsyncHTTPProvider

# ==========================================
# ⚙️ 1. الإعدادات الأساسية (قراءة آمنة)
# ==========================================
# قراءة رابط الشبكة من Environment Variables
RPC_URL = os.getenv("BNB_RPC_URL", "https://bsc-dataseed.binance.org/")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

VENUS_COMPTROLLER = "0xfD36E2c2a6789Db23113685031d7F16329158384"
VTOKEN_USDT = "0xfD5840Cd36d94D7229439859C0112a4185BC0255"

COMPTROLLER_ABI = [{"constant": True, "inputs": [{"internalType": "address", "name": "account", "type": "address"}], "name": "getAccountLiquidity", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}, {"internalType": "uint256", "name": "", "type": "uint256"}, {"internalType": "uint256", "name": "", "type": "uint256"}], "payable": False, "stateMutability": "view", "type": "function"}]
VTOKEN_ABI = [{"anonymous": False, "inputs": [{"indexed": False, "internalType": "address", "name": "borrower", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "borrowAmount", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "accountBorrows", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "totalBorrows", "type": "uint256"}], "name": "Borrow", "type": "event"}]

# ==========================================
# 📱 2. دالة إرسال إشعارات التليجرام
# ==========================================
async def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return # تجاهل الإرسال إذا لم تكن الإعدادات موجودة
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(url, json=payload)
    except Exception as e:
        print(f"⚠️ فشل إرسال التليجرام: {e}")

# ==========================================
# 🔍 3. دالة فحص السيولة للتصفية
# ==========================================
async def check_liquidity(w3, comptroller, wallet_address):
    try:
        result = await comptroller.functions.getAccountLiquidity(wallet_address).call()
        # إذا كان الخطأ 0 (لا يوجد خطأ) والعجز (shortfall) أكبر من 0
        if result[0] == 0 and result[2] > 0:
            shortfall = w3.from_wei(result[2], 'ether') # تحويل العجز لرقم مقروء
            msg = f"🚨🚨 <b>[هدف ثمين]</b> محفظة معرضة للتصفية!\n\n"
            msg += f"👤 <b>المحفظة:</b> <code>{wallet_address}</code>\n"
            msg += f"📉 <b>العجز:</b> {shortfall:.2f} USD\n"
            msg += f"🔗 <a href='https://bscscan.com/address/{wallet_address}'>عرض في BscScan</a>"
            
            print(f"🚨 [هدف] محفظة: {wallet_address} | العجز: {shortfall}")
            await send_telegram(msg) # إرسال إشعار فوري
    except Exception:
        pass

# ==========================================
# 🚀 4. الحلقة الرئيسية للبوت
# ==========================================
async def main():
    print("📡 جاري الاتصال بشبكة BNB...")
    if not TELEGRAM_TOKEN:
        print("⚠️ تحذير: توكن التليجرام غير موجود، لن يتم إرسال إشعارات.")
        
    w3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))
    
    # إضافة دعم شبكة BNB (POA Middleware)
    try:
        from web3.middleware import ExtraDataToPOAMiddleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except ImportError:
        from web3.middleware import async_geth_poa_middleware
        w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)

    comptroller = w3.eth.contract(address=w3.to_checksum_address(VENUS_COMPTROLLER), abi=COMPTROLLER_ABI)
    vtoken_usdt = w3.eth.contract(address=w3.to_checksum_address(VTOKEN_USDT), abi=VTOKEN_ABI)

    # جلب رقم البلوك الحالي لنبدأ منه
    last_block = await w3.eth.block_number
    print(f"✅ البوت يعمل الآن! نبدأ المراقبة من البلوك: {last_block}")
    print("⏳ ننتظر عمليات الاقتراض الجديدة... (اضغط Ctrl+C للإيقاف)")
    
    await send_telegram(f"✅ <b>بوت التصفية (Venus) يعمل الآن!</b>\nبدأ المراقبة من البلوك: {last_block}")

    while True:
        try:
            current_block = await w3.eth.block_number
            
            # إذا ظهر بلوك جديد
            if current_block > last_block:
                start_block = last_block + 1
                end_block = current_block
                
                try:
                    # جلب أحداث الاقتراض في البلوكات الجديدة
                    events = await vtoken_usdt.events.Borrow.get_logs(from_block=start_block, to_block=end_block)
                    
                    if events:
                        print(f"🎯 تم العثور على {len(events)} عملية اقتراض في البلوك {end_block}!")
                        for event in events:
                            borrower = event['args']['borrower']
                            await check_liquidity(w3, comptroller, borrower)
                except Exception:
                    pass # تجاهل الأخطاء في بلوك معين ونكمل
                
                last_block = current_block
            
            # انتظار ثانية واحدة قبل فحص البلوك التالي (توفيراً لاستهلاك الـ API)
            await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            print("\n🛑 تم إيقاف البوت يدوياً.")
            break
        except Exception as e:
            print(f"⚠️ خطأ في الشبكة: {e}")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
