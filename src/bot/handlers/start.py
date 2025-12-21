from telegram import Update
from telegram.ext import ContextTypes

from src.bot.texts import WELCOME_TEXT
from src.bot.keyboards import start_keyboard
from src.bot.states import OrderStates


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=start_keyboard(),
    )
    return OrderStates.INFO
