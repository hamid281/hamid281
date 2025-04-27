import os
import logging
from threading import Thread, Lock
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from flask import Flask
from waitress import serve
from dotenv import load_dotenv

# --- تنظیمات اولیه ---
load_dotenv()

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# قفل برای جلوگیری از اجرای چند نمونه
bot_lock = Lock()

# --- تنظیمات ربات ---
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '7708534005:AAHxcmWAs82atcdiNLwuPw_3CDX_3A_hIfs')
if not TOKEN:
    logger.error("لطفا TELEGRAM_BOT_TOKEN را تنظیم کنید!")
    exit(1)

ADMIN_ID = int(os.getenv('ADMIN_ID', '7759311246'))
MY_PHONE = "09120824174"
MY_CARD = "6104-3378-3263-5559"

# --- دیتابیس محصولات ---
products_db = {
    1: {'name': '🍕 پیتزا مخصوص', 'price': 120000, 'stock': 10},
    2: {'name': '🍔 همبرگر ویژه', 'price': 95000, 'stock': 8},
    3: {'name': '🥤 نوشابه قوطی', 'price': 15000, 'stock': 20}
}

user_carts = {}

# --- پیام‌ها ---
MESSAGES = {
    "welcome": "👋 خوش آمدید! برای سفارش، یکی از گزینه‌های زیر را انتخاب کنید.",
    "products": "🛍 لیست محصولات موجود:\n",
    "contact": f"📞 تماس با ما:\nشماره تماس: {MY_PHONE}\nایمیل: example@example.com",
    "cart_empty": "🛒 سبد خرید شما خالی است!",
    "cart": "📦 سبد خرید شما:\n",
    "checkout": f"💰 مبلغ قابل پرداخت: {{total}} تومان\n\n💳 برای پرداخت به شماره کارت زیر واریز کنید:\n{MY_CARD}\n📞 پس از پرداخت، فیش را به {MY_PHONE} ارسال کنید",
    "added_to_cart": "✅ محصول به سبد خرید اضافه شد!"
}

# --- صفحه کلیدها ---
KEYBOARD_MAIN = [
    [KeyboardButton("🛍 محصولات"), KeyboardButton("📞 تماس با ما")],
    [KeyboardButton("🛒 سبد خرید"), KeyboardButton("💳 پرداخت")]
]

KEYBOARD_PRODUCTS = [
    [KeyboardButton(f"🛒 خرید {product['name']}")] for product in products_db.values()
] + [[KeyboardButton("🔙 بازگشت")]]

# --- توابع ربات ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_carts[user.id] = {}
    await update.message.reply_text(
        MESSAGES["welcome"],
        reply_markup=ReplyKeyboardMarkup(KEYBOARD_MAIN, resize_keyboard=True)
    )

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products_text = MESSAGES["products"]
    for pid, product in products_db.items():
        products_text += f"{pid}. {product['name']} - {product['price']:,} تومان\nموجودی: {product['stock']}\n\n"
    
    await update.message.reply_text(
        products_text,
        reply_markup=ReplyKeyboardMarkup(KEYBOARD_PRODUCTS, resize_keyboard=True)
    )

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    for pid, product in products_db.items():
        if product["name"] in text:
            if product["stock"] > 0:
                user_carts.setdefault(user.id, {})
                user_carts[user.id][pid] = user_carts[user.id].get(pid, 0) + 1
                products_db[pid]['stock'] -= 1
                await update.message.reply_text(
                    MESSAGES["added_to_cart"],
                    reply_markup=ReplyKeyboardMarkup(KEYBOARD_MAIN, resize_keyboard=True)
                )
            else:
                await update.message.reply_text("❌ موجودی کالا تمام شده!")
            return

    await update.message.reply_text("❗️ محصول پیدا نشد!")

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cart = user_carts.get(user.id, {})
    
    if not cart:
        await update.message.reply_text(MESSAGES["cart_empty"])
        return
    
    cart_text = MESSAGES["cart"]
    total = 0
    for pid, quantity in cart.items():
        product = products_db[pid]
        subtotal = product["price"] * quantity
        cart_text += f"{product['name']} × {quantity} = {subtotal:,} تومان\n"
        total += subtotal
    
    cart_text += f"\n{MESSAGES['checkout'].format(total=f'{total:,}')}"
    
    await update.message.reply_text(
        cart_text,
        reply_markup=ReplyKeyboardMarkup(KEYBOARD_MAIN, resize_keyboard=True)
    )

# --- سرور Flask برای Health Check ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "ربات تلگرام در حال اجراست", 200

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"در حال راه‌اندازی سرور Flask روی پورت {port}")
    serve(app, host='0.0.0.0', port=port)

# --- اجرای اصلی ---
def run_bot():
    try:
        application = Application.builder().token(TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🛍 محصولات$"), show_products))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🛒 خرید"), add_to_cart))
        application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🛒 سبد خرید$"), show_cart))
        
        logger.info("ربات تلگرام در حال راه‌اندازی...")
        application.run_polling(
            clean=True,
            drop_pending_updates=True,
            close_loop=False,
            read_timeout=30,
            connect_timeout=10,
            pool_timeout=10
        )
    except Exception as e:
        logger.error(f"خطا در اجرای ربات: {e}", exc_info=True)
        raise

def main():
    if not bot_lock.acquire(blocking=False):
        logger.warning("ربات از قبل در حال اجراست!")
        return

    try:
        # اجرای Flask در یک thread جداگانه
        flask_thread = Thread(target=run_flask, daemon=True)
        flask_thread.start()
        
        # اجرای ربات تلگرام
        run_bot()
    except Exception as e:
        logger.error(f"خطای اصلی: {e}", exc_info=True)
    finally:
        bot_lock.release()

if __name__ == "__main__":
    main()
