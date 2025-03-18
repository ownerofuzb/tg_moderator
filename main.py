import os
import time
from threading import Thread
from flask import Flask
from telegram import Update, ChatPermissions
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")
DEBUG_CHAT_ID = "-1001847826975"

app = Flask(__name__)

user_messages = {}

BANNED_WORDS = [
    "free money", "fuck", "bitch", "nigga", "nigger", "Хуй", "сука",
    "Гавно", "Мудак", "Пошёл на хуй", "Ублюдок", "Гандон", "Пиздец",
    "Сволочь", "Гавно", "Мудак", "Ублюдок", "Гандон", "Пиздец",
    "Бля", "секс", "jala", "ебать", "yba", "chert", "черть", "порн",
    "porno", "gay", "gey", "гей", "жала", "xuy", "huy", "tupoy", "тупой"
]

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🤖 Hello! I'm your group management bot. I will delete all spam messages from your group!\n"
        "To activate me, add me to your group and promote me to admin."
    )

def report(update: Update, context: CallbackContext, message: str, reason: str):
    """Sends a report about banned words or spam activity."""
    chat_id = update.effective_chat.id
    user = update.message.from_user.full_name
    user_id = update.message.from_user.id
    context.bot.send_message(
        chat_id=DEBUG_CHAT_ID,
        text=f"🚨 ALERT:\n👤 User: {user} (ID: {user_id})\n💬 Message: {message}\n⚠️ Reason: {reason}\n📍 Chat ID: {chat_id}"
    )

def restrict_user(update: Update, context: CallbackContext):
    """Restricts the user from sending messages for 5 minutes and deletes the warning message after 5 minutes."""
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    user_name = update.message.from_user.full_name

    try:
        context.bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=time.time() + 300 
        )
        print(f"Restricted {user_name} for 5 minutes.")

        warning_message = context.bot.send_message(
            chat_id=chat_id,
            text=f"🚨 {user_name} has been restricted for 5 minutes due to spamming."
        )

        context.job_queue.run_once(delete_warning_message, 300, context=(chat_id, warning_message.message_id))

    except Exception as e:
        print(f"Failed to restrict user: {e}")

def delete_warning_message(context: CallbackContext):
    """Deletes the warning message after 5 minutes."""
    chat_id, message_id = context.job.context
    try:
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        print(f"Deleted restriction warning message in chat {chat_id}.")
    except Exception as e:
        print(f"Failed to delete warning message: {e}")

def detect_spam(update: Update, context: CallbackContext):
    """Detects and deletes banned words, logs the word, and restricts the user if necessary."""
    user_id = update.message.from_user.id
    text = update.message.text.lower() if update.message.text else ""
    user_name = update.message.from_user.full_name

    print(f"User {user_name} sent message: {text}")

    detected_word = None
    for word in BANNED_WORDS:
        if word.lower() in text:
            detected_word = word
            break  

    if detected_word:
        try:
            update.message.delete()
            report(update, context, text, f"🚫 Banned word detected: '{detected_word}'")
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
                report(update, context, text, "🚨 Repeated message detected!")
                restrict_user(update, context)
            except Exception as e:
                print(f"Failed to delete spam message: {e}")
    else:
        user_messages[user_id] = (text, time.time(), 1)

def delete_spam_media(update: Update, context: CallbackContext):
    """Deletes GIFs and Stickers if sent repeatedly and restricts the user."""
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
                report(update, context, media_type, "🚨 Repeated Sticker/GIF detected!")
                restrict_user(update, context)
            except Exception as e:
                print(f"Failed to delete spam {media_type}: {e}")
    else:
        user_messages[user_id] = (media_type, time.time(), 1)

def delete_join_messages(update: Update, context: CallbackContext):
    """Deletes join and leave messages to keep the chat clean."""
    if update.message:
        try:
            if update.message.new_chat_members:
                update.message.delete()
                print(f"Deleted join message from {update.message.from_user.full_name}")

            if update.message.left_chat_member:
                update.message.delete()
                print(f"Deleted leave message from {update.message.left_chat_member.full_name}")

        except Exception as e:
            print(f"Failed to delete message: {e}")

def run_telegram_bot():
    """Starts the Telegram bot."""
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.status_update, delete_join_messages))
    dp.add_handler(CommandHandler("start", start))  
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, detect_spam)) 
    dp.add_handler(MessageHandler(Filters.animation | Filters.sticker, delete_spam_media))  

    print("Bot is running...")
    updater.start_polling()
    updater.idle()

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    bot_thread = Thread(target=run_telegram_bot)
    bot_thread.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
