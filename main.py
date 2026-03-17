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

# Function to check links from a file
def check_links_in_file():
    links = []
    try:
        with open("links.txt", "r") as file:
            links = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print("The file links.txt does not exist.")
        return
    
    results = []
    for url in links:
        if not (url.startswith("http://") or url.startswith("https://")):
            results.append(f"{url} - Invalid")
            continue
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                results.append(f"{url} - Working fine")
            else:
                results.append(f"{url} - Unexpected response: {response.status_code}")
        except requests.RequestException:
            results.append(f"{url} - Not working or there's an issue")
    return results

# Command handler for /give
async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Please send the link after the command, e.g., /give <URL>")
        return
    
    url = context.args[0]
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

    # Check if site supports donation
    supported = is_supported_site(url)

    # Extract donation ID
    donation_id = extract_donation_id(url)

    # Compose the reply based on the result
    if donation_id:
        new_link = f"https://deepcreekwatershedfoundation.org/give/{donation_id}?giveDonationFormInIframe=1"
        message = (
            f"🌐 **Live**\n"
            f"Your link supports donation ID: {donation_id}\n"
            f"Modified donation link: {new_link}"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    elif supported:
        await update.message.reply_text("✅ The link is valid and supports donations.")
    else:
        await update.message.reply_text("❌ The link is unsupported or invalid.")

# Command to check links from file
async def check_links_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = check_links_in_file()
    if results:
        reply_text = "\n".join(results)
        # If message is too long, consider splitting or sending as a file
        await update.message.reply_text(reply_text)
    else:
        await update.message.reply_text("No links found to check.")

# Main program
if __name__ == '__main__':
    app = ApplicationBuilder().token('7707742168:AAGYX7yJBHjm-aVECNFHJ8n68YMPRThD76w').build()

    # Add command handlers
    app.add_handler(CommandHandler("give", give_command))
    app.add_handler(CommandHandler("checklinks", check_links_file))
    
    app.run_polling()
