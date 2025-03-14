import os
import time
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__) 

user_messages = {}

BANNED_WORDS = ["spam", "fake", "scam", "click here", "free money"]

def restrict_user(update: Update, context: CallbackContext):
    """Restricts the user from sending messages for 10 minutes and sends a warning message."""
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    user_name = update.message.from_user.full_name

    try:
        context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=time.time() + 600  
        )
        print(f"Restricted {user_name} for 10 minutes.")

        context.bot.send_message(
            chat_id=chat_id,
            text=f"🚨 {user_name} has been restricted for 10 minutes due to spamming."
        )
    except Exception as e:
        print(f"Failed to restrict user: {e}")

def detect_spam(update: Update, context: CallbackContext):
    """Detects and deletes spam messages, including repeated texts."""
    user_id = update.message.from_user.id
    text = update.message.text.lower() if update.message.text else ""

    print(f"User {update.message.from_user.full_name} sent message: {text}")

    if any(word in text for word in BANNED_WORDS):
        try:
            update.message.delete()
            print(f"Deleted spam message from {update.message.from_user.full_name} (Blacklisted word)")
            restrict_user(update, context) 
        except Exception as e:
            print(f"Failed to delete spam message: {e}")
        return

    
    if user_id in user_messages:
        last_message, last_time, count = user_messages[user_id]

        if text == last_message and time.time() - last_time < 10:
            count += 1
        else:
            count = 1  

        user_messages[user_id] = (text, time.time(), count)

        if count >= 3:  
            try:
                update.message.delete()
                print(f"Deleted spam message from {update.message.from_user.full_name} (Repeated message)")
                restrict_user(update, context)  # Restrict user
            except Exception as e:
                print(f"Failed to delete spam message: {e}")
    else:
        user_messages[user_id] = (text, time.time(), 1)

def delete_spam_media(update: Update, context: CallbackContext):
    """Deletes GIFs and Stickers if they are sent repeatedly (spam) and restricts the user."""
    user_id = update.message.from_user.id
    media_type = "GIF" if update.message.animation else "Sticker"

    print(f"User {update.message.from_user.full_name} sent a {media_type}")

    if user_id in user_messages:
        last_media, last_time, count = user_messages[user_id]

        if last_media == media_type and time.time() - last_time < 10:
            count += 1
        else:
            count = 1

        user_messages[user_id] = (media_type, time.time(), count)

        if count >= 3:  
            try:
                update.message.delete()
                print(f"Deleted spam {media_type} from {update.message.from_user.full_name}")
                restrict_user(update, context)  # Restrict user
            except Exception as e:
                print(f"Failed to delete spam {media_type}: {e}")
    else:
        user_messages[user_id] = (media_type, time.time(), 1)

def run_telegram_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, detect_spam))

    dp.add_handler(MessageHandler(Filters.animation | Filters.sticker, delete_spam_media))

    print("Bot is running...")
    updater.start_polling()

if __name__ == "__main__":
    run_telegram_bot()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
