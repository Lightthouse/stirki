from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from src.repositories import Repository
from src.enums import PaymentStatus, OrderStatusName

from src.bot.states import OrderStates
from src.bot import texts
from src.bot.keyboards import (
    phone_keyboard,
    streets_keyboard,
    yes_no_keyboard,
    confirm_keyboard,
    client_confirm_keyboard
)


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    client = await Repository.get_client_by_telegram_id(telegram_id)


    if client:
        # Клиент найден
        context.user_data["client_id"] = client.id
        context.user_data["client_exists"] = True
        context.user_data["client_changed"] = False

        street = await Repository.resolve_client_street(client)
        text = texts.ASK_REUSE_USER_SETTINGS_TEXT.format(
            name=client.name,
            street=street,
            apartment=client.apartment,
            house=client.house
        )

        await query.edit_message_text(
            text,
            reply_markup=client_confirm_keyboard(),
        )
        return OrderStates.CLIENT_CONFIRM

    # Клиента нет — идём стандартным путём
    context.user_data["client_exists"] = False
    context.user_data["client_changed"] = True

    # await query.edit_message_text(texts.ASK_PHONE_TEXT)
    await query.message.reply_text(
        texts.ASK_PHONE_TEXT,
        reply_markup=phone_keyboard(),
    )
    return OrderStates.GET_PHONE

async def client_confirm_ok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    client = await Repository.get_client_by_telegram_id(telegram_id)
    street = await Repository.resolve_client_street(client)

    # Кладём данные клиента в context, чтобы дальше всё было единообразно
    context.user_data.update(
        {
            "name": client.name,
            "phone": client.phone,
            "street": street,
            "house": client.house,
            "apartment": client.apartment,
            "entrance": client.entrance,
        }
    )

    await query.edit_message_text(
        "Отлично 👍\n\nПерейдём к дополнительным услугам."
    )

    # Переходим сразу к первому вопросу заказа
    await query.message.reply_text(
        "Нужна глажка?",
        reply_markup=yes_no_keyboard("ironing"),
    )
    return OrderStates.NEED_IRONING

async def client_confirm_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["client_changed"] = True


    # await query.edit_message_text(texts.ASK_PHONE_TEXT)
    await query.message.reply_text(
        texts.CONFIRM_TEXT,
        reply_markup=phone_keyboard(),
    )
    return OrderStates.GET_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.contact.phone_number
    context.user_data["client_changed"] = True

    await update.message.reply_text(
        texts.ASK_NAME_TEXT,
        reply_markup=ReplyKeyboardRemove(),
    )
    return OrderStates.GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(texts.ASK_STREET_TEXT, reply_markup=streets_keyboard())
    return OrderStates.GET_STREET


