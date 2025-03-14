import telegram
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

TOKEN = "7560870825:AAH6Sr1KLt6G8l8tdPN-6vC5FPmNnWg9EH4"

def delete_join_messages(update: Update, context: CallbackContext):
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

def main():
    print("start")
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.status_update, delete_join_messages))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
