import os
import time
from threading import Thread
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)  # Flask server to keep bot alive

# Store user messages for spam detection
user_messages = {}

# List of banned words (modify as needed)
BANNED_WORDS = ["spam", "fake", "scam", "click here", "free money"]

# Function to restrict spammers and send a warning message
def restrict_user(update: Update, context: CallbackContext):
    """Restricts the user from sending messages for 10 minutes and sends a warning message."""
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    user_name = update.message.from_user.full_name

    try:
        context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),  # Restrict sending messages
            until_date=time.time() + 600  # 600 seconds = 10 minutes
        )
        print(f"Restricted {user_name} for 10 minutes.")

        # Send a warning message in the group
        context.bot.send_message(
            chat_id=chat_id,
            text=f"🚨 {user_name} has been restricted for 10 minutes due to spamming."
        )
    except Exception as e:
        print(f"Failed to restrict user: {e}")

# Function to detect and delete spam messages
def detect_spam(update: Update, context: CallbackContext):
    """Detects and deletes spam messages, including repeated texts."""
    user_id = update.message.from_user.id
    text = update.message.text.lower() if update.message.text else ""

    print(f"User {update.message.from_user.full_name} sent message: {text}")

    # 1️⃣ Check for blacklisted words
    if any(word in text for word in BANNED_WORDS):
        try:
            update.message.delete()
            print(f"Deleted spam message from {update.message.from_user.full_name} (Blacklisted word)")
            restrict_user(update, context)  # Restrict user
        except Exception as e:
            print(f"Failed to delete spam message: {e}")
        return

    # 2️⃣ Check for repeated messages
    if user_id in user_messages:
        last_message, last_time, count = user_messages[user_id]

        if text == last_message and time.time() - last_time < 10:
            count += 1
        else:
            count = 1  # Reset count for new messages

        user_messages[user_id] = (text, time.time(), count)

        if count >= 3:  # If repeated 3 times quickly, delete as spam
            try:
                update.message.delete()
                print(f"Deleted spam message from {update.message.from_user.full_name} (Repeated message)")
                restrict_user(update, context)  # Restrict user
            except Exception as e:
                print(f"Failed to delete spam message: {e}")
    else:
        user_messages[user_id] = (text, time.time(), 1)

# Function to delete GIFs & Stickers if they are spam
def delete_spam_media(update: Update, context: CallbackContext):
    """Deletes GIFs and Stickers if they are sent repeatedly (spam) and restricts the user."""
    user_id = update.message.from_user.id
    media_type = "GIF" if update.message.animation else "Sticker"

    print(f"User {update.message.from_user.full_name} sent a {media_type}")

    # Track user media messages
    if user_id in user_messages:
        last_media, last_time, count = user_messages[user_id]

        if last_media == media_type and time.time() - last_time < 10:
            count += 1
        else:
            count = 1

        user_messages[user_id] = (media_type, time.time(), count)

        if count >= 3:  # If sent 3 times quickly, delete as spam
            try:
                update.message.delete()
                print(f"Deleted spam {media_type} from {update.message.from_user.full_name}")
                restrict_user(update, context)  # Restrict user
            except Exception as e:
                print(f"Failed to delete spam {media_type}: {e}")
    else:
        user_messages[user_id] = (media_type, time.time(), 1)

# Telegram bot setup
def run_telegram_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Handle spam text messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, detect_spam))

    # Handle spam GIFs & Stickers
    dp.add_handler(MessageHandler(Filters.animation | Filters.sticker, delete_spam_media))

    # Start bot
    print("Bot is running...")
    updater.start_polling()
    updater.idle()

# Start the bot in a separate thread
bot_thread = Thread(target=run_telegram_bot)
bot_thread.start()

# Run Flask server
@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
