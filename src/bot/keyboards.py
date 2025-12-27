from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def start_keyboard():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🧺 Заказать стирку", callback_data="order")]]
    )


def phone_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Поделиться номером", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def streets_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Новорождественская", callback_data="street_nov")],
            [InlineKeyboardButton("Мытищинская", callback_data="street_mit")],
        ]
    )


def client_confirm_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Всё верно", callback_data="client_ok"),
                InlineKeyboardButton("✏️ Изменить", callback_data="client_edit"),
            ]
        ]
    )

def yes_no_keyboard(prefix: str):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Да", callback_data=f"{prefix}_yes"),
                InlineKeyboardButton("❌ Нет", callback_data=f"{prefix}_no"),
            ]
        ]
    )


def skip_keyboard(prefix: str):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("Пропустить", callback_data=f"{prefix}_skip")]]
    )


def confirm_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
                InlineKeyboardButton("❌ Отменить", callback_data="cancel"),
            ]
        ]
    )
