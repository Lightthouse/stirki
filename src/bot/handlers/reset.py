from src.repositories import Repository


async def reset(update, context):

    """Обработчик команды /reset для очистки базы данных"""
    reset_bd = await Repository.reset_db()

    await update.message.reply_text("✅ База данных успешно очищена!")