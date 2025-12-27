from icecream import ic

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from src.repositories import Repository
from src.enums import PaymentStatus, OrderStatusName, ServiceCyrillic, ServiceSlug, ServiceCyrillicSlugMap

from src.bot.states import OrderStates
from src.bot import texts
from src.bot.keyboards import (
    phone_keyboard,
    streets_keyboard,
    yes_no_keyboard,
    confirm_keyboard,
    client_confirm_keyboard,
    services_keyboard,
    services_keyboard_compact
)

from src.services.pricing import Pricing


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
            house=client.house,
            phone=client.phone
        )

        await query.edit_message_text(text, reply_markup=client_confirm_keyboard())
        return OrderStates.REUSE_QUESTION

    # Клиента нет — идём стандартным путём
    context.user_data["client_exists"] = False
    context.user_data["client_changed"] = True

    # await query.edit_message_text(texts.ASK_PHONE_TEXT)
    await query.message.reply_text(texts.ASK_PHONE_TEXT, reply_markup=phone_keyboard())
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

    await query.message.reply_text( "Отлично! Теперь можете выбрать дополнительные услуги\n", reply_markup=services_keyboard())
    return OrderStates.SELECT_SERVICES


async def client_confirm_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["client_changed"] = True

    await query.message.reply_text(texts.ASK_PHONE_TEXT, reply_markup=phone_keyboard())
    return OrderStates.GET_PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.contact.phone_number
    context.user_data["client_changed"] = True

    await update.message.reply_text(texts.ASK_NAME_TEXT, reply_markup=ReplyKeyboardRemove())
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

    await update.message.reply_text(texts.ASK_SERVICES, reply_markup=services_keyboard())
    return OrderStates.SELECT_SERVICES


async def select_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    services = context.user_data.get("services", {service: False for service in ServiceSlug})


    if "Готово" in text:
        current_services_text = Pricing.total_price_message(services)
        order_total_price = f"{current_services_text}\n\n"

        confirm_text = texts.ORDER_CHECKUP_TEXT.format(
            name=context.user_data["name"],
            phone=context.user_data["phone"],
            street=context.user_data["street"],
            house=context.user_data["house"],
            apartment=context.user_data["apartment"],
            entrance=context.user_data["entrance"],
            services=order_total_price,
        )

        context.user_data['order_price'] = current_services_text

        await update.message.reply_text(confirm_text, reply_markup=ReplyKeyboardRemove())
        await update.message.reply_text("Всё верно?\nПодтвердите заказ:", reply_markup=confirm_keyboard())

        return OrderStates.CONFIRM

    if text in ServiceCyrillic:
        services[ServiceCyrillicSlugMap[text]] = not services[ServiceCyrillicSlugMap[text]]

        context.user_data['services'] = services

        current_services_text = Pricing.services_price_message(services)
        services_price = f"{current_services_text}\n\nПродолжайте выбор или нажмите «Готово»"
        await update.message.reply_text(services_price, reply_markup=services_keyboard(services))


    return OrderStates.SELECT_SERVICES


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = texts.CONFIRM_TEXT.format(
        name=context.user_data["name"],
        phone=context.user_data["phone"],
        street=context.user_data["street"],
        house=context.user_data["house"],
        apartment=context.user_data["apartment"],
        entrance=context.user_data["entrance"],
        services=context.user_data["order_price"],
    )

    await update.callback_query.edit_message_text(text, reply_markup=confirm_keyboard())
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
        services=context.user_data['services']
    )

    context.user_data["order_id"] = order.id

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(texts.PAYMENT_QUESTION_TEXT, reply_markup=yes_no_keyboard("paid"))

    return OrderStates.PAYMENT_QUESTION


async def payment_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text = texts.SUCCESS_TEXT.format(
        name=context.user_data["name"],
        phone=context.user_data["phone"],
        street=context.user_data["street"],
        house=context.user_data["house"],
        apartment=context.user_data["apartment"],
        entrance=context.user_data["entrance"],
        services=context.user_data["order_price"],
    )

    order_id = context.user_data["order_id"]
    update_order = await Repository.update_order_status(order_id, OrderStatusName.NEW, PaymentStatus.SUCCEEDED)

    await query.edit_message_text(text)

    return ConversationHandler.END


async def payment_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = context.user_data["order_id"]
    update_order = await Repository.update_order_status(order_id, OrderStatusName.CANCELED, PaymentStatus.CANCELED)

    await query.edit_message_text(texts.CANCEL_TEXT)

    return ConversationHandler.END
