import json
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, \
    PreCheckoutQueryHandler, CallbackContext

from dotenv import load_dotenv, dotenv_values


config = dotenv_values(".env")

TG_TOKEN = config['TG_TOKEN']
PROVIDER_TOKEN = config['PROVIDER_TOKEN']

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
PACKETS, IRONING, ADDRESS, PAYMENT = range(4)

# Цены (в рублях, для примера)
PRICE_PER_PACKET = 500  # Цена за один пакет
IRONING_PRICE_PER_PACKET = 200  # Доплата за глажку за пакет

# Файл для хранения данных клиентов
CLIENTS_FILE = 'clients.json'


# Загрузка данных из JSON
def load_clients():
    try:
        with open(CLIENTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Сохранение данных в JSON
def save_clients(clients):
    with open(CLIENTS_FILE, 'w') as f:
        json.dump(clients, f, ensure_ascii=False, indent=4)


# Начало разговора
async def start(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info(f"User {user.id} started the conversation.")
    reply_keyboard = [['1', '2', '3'], ['4', '5', '6'], ['7', '8', '9'], ['/restart', '/cancel']]
    await update.message.reply_text(
        "Привет! Давайте оформим заказ на стирку.\n"
        "Сколько пакетов вы хотите отправить? (Выберите от 1 до 9)",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return PACKETS


# Обработка количества пакетов
async def packets(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if text == '/restart':
        return await start(update, context)
    try:
        packets = int(text)
        if packets < 1 or packets > 9:
            raise ValueError
        context.user_data['packets'] = packets
        reply_keyboard = [['Да', 'Нет'], ['/restart', '/cancel']]
        await update.message.reply_text(
            f"Ок, {packets} пакетов.\n"
            f"Нужна ли глажка? (Доплата {IRONING_PRICE_PER_PACKET} руб за пакет)",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return IRONING
    except ValueError:
        reply_keyboard = [['1', '2', '3'], ['4', '5', '6'], ['7', '8', '9'], ['/restart', '/cancel']]
        await update.message.reply_text(
            "Пожалуйста, выберите число от 1 до 9.",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return PACKETS


# Обработка выбора глажки
async def ironing(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if text == '/restart':
        return await start(update, context)
    ironing = text.lower() == 'да'
    context.user_data['ironing'] = ironing
    reply_keyboard = [['/restart', '/cancel']]
    await update.message.reply_text(
        "Укажите ваш адрес для доставки.",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )
    return ADDRESS


# Обработка адреса
async def address(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if text == '/restart':
        return await start(update, context)
    address = text
    context.user_data['address'] = address

    packets = context.user_data['packets']
    ironing = context.user_data['ironing']
    total_price = packets * PRICE_PER_PACKET
    if ironing:
        total_price += packets * IRONING_PRICE_PER_PACKET

    await update.message.reply_text(
        f"Адрес: {address}\n"
        f"Пакетов: {packets}\n"
        f"Глажка: {'Да' if ironing else 'Нет'}\n"
        f"Итоговая сумма: {total_price} руб.\n"
        "Теперь перейдем к оплате.",
        reply_markup=ReplyKeyboardRemove()
    )

    # Формируем invoice
    title = "Оплата за стирку"
    description = f"{packets} пакетов, глажка: {'Да' if ironing else 'Нет'}"
    payload = f"order_{update.message.from_user.id}_{context.user_data['packets']}"
    currency = "RUB"
    prices = [{"label": "Стирка", "amount": packets * PRICE_PER_PACKET * 100}]
    if ironing:
        prices.append({"label": "Глажка", "amount": packets * IRONING_PRICE_PER_PACKET * 100})

    await context.bot.send_invoice(
        chat_id=update.message.chat_id,
        title=title,
        description=description,
        payload=payload,
        provider_token=PROVIDER_TOKEN,  # Замените на ваш provider_token
        currency=currency,
        prices=prices
    )
    return PAYMENT


# Подтверждение оплаты (pre_checkout)
async def pre_checkout(update: Update, context: CallbackContext) -> None:
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("order_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Что-то пошло не так.")


# Успешная оплата
async def successful_payment(update: Update, context: CallbackContext) -> int:
    user_id = str(update.message.from_user.id)
    clients = load_clients()
    if user_id not in clients:
        clients[user_id] = []

    order = {
        'packets': context.user_data['packets'],
        'ironing': context.user_data['ironing'],
        'address': context.user_data['address'],
        'total': (context.user_data['packets'] * PRICE_PER_PACKET) + (
            context.user_data['packets'] * IRONING_PRICE_PER_PACKET if context.user_data['ironing'] else 0)
    }
    clients[user_id].append(order)
    save_clients(clients)

    await update.message.reply_text("Оплата прошла успешно! Заказ принят. Курьер скоро приедет.")
    context.user_data.clear()
    return ConversationHandler.END


# Отмена
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Заказ отменен.", reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END


# Рестарт
async def restart(update: Update, context: CallbackContext) -> int:
    return await start(update, context)


def main() -> None:
    # Замените 'YOUR_TELEGRAM_TOKEN' на токен вашего бота
    application = Application.builder().token(TG_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), MessageHandler(filters.TEXT & ~filters.COMMAND, start)],
        states={
            PACKETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, packets)],
            IRONING: [MessageHandler(filters.TEXT & ~filters.COMMAND, ironing)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, address)],
            PAYMENT: [MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment)],
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('restart', restart)],
    )

    application.add_handler(conv_handler)
    application.add_handler(PreCheckoutQueryHandler(pre_checkout))
    application.add_handler(CommandHandler('restart', restart))

    application.run_polling()


if __name__ == '__main__':
    main()
