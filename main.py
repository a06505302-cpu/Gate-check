from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import urlparse
import requests

# قائمة المواقع المدعومة
SUPPORTED_SITES = [
    "deepcreekwatershedfoundation.org",
    # أضف مزيدًا من النطاقات المدعومة هنا إذا لزم الأمر
]

# التحقق مما إذا كان الموقع يدعم التبرع
def is_supported_site(url):
    parsed_url = urlparse(url)
    return any(domain in parsed_url.netloc for domain in SUPPORTED_SITES)

# استخراج معرف التبرع من الرابط
def extract_donation_id(url):
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.strip('/').split('/')
    if 'give' in path_segments:
        give_index = path_segments.index('give')
        if give_index + 1 < len(path_segments):
            return path_segments[give_index + 1]
    return None

# التحقق من صحة صيغة الرابط
def is_valid_http(url):
    return url.startswith('http://') or url.startswith('https://')

# التحقق من حالة الرد على الرابط
def check_url_status(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

# التحقق من الروابط داخل ملف
def check_links_in_file():
    links = []
    try:
        with open("links.txt", "r") as file:
            links = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("ملف links.txt غير موجود.")
        return
    
    results = []
    for url in links:
        if not is_valid_http(url):
            results.append(f"{url} - غير صالح")
            continue
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                results.append(f"{url} - يعمل بشكل جيد")
            else:
                results.append(f"{url} - استجابة غير متوقعة: {response.status_code}")
        except requests.RequestException:
            results.append(f"{url} - غير يعمل أو هناك مشكلة")
    return results

# أمر /give
async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("رجاءً أرسل الرابط بعد الأمر، مثلاً /give <رابط>")
        return
    
    url = context.args[0]
    await update.message.reply_text("🔍 جاري التحقق من الرابط...")

    # التحقق من صحة الرابط
    if not is_valid_http(url):
        await update.message.reply_text("❌ صيغة الرابط غير صحيحة. يجب أن يبدأ بـ http:// أو https://")
        return
    
    # التحقق من استجابة الموقع
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            await update.message.reply_text(f"⚠️ الموقع لا يستجيب بشكل صحيح. الرمز: {response.status_code}")
            return
    except requests.RequestException:
        await update.message.reply_text("❌ غير قادر على الوصول للموقع. يرجى التحقق من الرابط.")
        return

    # التحقق مما إذا كان الموقع يدعم التبرع
    supported = is_supported_site(url)

    # استخراج معرف التبرع
    donation_id = extract_donation_id(url)

    # الرد بناءً على النتائج
    if donation_id:
        new_link = f"https://deepcreekwatershedfoundation.org/give/{donation_id}?giveDonationFormInIframe=1"
        message = (
            f"🌐 **مباشر**\n"
            f"رابطك يدعم معرف التبرع: {donation_id}\n"
            f"رابط التبرع المعدل: {new_link}"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    elif supported:
        await update.message.reply_text("✅ الرابط صالح ويدعم التبرع.")
    else:
        await update.message.reply_text("❌ الرابط غير مدعوم أو غير صحيح.")

# أمر /check (للتحقق من روابط في ملف)
async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = check_links_in_file()
    if results:
        reply_text = "\n".join(results)
        await update.message.reply_text(reply_text)
    else:
        await update.message.reply_text("لا توجد روابط للتحقق أو الملف غير موجود.")

# أمر /checklinks (للتحقق من روابط في ملف)
async def check_links_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = check_links_in_file()
    if results:
        reply_text = "\n".join(results)
        await update.message.reply_text(reply_text)
    else:
        await update.message.reply_text("لا توجد روابط للتحقق أو الملف غير موجود.")

# البرنامج الرئيسي
if __name__ == '__main__':
    app = ApplicationBuilder().token('7707742168:AAGYX7yJBHjm-aVECNFHJ8n68YMPRThD76w').build()

    # إضافة معالجات الأوامر
    app.add_handler(CommandHandler("give", give_command))
    app.add_handler(CommandHandler("check", check_command))
    app.add_handler(CommandHandler("checklinks", check_links_file))
    
    app.run_polling()