async def get_street(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    street_name = query.data.split('_')[1]
    street_map = {
        'nov': 'Новорождественская',
        'mit': 'Мытищинская',
    }

    context.user_data["street"] = street_map.get(street_name, 'Мытищинская')
    await query.edit_message_text(texts.ASK_HOUSE_TEXT)
    return OrderStates.GET_HOUSE


async def get_house(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["house"] = update.message.text.strip()
    await update.message.reply_text(texts.ASK_APARTMENT_TEXT)
    return OrderStates.GET_APARTMENT


async def get_apartment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["apartment"] = update.message.text.strip()
    await update.message.reply_text(texts.ASK_ENTRANCE_TEXT)
    return OrderStates.GET_ENTRANCE

async def get_entrance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["entrance"] = update.message.text.strip()
    await update.message.reply_text(
        "Нужна глажка?",
        reply_markup=yes_no_keyboard("ironing"),
    )
    return OrderStates.NEED_IRONING

async def set_ironing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["need_ironing"] = update.callback_query.data.endswith("yes")
    await update.callback_query.edit_message_text(
        "Использовать ультрафиолет?",
        reply_markup=yes_no_keyboard("uv"),
    )
    return OrderStates.NEED_UV

async def set_uv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["need_uv"] = update.callback_query.data.endswith("yes")
    await update.callback_query.edit_message_text(
        "Добавить кондиционер?",
        reply_markup=yes_no_keyboard("conditioner"),
    )
    return OrderStates.NEED_CONDITIONER

async def set_conditioner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["need_conditioner"] = update.callback_query.data.endswith("yes")
    await update.callback_query.edit_message_text(
        "Использовать мешок для стирки?",
        reply_markup=yes_no_keyboard("wash_bag"),
    )
    return OrderStates.NEED_WASH_BAG

async def set_wash_bag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["need_wash_bag"] = update.callback_query.data.endswith("yes")
    await update.callback_query.edit_message_text(
        "Упаковать в вакуумный пакет?",
        reply_markup=yes_no_keyboard("vacuum_pack"),
    )
    return OrderStates.NEED_VACUUM_PACK

async def set_vacuum_pack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data["need_vacuum_pack"] = update.callback_query.data.endswith("yes")

    # Переходим сразу к подтверждению
    services = []
    for key, label in [
        ("need_ironing", "Глажка"),
        ("need_uv", "УФ обработка"),
        ("need_conditioner", "Кондиционер"),
        ("need_wash_bag", "Мешок для стирки"),
        ("need_vacuum_pack", "Вакуумный пакет"),
    ]:
        if context.user_data.get(key):
            services.append(f"• {label}")

    text = texts.CONFIRM_TEXT.format(
        name=context.user_data["name"],
        phone=context.user_data["phone"],
        street=context.user_data["street"],
        house=context.user_data["house"],
        apartment=context.user_data["apartment"],
        entrance=context.user_data.get("entrance"),
        services="\n".join(services) or "Нет",
    )

    await update.callback_query.edit_message_text(
        text,
        reply_markup=confirm_keyboard(),
    )
    return OrderStates.CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    services = []
    for key, label in [
        ("need_ironing", "Глажка"),
        ("need_uv", "УФ обработка"),
        ("need_conditioner", "Кондиционер"),
        ("need_wash_bag", "Мешок для стирки"),
        ("need_vacuum_pack", "Вакуумный пакет"),
    ]:
        if context.user_data.get(key):
            services.append(f"• {label}")

    text = texts.CONFIRM_TEXT.format(
        name=context.user_data["name"],
        phone=context.user_data["phone"],
        street=context.user_data["street"],
        house=context.user_data["house"],
        apartment=context.user_data["apartment"],
        entrance=context.user_data.get("entrance"),
        services="\n".join(services) or "Нет",
    )

    await update.callback_query.edit_message_text(
        text,
        reply_markup=confirm_keyboard(),
    )
    return OrderStates.CONFIRM



async def payment_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    telegram_id = query.from_user.id
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    if not context.user_data["client_exists"]:
        client = await Repository.create_client(
            telegram_id=telegram_id,
            name=context.user_data["name"],
            phone=context.user_data["phone"],
            street=context.user_data["street"],
            house=context.user_data["house"],
            apartment=context.user_data["apartment"],
            entrance=context.user_data["entrance"],
        )
    elif context.user_data["client_changed"]:
        client = await Repository.update_client(
            telegram_id=telegram_id,
            name=context.user_data["name"],
            phone=context.user_data["phone"],
            street=context.user_data["street"],
            house=context.user_data["house"],
            apartment=context.user_data["apartment"],
            entrance=context.user_data["entrance"],
        )
    else:
        client = await Repository.get_client_by_telegram_id(telegram_id)

    order = await Repository.create_order(
        client=client,

        telegram_chat_id=chat_id,
        telegram_message_id=message_id,

        need_ironing=context.user_data.get('need_ironing', False),
        need_conditioner=context.user_data.get('need_conditioner', False),
        need_vacuum_pack=context.user_data.get('need_vacuum_pack', False),
        need_uv=context.user_data.get('need_uv', False),
        need_wash_bag=context.user_data.get('need_wash_bag', False),
    )

    context.user_data["order_id"] = order.id

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        texts.PAYMENT_QUESTION_TEXT,
        reply_markup=yes_no_keyboard("paid"),
    )

    return OrderStates.PAYMENT_QUESTION

async def payment_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    services = []
    for key, label in [
        ("need_ironing", "Глажка"),
        ("need_uv", "УФ обработка"),
        ("need_conditioner", "Кондиционер"),
        ("need_wash_bag", "Мешок для стирки"),
        ("need_vacuum_pack", "Вакуумный пакет"),
    ]:
        if context.user_data.get(key):
            services.append(f"• {label}")

    text = texts.SUCCESS_TEXT.format(
        name=context.user_data["name"],
        phone=context.user_data["phone"],
        street=context.user_data["street"],
        house=context.user_data["house"],
        apartment=context.user_data["apartment"],
        entrance=context.user_data.get("entrance") or "-",
        services="\n".join(services) or "Нет",
    )


    order_id = context.user_data["order_id"]
    update_order = await Repository.update_order_status(order_id, OrderStatusName.NEW, PaymentStatus.SUCCEEDED)

    await query.edit_message_text(
        text
    )

    return ConversationHandler.END

async def payment_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = context.user_data["order_id"]
    update_order = await Repository.update_order_status(order_id, OrderStatusName.CANCELED, PaymentStatus.CANCELED)


    await query.edit_message_text(
        texts.CANCEL_TEXT
    )

    return ConversationHandler.END