import os
import telegram
from flask import Flask
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

TOKEN = os.getenv("7560870825:AAH6Sr1KLt6G8l8tdPN-6vC5FPmNnWg9EH4")  # Get token from environment variable

app = Flask(__name__)  # Flask server to keep Render's web service alive

def delete_join_messages(update: Update, context: CallbackContext):
    """Deletes messages when a new user joins the group."""
    if update.message and update.message.new_chat_members:
        try:
            update.message.delete()
            print(f"Deleted a join message from {update.message.from_user.full_name}")
        except Exception as e:
            print(f"Failed to delete message: {e}")
    if update.message and update.message.left_chat_member:
        try:
            update.message.delete()
            print(f"Deleted a left message from {update.message.from_user.full_name}")
        except Exception as e:
            print(f"Failed to delete message: {e}")

def run_telegram_bot():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Handle new user join messages
    dp.add_handler(MessageHandler(Filters.status_update, delete_join_messages))

    updater.start_polling()
    updater.idle()  # Keep the bot running

# Flask route to prevent shutdown
@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    from threading import Thread

    # Run Telegram bot in a separate thread
    bot_thread = Thread(target=run_telegram_bot)
    bot_thread.start()

    # Start Flask web server on Render's required port
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
