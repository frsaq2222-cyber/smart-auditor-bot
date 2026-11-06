import re
import os

def scan_local_contract(file_path):
    print(f"🚀 جاري إطلاق الصاروخ لفحص الملف المحلي: {file_path} ...")
    
    # التأكد من وجود الملف
    if not os.path.exists(file_path):
        print("❌ لم يتم العثور على الملف. تأكد من المسار.")
        return

    try:
        # قراءة الكود من الملف
        with open(file_path, 'r', encoding='utf-8') as file:
            source_code = file.read()

        print("✅ تم جلب الكود بنجاح. جاري الفحص الصاروخي...")

        # الفحص الصاروخي (Regex) للبحث عن balanceOf داخل دوال المكافآت
        pattern = r"function\s+.*?\(.*?\).*?\{[^}]*?balanceOf\s*\(.*?\).*?\}"
        
        matches = re.finditer(pattern, source_code, re.DOTALL)
        
        found_vulnerability = False
        for match in matches:
            function_code = match.group(0)
            # التأكد من أن الدالة لها علاقة بالمكافآت أو التوزيعات
            if "claim" in function_code.lower() or "reward" in function_code.lower() or "distribute" in function_code.lower():
                print("\n🚨🚨 [تم اكتشاف ثغرة محتملة!] 🚨🚨")
                print("الوظيفة المشبوهة:")
                print("-" * 50)
                print(function_code.strip()[:400] + "...\n") # طباعة جزء من الدالة
                print("-" * 50)
                found_vulnerability = True
        
        if not found_vulnerability:
            print("\n✅ لم يتم العثور على النمط الخطير (balanceOf داخل دالة مكافآت) في هذا العقد.")
            print("ملاحظة: قد يستخدم العقد اسماً مختلفاً للدالة، أو أنه يستخدم Snapshot (وهو آمن).")

    except Exception as e:
        print(f"⚠️ خطأ أثناء الفحص: {e}")

if __name__ == "__main__":
    # 🎯 هنا نضع مسار ملف العقد الموجود على جهازك
    # تأكد أن الملف موجود في مجلد contracts
    local_contract_path = os.path.join("contracts", "AirdropTest.sol")
    
    print("💡 هذا السكربت يفحص الكود بسرعة البرق بحثاً عن ثغرة balanceOf.")
    scan_local_contract(local_contract_path)