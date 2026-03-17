from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import urlparse
import requests

# Supported sites list
SUPPORTED_SITES = [
    "deepcreekwatershedfoundation.org",
    # Add other supported domains here if needed
]

# Check if the site supports the donation feature
def is_supported_site(url):
    parsed_url = urlparse(url)
    return any(domain in parsed_url.netloc for domain in SUPPORTED_SITES)

# Extract donation ID from the URL
def extract_donation_id(url):
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.strip('/').split('/')
    if 'give' in path_segments:
        give_index = path_segments.index('give')
        if give_index + 1 < len(path_segments):
            return path_segments[give_index + 1]
    return None

# Validate URL format
def is_valid_http(url):
    return url.startswith('http://') or url.startswith('https://')

# Check URL response status
def check_url_status(url):
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Command handler for /give
async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Please send the link after the command, e.g., /give <URL>")
        return
    
    url = context.args[0]

    # Indicate that the check has started
    await update.message.reply_text("🔍 Checking the link...")

    # Validate URL format
    if not is_valid_http(url):
        await update.message.reply_text("❌ Invalid URL format. The link must start with http:// or https://")
        return
    
    # Verify site response
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            await update.message.reply_text(f"⚠️ The site is not responding properly. Status code: {response.status_code}")
            return
    except requests.RequestException:
        await update.message.reply_text("❌ Unable to reach the site. Please check the URL.")
        return

    # Check if site is supported
    supported = is_supported_site(url)

    # Extract donation ID
    donation_id = extract_donation_id(url)

    # Compose the final message
    if donation_id:
        new_link = f"https://deepcreekwatershedfoundation.org/give/{donation_id}?giveDonationFormInIframe=1"
        message = (
            f"🌐 **Live**\n"
            f"Your link supports donation ID: {donation_id}\n"
            f"Site support status: {'Supported' if supported else 'Not Supported'}"
        )
    else:
        message = (
            f"🌐 **Live**\n"
            f"Your link does not contain a donation ID.\n"
            f"Site support status: {'Supported' if supported else 'Not Supported'}"
        )

    await update.message.reply_markdown_v2(message)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send /give <donation link> to check your URL.")

# Main application
if __name__ == '__main__':
    TOKEN = '7707742168:AAGYX7yJBHjm-aVECNFHJ8n68YMPRThD76w'  # Replace with your bot token
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("give", give_command))

    app.run_polling()
