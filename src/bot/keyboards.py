from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from src.enums import ServiceCyrillicSlugMap
from src.addresses import STREETS_SLUG, HOUSE_STREET_MAP


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
    street_buttons = [[InlineKeyboardButton(street, callback_data=f'street_{slug}')] for street, slug in
                      STREETS_SLUG.items()]

    return InlineKeyboardMarkup(street_buttons)


def house_keyboard(street: str):
    houses_buttons = [[InlineKeyboardButton(house, callback_data=f'house_{house}')] for house in
                      HOUSE_STREET_MAP[street]]

    return InlineKeyboardMarkup(houses_buttons)


def bags_numbers_keyboard():
    return ReplyKeyboardMarkup(
        [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
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


def services_keyboard(selected: dict[str, bool] | None = None) -> ReplyKeyboardMarkup:
    if selected is None:
        selected = {}

    def btn_text(name: str, key: str) -> str:
        mark = "✅" if selected.get(key, False) else "⬜"
        return f"{mark} {name}"

    keyboard = [[KeyboardButton(name)] for name, slug in ServiceCyrillicSlugMap.items()]
    keyboard.append([KeyboardButton("✅ Готово")])

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,  # остаётся до конца выбора
    )


def services_keyboard_compact(selected: dict[str, bool] | None = None) -> ReplyKeyboardMarkup:
    if selected is None:
        selected = {}

    def mark(key: str) -> str:
        return "✅" if selected.get(key, False) else ""

    return ReplyKeyboardMarkup(
        [
            [
                f"{mark('need_ironing')} Глажка",
                f"{mark('need_uv')} УФ",
            ],
            [
                f"{mark('need_conditioner')} Кондиционер",
                f"{mark('need_wash_bag')} Мешок",
            ],
            [
                f"{mark('need_vacuum_pack')} Вакуум",
                "✅ Готово",
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
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
