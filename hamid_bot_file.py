import os
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# تنظیمات
TOKEN = os.getenv('7708534005:AAHxcmWAs82atcdiNLwuPw_3CDX_3A_hIfs')
ADMIN_ID = int(os.getenv('ADMIN_ID', '7759311246'))

# دیتابیس محصولات
products_db = {
    1: {'name': '🍕 پیتزا مخصوص', 'price': 120000, 'stock': 10},
    2: {'name': '🍔 همبرگر ویژه', 'price': 95000, 'stock': 8},
    3: {'name': '🥤 نوشابه قوطی', 'price': 15000, 'stock': 20}
}

user_carts = {}

# پیام‌ها
MESSAGES = {
    "welcome": "👋 خوش آمدید! برای سفارش، یکی از گزینه‌های زیر را انتخاب کنید.",
    "products": "🛍 لیست محصولات موجود:\n",
    "contact": "📞 تماس با ما: example@example.com",
    "cart_empty": "🛒 سبد خرید شما خالی است!",
    "cart": "📦 سبد خرید شما:\n",
    "unknown": "دستور نامشخص!",
    "admin_welcome": "🎛 خوش آمدید به پنل مدیریت",
    "added_to_cart": "✅ محصول به سبد خرید اضافه شد!",
    "checkout": "💰 مبلغ قابل پرداخت: {total} تومان"
}

# صفحه کلید
KEYBOARD_MAIN = [
    [KeyboardButton("🛍 محصولات"), KeyboardButton("📞 تماس با ما")],
    [KeyboardButton("🛒 سبد خرید")]
]

# توابع بات
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
        products_text += f"{pid}. {product['name']} - {product['price']} تومان\n📦 موجودی: {product['stock']}\n\n"
    
    product_buttons = [[KeyboardButton(f"🛒 خرید {product['name']}")] for product in products_db.values()]
    product_buttons.append([KeyboardButton("🔙 بازگشت")])

    await update.message.reply_text(
        products_text,
        reply_markup=ReplyKeyboardMarkup(product_buttons, resize_keyboard=True)
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
                await update.message.reply_text("❌ این محصول ناموجود است.")
            return

    await update.message.reply_text("❗️محصول یافت نشد!")

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cart = user_carts.get(user.id, {})
    if not cart:
        await update.message.reply_text(MESSAGES["cart_empty"], reply_markup=ReplyKeyboardMarkup(KEYBOARD_MAIN, resize_keyboard=True))
        return
    
    cart_text = MESSAGES["cart"]
    total = 0
    for pid, quantity in cart.items():
        product = products_db[pid]
        subtotal = product["price"] * quantity
        cart_text += f"{product['name']} × {quantity} = {subtotal} تومان\n"
        total += subtotal
    cart_text += f"\n{MESSAGES['checkout'].format(total=total)}"
    
    await update.message.reply_text(cart_text, reply_markup=ReplyKeyboardMarkup(KEYBOARD_MAIN, resize_keyboard=True))

# اجرای برنامه
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🛍 محصولات$"), show_products))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🛒 خرید "), add_to_cart))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🛒 سبد خرید$"), show_cart))

    application.run_polling()

if __name__ == "__main__":
    main()
