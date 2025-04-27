import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from dotenv import load_dotenv
from flask import Flask

# بارگذاری متغیرهای محیطی
load_dotenv()

# تنظیمات
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7708534005:AAHxcmWAs82atcdiNLwuPw_3CDX_3A_hIfs')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7759311246'))
MY_PHONE = "09120824174"
MY_CARD = "6104-3378-3263-5559"

# ایجاد برنامه Flask برای health check
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200

# دیتابیس محصولات و توابع بات (همان کد قبلی شما)
# ... [کدهای قبلی شما بدون تغییر]

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

def main():
    # اجرای Flask در یک thread جداگانه
    from threading import Thread
    Thread(target=run_flask).start()

    # اجرای ربات تلگرام
    application = Application.builder().token(TOKEN).build()
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🛍 محصولات$"), show_products))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📞 تماس با ما$"), show_contact))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🛒 خرید "), add_to_cart))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🛒 سبد خرید$"), show_cart))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🔙 بازگشت$"), back_to_main))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🏠 صفحه اصلی$"), back_to_main))

    application.run_polling()

if __name__ == "__main__":
    main()
