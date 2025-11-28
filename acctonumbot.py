import logging
import os
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# =======================
#  CONFIG – EDIT THESE
# =======================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

CRYPTO_ADDRESSES = {
    "BTC":  "your_btc_address_here",
    "ETH":  "your_eth_address_here",
    "USDT": "your_usdt_address_here",
    "LTC":  "your_ltc_address_here",
}

PLANS = {
    "week":  {"label": "Weekly", "price": 9.99, "duration": "1 week"},
    "month": {"label": "Monthly", "price": 19.99, "duration": "1 month"},
    "year":  {"label": "Yearly", "price": 79.00, "duration": "1 year"},
}

SUBSCRIPTIONS = {}

# =======================
#  LOGGING
# =======================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def log_user_action(update: Update, action: str) -> None:
    user = update.effective_user
    try:
        with open("logs.txt", "a", encoding="utf-8") as f:
            f.write(
                f"{datetime.utcnow().isoformat()} | {action} | "
                f"user_id={user.id} | username={user.username} | "
                f"name={user.full_name}\n"
            )
    except:
        pass


# =======================
#  COMMANDS
# =======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user_action(update, "START")

    kb = [
        [KeyboardButton("/buy"), KeyboardButton("/subscriptions")],
        [KeyboardButton("/getnum"), KeyboardButton("/help")],
    ]
    reply_kb = ReplyKeyboardMarkup(kb, resize_keyboard=True)

    text = (
        "✨ <b>Welcome to acctonumbot</b>\n\n"
        "This is a school project bot.\n\n"
        "👉 What I can do:\n"
        "• Convert @username ➝ Telegram number (ID)\n"
        "• Let you pick a subscription plan (demo)\n\n"
        "Use buttons below or commands."
    )
    await update.message.reply_html(text, reply_markup=reply_kb)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user_action(update, "HELP")

    await update.message.reply_html(
        "📘 <b>Help Menu</b>\n\n"
        "/buy – View subscription plans\n"
        "/subscriptions – View your current plan\n"
        "/getnum @username – Convert username → number\n"
        "/start – Main menu"
    )


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user_action(update, "BUY")

    keyboard = [
        [InlineKeyboardButton("Weekly $9.99", callback_data="plan_week")],
        [InlineKeyboardButton("Monthly $19.99", callback_data="plan_month")],
        [InlineKeyboardButton("Yearly $79.00", callback_data="plan_year")],
    ]

    await update.message.reply_html(
        "💳 <b>Choose a subscription plan:</b>\n\n"
        "Weekly – $9.99\n"
        "Monthly – $19.99\n"
        "Yearly – $79\n\n"
        "Select a plan to get payment details.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user_action(update, "SUBSCRIPTIONS")

    user_id = update.effective_user.id
    sub = SUBSCRIPTIONS.get(user_id)

    if not sub:
        await update.message.reply_html(
            "📦 <b>Your Subscription</b>\n\nYou do not have a plan yet.\nUse /buy."
        )
    else:
        plan = PLANS[sub["plan_key"]]
        await update.message.reply_html(
            f"📦 <b>Your Subscription</b>\n\n"
            f"Plan: <b>{plan['label']}</b>\n"
            f"Price: ${plan['price']}\n"
            f"Duration: {plan['duration']}\n"
            f"Status: <b>{sub['status']}</b>"
        )


async def getnum(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_user_action(update, "GETNUM")

    if not context.args:
        await update.message.reply_html("Usage: <code>/getnum @username</code>")
        return

    username = context.args[0]
    if not username.startswith("@"):
        username = "@" + username

    await fetch_id(update, context, username)


# =======================
#  CALLBACK HANDLER
# =======================

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data.startswith("plan_"):
        plan_key = data.split("_")[1]
        plan = PLANS[plan_key]

        SUBSCRIPTIONS[user_id] = {
            "plan_key": plan_key,
            "status": "pending payment",
        }

        msg = (
            f"✅ <b>{plan['label']} Plan Selected</b>\n"
            f"Price: ${plan['price']}\n"
            f"Duration: {plan['duration']}\n\n"
            "🪙 <b>Send payment within 30 minutes:</b>\n\n"
        )

        for coin, address in CRYPTO_ADDRESSES.items():
            msg += f"<b>{coin}</b>: <code>{address}</code>\n"

        await query.edit_message_text(msg, parse_mode="HTML")


# =======================
#  CONVERT USERNAME → ID
# =======================

async def fetch_id(update, context, username):
    try:
        chat = await context.bot.get_chat(username.replace("@", ""))
        chat_id = chat.id

        await update.message.reply_html(
            f"🔍 <b>Result</b>\n\n"
            f"User: {username}\n"
            f"Telegram Number (ID): <code>{chat_id}</code>"
        )
    except:
        await update.message.reply_text("❌ Could not fetch that username.")


# =======================
#  MAIN
# =======================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("subscriptions", subscriptions))
    app.add_handler(CommandHandler("getnum", getnum))

    app.add_handler(CallbackQueryHandler(callback))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: None))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
