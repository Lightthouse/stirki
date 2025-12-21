from telegram import Update
from telegram.ext import ContextTypes, PreCheckoutQueryHandler


from telegram import Update
from telegram.ext import ContextTypes

from src.repositories import Repository
from src.enums import PaymentStatus
from src.bot.texts import ORDER_CREATED_TEXT


async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    payload = payment.invoice_payload

    # payload = "order:123"
    order_id = int(payload.split(":")[1])

    repo = Repository()

    # 1. Обновляем статус платежа и заказа
    order = await repo.update_payment_status(
        order_id=order_id,
        status_name=PaymentStatus.SUCCEEDED,
    )

    # 2. Отправляем статусное сообщение
    msg = await update.message.reply_text(
        ORDER_CREATED_TEXT.format(status="заказ оплачен")
    )

    # 3. Сохраняем message_id для дальнейших апдейтов
    await repo.attach_telegram_message(
        order_id=order.id,
        chat_id=msg.chat.id,
        message_id=msg.message_id,
    )

async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    await query.answer(ok=True)


precheckout_query_handler = PreCheckoutQueryHandler(precheckout_handler)
