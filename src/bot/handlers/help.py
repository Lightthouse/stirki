from telegram import Update
from telegram.ext import ContextTypes

from src.bot.texts import HELP_TEXT

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)