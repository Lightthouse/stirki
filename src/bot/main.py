from telegram.ext import (
    Application,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from src.database import init_db, close_db
from src.bot.settings import tg_settings
from src.bot.states import OrderStates
from src.bot.handlers.start import start
from src.bot.handlers.reset import reset
from src.bot.handlers.help import help
from src.bot.handlers.order import (
    ask_phone,

    client_confirm_ok,
    client_confirm_edit,

    get_phone,
    get_name,

    get_street,
    get_house,
    get_apartment,
    get_entrance,

    select_services,

    payment_question,
    payment_yes,
    payment_no,
)



async def on_startup(app: Application):
    await init_db()


async def on_shutdown(app: Application):
    await close_db()



def main():
    app = (
        Application.builder()
        .token(tg_settings.BOT_TOKEN)
        .post_init(on_startup)
        .post_shutdown(on_shutdown)
        .build()
    )

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            # ── старт ─────────────────────────────
            OrderStates.INFO: [
                CallbackQueryHandler(ask_phone, pattern="^order$"),
            ],

            # ── подтверждение существующего клиента ─
            OrderStates.REUSE_QUESTION: [
                CallbackQueryHandler(client_confirm_ok, pattern="^client_ok$"),
                CallbackQueryHandler(client_confirm_edit, pattern="^client_edit$"),
            ],

            # ── ввод данных клиента ───────────────
            OrderStates.GET_PHONE: [
                MessageHandler(filters.CONTACT, get_phone),
            ],
            OrderStates.GET_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name),
            ],
            OrderStates.GET_STREET: [
                CallbackQueryHandler(get_street, pattern="^street_"),
            ],
            OrderStates.GET_HOUSE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_house),
            ],
            OrderStates.GET_APARTMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_apartment),
            ],
            OrderStates.GET_ENTRANCE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_entrance),
            ],

            # ── услуги ────────────────────────────
            OrderStates.SELECT_SERVICES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, select_services),
            ],

            # ── подтверждение и оплата ─────────────
            OrderStates.CONFIRM: [
                CallbackQueryHandler(payment_question, pattern="^confirm$"),
            ],
            OrderStates.PAYMENT_QUESTION: [
                CallbackQueryHandler(payment_yes, pattern="^paid_yes$"),
                CallbackQueryHandler(payment_no, pattern="^paid_no$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler('reset', reset))
    app.add_handler(CommandHandler('help', help))

    app.run_polling()


if __name__ == "__main__":
    main()
