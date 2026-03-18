from telegram import Update, Document
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
from urllib.parse import urlparse
import requests

# ========= CONFIG =========

SUPPORTED_SITES = [
    "deepcreekwatershedfoundation.org",
]

# ========= HELPERS =========

def clean_url(url: str):
    url = url.strip()
    if not url:
        return None
    if not url.startswith("http"):
        url = "http://" + url
    return url

def is_valid_http(url):
    return url.startswith('http://') or url.startswith('https://')

def extract_donation_id(url):
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.strip('/').split('/')
    if 'give' in path_segments:
        give_index = path_segments.index('give')
        if give_index + 1 < len(path_segments):
            return path_segments[give_index + 1]
    return None

def is_supported_site(url):
    parsed_url = urlparse(url)
    return any(domain in parsed_url.netloc for domain in SUPPORTED_SITES)

# ========= CORE CHECK =========

def check_url(url):
    url = clean_url(url)
    if not url:
        return "❌ Empty line"

    if not is_valid_http(url):
        return f"{url} - ❌ Invalid URL"

    try:
        response = requests.get(url, timeout=6)
        status = response.status_code

        donation_id = extract_donation_id(url)
        supported = is_supported_site(url)

        # ===== GiveWP Detection =====
        if donation_id:
            iframe = f"https://deepcreekwatershedfoundation.org/give/{donation_id}?giveDonationFormInIframe=1"
            return (
                f"🌐 {url}\n"
                f"✅ GiveWP Detected\n"
                f"🆔 ID: {donation_id}\n"
                f"🔗 Iframe: {iframe}\n"
                f"📶 Status: {status}"
            )

        elif supported:
            return (
                f"🌐 {url}\n"
                f"⚠️ GiveWP Supported (No ID Found)\n"
                f"📶 Status: {status}"
            )

        else:
            return f"🌐 {url} - {'✅' if status==200 else '⚠️'} Status: {status}"

    except requests.RequestException:
        return f"🌐 {url} - ❌ Connection Error"

# ========= FILE READER =========

def read_links_file(filename):
    links = []
    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            url = clean_url(line)
            if url:
                links.append(url)
    return links

# ========= COMMAND: /site =========

async def site_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /site example.com")
        return

    url = " ".join(context.args)
    await update.message.reply_text("🔍 Checking...")

    result = check_url(url)
    await update.message.reply_text(result)

# ========= FILE HANDLER =========

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document: Document = update.message.document

    if not document.file_name.endswith(".txt"):
        await update.message.reply_text("❌ Please upload a .txt file only")
        return

    await update.message.reply_text("📥 Processing file...")

    file = await document.get_file()
    file_path = "links.txt"
    await file.download_to_drive(file_path)

    links = read_links_file(file_path)

    total = len(links)
    working = 0
    failed = 0
    givewp_count = 0

    chunk = ""

    for url in links:
        result = check_url(url)

        if "✅" in result:
            working += 1
        else:
            failed += 1

        if "GiveWP" in result:
            givewp_count += 1

        if len(chunk) + len(result) > 3500:
            await update.message.reply_text(chunk)
            chunk = ""

        chunk += result + "\n\n"

    if chunk:
        await update.message.reply_text(chunk)

    stats = (
        f"📊 RESULTS SUMMARY\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📦 Total: {total}\n"
        f"✅ Working: {working}\n"
        f"❌ Failed: {failed}\n"
        f"💳 GiveWP: {givewp_count}"
    )

    await update.message.reply_text(stats)

    os.remove(file_path)

# ========= RUN =========

if __name__ == "__main__":
    app = ApplicationBuilder().token("7707742168:AAGYX7yJBHjm-aVECNFHJ8n68YMPRThD76w").build()

    app.add_handler(CommandHandler("site", site_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot Started...")
    app.run_polling()
