import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from markupsafe import Markup, escape
from sqladmin import Admin, BaseView, ModelView, expose
from sqladmin.fields import FileField
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import ColumnElement, Select, case
from starlette.requests import Request
from jinja2 import ChoiceLoader, PackageLoader, PrefixLoader
from wtforms import Form, SelectField, StringField, TextAreaField
from wtforms.validators import NumberRange, Optional, Regexp, ValidationError

from src.addresses import STREETS_SLUG
from src.enums import HANDOVER_LABELS, OrderStatusName, PaymentStatus
from src.database import async_session, engine
from src.models.analytics import Ad, AdViewStats, LandingVisitStats, SmsSend
from src.models.client import Client
from src.models.order import Order, OrderStatus, OrderStatusHistory
from src.models.service import Service
from src.models.site_text import SITE_TEXT_NAMES, SiteText
from src.models.system_settings import SystemSettings
from src.services.ads import ALLOWED_EXTENSIONS, AdUploadError, delete_ad_file, save_ad_file
from src.services.auth import parse_phone_list, phone_digits
from src.services.notifications import parse_email_list
from src.services.schedule import MSK, now_msk, time_to_minutes
from src.settings import AppSettings

_SLUG_TO_STREET = {slug: name for name, slug in STREETS_SLUG.items()}

_TEMPLATES_DIR = Path(__file__).parent / "admin_templates"


def _msk(value: datetime | None) -> str:
    """Время из БД (UTC) → московское, в читаемом виде для сотрудников."""
    return value.astimezone(MSK).strftime("%d.%m.%Y %H:%M") if value else "—"


def _msk_formatters(*fields: str) -> dict:
    return {f: (lambda m, a, f=f: _msk(getattr(m, f))) for f in fields}


class RussianForm(Form):
    """Формы админки со встроенными русскими сообщениями WTForms («Обязательное поле» и т.п.)."""

    class Meta:
        locales = ["ru_RU", "ru"]


class BaseAdmin(ModelView):
    """Общее для всех разделов: 50 строк на странице, шаблон списка с кнопкой «Столбцы», русские формы."""

    page_size = 50
    page_size_options = [25, 50, 100, 200]
    list_template = "list.html"
    form_base_class = RussianForm


class ChoiceFilter:
    """Фильтр-список для боковой панели sqladmin: подписи по-русски, условие задаётся функцией.

    Встроенные фильтры sqladmin пишут «All / Yes / No» и умеют только «поле = значение».
    """

    has_operator = False

    def __init__(self, parameter_name: str, title: str, choices: list[tuple[str, str]],
                 where: Callable[[str], ColumnElement[bool]]):
        self.parameter_name = parameter_name
        self.title = title
        self.choices = choices
        self.where = where

    async def lookups(self, request: Request, model: Any, run_query: Any) -> list[tuple[str, str]]:
        return [("", "Все"), *self.choices]

    async def get_filtered_query(self, query: Select, value: Any, model: Any) -> Select:
        if value not in dict(self.choices):
            return query
        return query.filter(self.where(value))


def _period_bounds(period: str) -> tuple[datetime, datetime | None]:
    """Начало и конец периода по МСК: сутки считаются по московскому времени, как и всё в сервисе."""
    today = now_msk().replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "today":
        return today, None
    if period == "yesterday":
        return today - timedelta(days=1), today
    if period == "week":
        return today - timedelta(days=6), None
    if period == "month":
        return today - timedelta(days=29), None
    return today.replace(day=1), None  # this_month


def date_filter(column: Any, title: str) -> ChoiceFilter:
    def where(period: str) -> ColumnElement[bool]:
        start, end = _period_bounds(period)
        return (column >= start) & (column < end) if end else column >= start

    return ChoiceFilter(
        parameter_name=column.key,
        title=title,
        choices=[("today", "Сегодня"), ("yesterday", "Вчера"), ("week", "7 дней"),
                 ("month", "30 дней"), ("this_month", "Этот месяц")],
        where=where,
    )


def bool_filter(column: Any, title: str, yes: str = "Да", no: str = "Нет") -> ChoiceFilter:
    return ChoiceFilter(column.key, title, [("1", yes), ("0", no)], lambda v: column.is_(v == "1"))


# Статусы в порядке жизни заказа — для фильтра и для сортировки по статусу.
_STATUS_ORDER = [
    (OrderStatusName.WAITING_PAYMENT, "Ожидает оплаты"),
    (OrderStatusName.COURIER_PICKUP, "В пути"),
    (OrderStatusName.PICKED_UP, "Забрали"),
    (OrderStatusName.WASHING, "Чистим"),
    (OrderStatusName.COURIER_DELIVERY, "Идём отдавать"),
    (OrderStatusName.DELIVERED, "Доставлено"),
    (OrderStatusName.CANCELED, "Отменено"),
]

_PAYMENT_LABELS = {
    PaymentStatus.PENDING: "Ожидает оплаты",
    PaymentStatus.SUCCEEDED: "Оплачен",
    PaymentStatus.CANCELED: "Отменён",
}
_WASHING_TYPE_LABELS = {"bag": "Пакет", "piece": "Вещь", "mixed": "Пакеты и вещи"}
_CHANGED_BY_LABELS = {
    "system": "Система", "admin": "Администратор", "tochka": "Точка (оплата)", "client": "Клиент",
}


class HelpView(BaseView):
    name = "Инструкция"
    icon = "fa-solid fa-circle-question"

    @expose("/help", methods=["GET"])
    async def help_page(self, request: Request):
        return await self.templates.TemplateResponse(request, "help.html")


class AdminAuth(AuthenticationBackend):
    def __init__(self, secret_key: str, username: str, password: str):
        super().__init__(secret_key=secret_key)
        self._username = username
        self._password = password

    async def login(self, request: Request) -> bool:
        form = await request.form()
        if form.get("username") == self._username and form.get("password") == self._password:
            request.session["admin"] = "ok"
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("admin") == "ok"


class OrderAdmin(BaseAdmin, model=Order):
    name = "Заказ"
    name_plural = "Заказы"
    icon = "fa-solid fa-basket-shopping"

    # Заказы не удаляются из админки (решение 2026-11-20): настоящий заказ отменяют, тестовые удаляет
    # разработчик запросом к БД (README, «Удаление тестовых заказов»).
    can_delete = False

    column_list = [
        Order.id,
        Order.created_at,
        "client",
        Order.street,
        Order.house,
        Order.apartment,
        "status",
        Order.washing_type,
        Order.bags_number,
        Order.pieces_number,
        Order.total_price_rub,
        Order.payment_status,
        Order.next_day_delivery,
        Order.handover,
    ]
    column_details_list = "__all__"
    # № платежа в Точке — чтобы найти заказ по реестру платежей Точки (ST-123-K7Q2).
    column_searchable_list = [Order.street, Order.house, Order.payment_link_id]

    def search_query(self, stmt: Select, term: str) -> Select:
        """«ST-123» или «123» — точный поиск по номеру заказа (в т.ч. бесплатного, без платежа)."""
        match = re.fullmatch(r"(?:st-?)?(\d+)", term.strip(), flags=re.IGNORECASE)
        if match:
            return stmt.filter(Order.id == int(match.group(1)))
        return super().search_query(stmt, term)

    def search_placeholder(self) -> str:
        return "№ заказа (ST-123), № платежа, улица, дом"
    column_sortable_list = [
        Order.id, Order.created_at, "status", Order.street, Order.total_price_rub,
        Order.payment_status, Order.next_day_delivery, Order.handover,
    ]
    column_default_sort = [(Order.created_at, True)]

    column_filters = [
        ChoiceFilter("status", "Статус", [(slug.value, name) for slug, name in _STATUS_ORDER],
                     lambda v: Order.status.has(OrderStatus.slug == v)),
        date_filter(Order.created_at, "Создан"),
        ChoiceFilter("is_free", "Тариф", [("1", "Бесплатный"), ("0", "Платный")],
                     lambda v: Order.is_free.is_(v == "1")),
        ChoiceFilter("payment_status", "Оплата", [(k.value, v) for k, v in _PAYMENT_LABELS.items()],
                     lambda v: Order.payment_status == v),
        ChoiceFilter("handover", "Передача", [(k.value, v) for k, v in HANDOVER_LABELS.items()],
                     lambda v: Order.handover == v),
        bool_filter(Order.next_day_delivery, "Доставка завтра"),
    ]

    def sort_query(self, stmt: Select, request: Request) -> Select:
        """По статусу — в порядке жизни заказа (а не по алфавиту или id), внутри статуса — новые сверху."""
        if request.query_params.get("sortBy") != "status":
            return super().sort_query(stmt, request)
        rank = case({slug.value: i for i, (slug, _) in enumerate(_STATUS_ORDER)}, value=OrderStatus.slug)
        rank = rank.desc() if request.query_params.get("sort") == "desc" else rank.asc()
        return stmt.join(Order.status).order_by(rank, Order.created_at.desc())

    column_labels = {
        "id": "№",
        "client_id": "Клиент ID",
        "is_free": "Бесплатный тариф",
        "payment_token": "Токен возврата после оплаты",
        "client": "Клиент",
        "history": "История",
        "street": "Улица",
        "house": "Дом",
        "apartment": "Кв.",
        "entrance": "Подъезд",
        "floor": "Этаж",
        "comment": "Комментарий",
        "next_day_delivery": "Доставка завтра",
        "handover": "Передача",
        "status": "Статус",
        "status_id": "Статус ID",
        "washing_type": "Тип стирки",
        "bags_number": "Мешков",
        "pieces_number": "Вещей",
        "ironing": "Глажка",
        "conditioner": "Кондиционер",
        "vacuum_pack": "Вакуум",
        "stain_remover": "Пятновыводитель",
        "laundry_net": "Стирка в мешке",
        "bleach": "Отбеливатель",
        "color_catcher_sheets": "Салфетки (ловушки цвета)",
        "bag_price_rub": "Цена пакета (на момент заказа)",
        "piece_price_rub": "Цена вещи (на момент заказа)",
        "steaming": "Отпаривание",
        "hypoallergenic_conditioner": "Кондиционер гипоаллергенный",
        "no_conditioner": "Не добавлять кондиционер",
        "total_price_rub": "Цена (₽)",
        "payment_status": "Оплата",
        "payment_link": "Ссылка оплаты",
        "payment_link_id": "№ платежа в Точке",
        "operation_id": "ID операции в Точке",
        "created_at": "Создан",
        "updated_at": "Обновлён",
    }

    column_formatters = {
        "id": lambda m, a: m.number,
        "street": lambda m, a: _SLUG_TO_STREET.get(m.street, m.street),
        "status": lambda m, a: str(m.status) if m.status else "—",
        "client": lambda m, a: f"{m.client.name or '—'}, {m.client.phone}" if m.client else "—",
        "handover": lambda m, a: HANDOVER_LABELS.get(m.handover, m.handover),
        "payment_status": lambda m, a: _PAYMENT_LABELS.get(m.payment_status, m.payment_status),
        "washing_type": lambda m, a: _WASHING_TYPE_LABELS.get(m.washing_type, m.washing_type),
        **_msk_formatters("created_at", "updated_at"),
    }
    column_formatters_detail = column_formatters

    form_include_pk = False
    form_columns = [
        'status',
        Order.comment,
        Order.handover,
        Order.payment_status,
    ]
    # Передачу можно поменять, если клиент попросил по телефону. Списки вместо textarea, которую sqladmin делает для Text.
    form_overrides = {"handover": SelectField, "payment_status": SelectField}
    form_args = {
        "handover": {"choices": [(k.value, v) for k, v in HANDOVER_LABELS.items()]},
        "payment_status": {"choices": [(k.value, v) for k, v in _PAYMENT_LABELS.items()]},
    }
    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        request.state.prev_status_id = None if is_created else model.status_id

    async def after_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        status_val = data.get('status')
        if not status_val:
            return
        new_status_id = int(status_val)
        old_status_id = getattr(request.state, 'prev_status_id', None)
        if is_created or old_status_id != new_status_id:
            async with async_session() as session:
                session.add(OrderStatusHistory(
                    order_id=model.id,
                    status_id=new_status_id,
                    changed_by='admin',
                ))
                await session.commit()


class OrderStatusAdmin(BaseAdmin, model=OrderStatus):
    name = "Статус"
    name_plural = "Статусы заказов"
    icon = "fa-solid fa-list-check"

    column_list = [OrderStatus.id, OrderStatus.slug, OrderStatus.name]
    column_labels = {
        "id": "ID",
        "slug": "Slug",
        "name": "Название",
    }

    can_create = False
    can_edit = False
    can_delete = False


class ClientAdmin(BaseAdmin, model=Client):
    name = "Клиент"
    name_plural = "Клиенты"
    icon = "fa-solid fa-users"

    column_list = [
        Client.id,
        Client.phone,
        Client.name,
        Client.street,
        Client.house,
        Client.apartment,
        Client.is_verified,
        Client.sms_marketing_consent_at,
        Client.total_orders,
        Client.registered_at,
    ]
    column_details_exclude_list = [
        Client.auth_token,
        Client.verification_code,
    ]
    column_formatters = {
        "street": lambda m, a: _SLUG_TO_STREET.get(m.street, m.street),
        **_msk_formatters(
            "registered_at", "offer_accepted_at", "sms_marketing_consent_at",
            "auth_token_expires_at", "verification_expires_at", "verification_sent_at",
        ),
    }
    column_formatters_detail = column_formatters

    # email — чтобы найти клиента по кассовому чеку
    column_searchable_list = [Client.phone, Client.name, Client.email]
    column_sortable_list = [Client.id, Client.name, Client.street, Client.registered_at, Client.total_orders]
    column_default_sort = [(Client.registered_at, True)]
    column_filters = [
        date_filter(Client.registered_at, "Зарегистрирован"),
        ChoiceFilter("sms_marketing_consent_at", "Согласие на рассылку", [("1", "Есть"), ("0", "Нет")],
                     lambda v: Client.sms_marketing_consent_at.isnot(None) if v == "1"
                     else Client.sms_marketing_consent_at.is_(None)),
        bool_filter(Client.is_verified, "Верифицирован"),
    ]

    column_labels = {
        "id": "ID",
        "phone": "Телефон",
        "name": "Имя",
        "email": "Email",
        "is_verified": "Верифицирован",
        "street": "Улица",
        "house": "Дом",
        "apartment": "Кв.",
        "entrance": "Подъезд",
        "floor": "Этаж",
        "comment": "Комментарий",
        "total_orders": "Заказов",
        "registered_at": "Зарегистрирован",
        "offer_accepted_at": "Принял оферту",
        "sms_marketing_consent_at": "Согласие на рассылку",
        "auth_token_expires_at": "Вход действует до",
        "verification_expires_at": "Код входа действует до",
        "verification_attempts": "Неверных вводов кода",
        "verification_sent_at": "Код отправлен",
        "orders": "Заказы",
    }

    can_create = False
    can_delete = False
    form_columns = [Client.name, Client.email, Client.comment]


class ServiceAdmin(BaseAdmin, model=Service):
    name = "Услуга"
    name_plural = "Услуги"
    icon = "fa-solid fa-tags"

    column_list = [Service.id, Service.name, Service.slug, Service.price_rub, Service.is_active]
    column_labels = {
        "id": "ID",
        "name": "Название",
        "slug": "Slug",
        "price_rub": "Цена (₽)",
        "is_active": "Активна",
    }

    can_create = False
    can_delete = False
    form_columns = [Service.name, Service.price_rub, Service.is_active]


def _validate_phone_list(form: Any, field: Any) -> None:
    """Каждый номер в списке — 11 цифр с 7 (как на странице входа)."""
    items = [p.strip() for p in re.split(r"[,;\n]", field.data or "") if p.strip()]
    bad = [p for p in items if not re.fullmatch(r"7\d{10}", phone_digits(p))]
    if bad:
        raise ValidationError(f"Неверный номер: {', '.join(bad)}. Нужно 11 цифр, например +7 999 999-99-99")


def _validate_email_list(form: Any, field: Any) -> None:
    """Каждый адрес в списке похож на email."""
    bad = [a for a in parse_email_list(field.data or "") if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", a)]
    if bad:
        raise ValidationError(f"Неверный email: {', '.join(bad)}")


class SystemSettingsAdmin(BaseAdmin, model=SystemSettings):
    name = "Настройки"
    name_plural = "Системные настройки"
    icon = "fa-solid fa-sliders"

    column_list = [
        SystemSettings.free_tariff_is_available,
        SystemSettings.promo_enabled,
        SystemSettings.promo_bag_price,
        SystemSettings.promo_piece_price,
        SystemSettings.promo_label,
        SystemSettings.sms_enabled,
        SystemSettings.debug_phones_enabled,
        SystemSettings.debug_phones,
        SystemSettings.sms_ip_limit_10min,
        SystemSettings.sms_ip_limit_day,
        SystemSettings.sms_ip_limit_week,
        SystemSettings.free_bag_slots,
        SystemSettings.free_piece_slots,
        SystemSettings.paid_bag_slots,
        SystemSettings.paid_piece_slots,
        SystemSettings.order_accept_from,
        SystemSettings.order_accept_to,
        SystemSettings.next_day_delivery_from_hour,
        SystemSettings.free_orders_per_address_per_day,
        SystemSettings.ad_count,
        SystemSettings.ad_duration_sec,
        SystemSettings.support_phone,
        SystemSettings.support_telegram,
        SystemSettings.support_email,
        SystemSettings.notify_emails,
    ]
    column_labels = {
        "id": "ID",
        "free_tariff_is_available": "Бесплатный тариф доступен",
        "promo_enabled": "Акция включена",
        "promo_bag_price": "Акция: цена пакета (₽)",
        "promo_piece_price": "Акция: цена вещи (₽)",
        "promo_label": "Акция: надпись на сайте",
        "sms_enabled": "Вход по SMS (отправлять коды)",
        "debug_phones_enabled": "Отладочные номера включены",
        "debug_phones": "Отладочные номера",
        "sms_ip_limit_10min": "SMS с одного IP: за 10 минут",
        "sms_ip_limit_day": "SMS с одного IP: за сутки",
        "sms_ip_limit_week": "SMS с одного IP: за неделю",
        "free_bag_slots": "Бесплатный: пакеты (макс.)",
        "free_piece_slots": "Бесплатный: вещи (макс.)",
        "paid_bag_slots": "Платный: пакеты (макс.)",
        "paid_piece_slots": "Платный: вещи (макс.)",
        "order_accept_from": "Приём заказов с (ЧЧ:ММ, МСК)",
        "order_accept_to": "Приём заказов до (ЧЧ:ММ, МСК)",
        "next_day_delivery_from_hour": "Доставка на след. день для заказов с (час, МСК)",
        "free_orders_per_address_per_day": "Бесплатных заказов на адрес в сутки",
        "ad_count": "Реклама: картинок за просмотр",
        "ad_duration_sec": "Реклама: секунд на картинку",
        "support_phone": "Поддержка: телефон",
        "support_telegram": "Поддержка: Telegram",
        "support_email": "Поддержка: email",
        "notify_emails": "Уведомления о заказах: email",
    }

    can_create = False
    can_delete = False
    form_columns = [
        SystemSettings.free_tariff_is_available,
        SystemSettings.promo_enabled,
        SystemSettings.promo_bag_price,
        SystemSettings.promo_piece_price,
        SystemSettings.promo_label,
        SystemSettings.sms_enabled,
        SystemSettings.debug_phones_enabled,
        SystemSettings.debug_phones,
        SystemSettings.sms_ip_limit_10min,
        SystemSettings.sms_ip_limit_day,
        SystemSettings.sms_ip_limit_week,
        SystemSettings.free_bag_slots,
        SystemSettings.free_piece_slots,
        SystemSettings.paid_bag_slots,
        SystemSettings.paid_piece_slots,
        SystemSettings.order_accept_from,
        SystemSettings.order_accept_to,
        SystemSettings.next_day_delivery_from_hour,
        SystemSettings.free_orders_per_address_per_day,
        SystemSettings.ad_count,
        SystemSettings.ad_duration_sec,
        SystemSettings.support_phone,
        SystemSettings.support_telegram,
        SystemSettings.support_email,
        SystemSettings.notify_emails,
    ]
    # Контакты — однострочные поля, а не textarea, которую sqladmin делает для Text.
    form_overrides = {
        f: StringField
        for f in (
            "debug_phones", "support_phone", "support_telegram", "support_email", "notify_emails", "promo_label",
            "order_accept_from", "order_accept_to",
        )
    }
    form_args = {
        "order_accept_from": {
            "validators": [Regexp(r"^\s*([01]?\d|2[0-3]):[0-5]\d\s*$", message="Время в виде 7:30 или 09:00")],
            "description": "Например 7:30. Заказы принимаются с этого времени включительно.",
        },
        "order_accept_to": {
            "validators": [Regexp(r"^\s*(([01]?\d|2[0-3]):[0-5]\d|24:00)\s*$", message="Время в виде 21:00 (24:00 — до конца суток)")],
            "description": "Например 21:00 — последний заказ в 20:59. 24:00 — до конца суток.",
        },
        # 24 — доставка на следующий день не применяется никогда.
        "next_day_delivery_from_hour": {"validators": [NumberRange(0, 24)]},
        "free_orders_per_address_per_day": {"validators": [NumberRange(0, 100)]},
        "ad_count": {"validators": [NumberRange(0, 10)]},
        "ad_duration_sec": {"validators": [NumberRange(1, 60)]},
        "sms_ip_limit_10min": {
            "validators": [NumberRange(1, 1000)],
            "description": "Защита от перебора номеров: сколько кодов можно отправить на запросы с одного IP-адреса. "
                           "Если бюджет SMS тратится подозрительно быстро — уменьшите. Действует сразу.",
        },
        "sms_ip_limit_day": {"validators": [NumberRange(1, 1000)]},
        "promo_enabled": {
            "description": "Включено — пакет и вещь стоят по ценам акции ниже, а обычные цены из «Услуг» на сайте "
                           "зачёркнуты. Выключено — действуют обычные цены. Допы акция не меняет.",
        },
        "promo_bag_price": {"validators": [NumberRange(0, 100000)]},
        "promo_piece_price": {"validators": [NumberRange(0, 100000)]},
        "promo_label": {"description": "Показывается рядом с ценой, например «акция 7 дней»."},
        "sms_ip_limit_week": {"validators": [NumberRange(1, 1000)]},
        "sms_enabled": {
            "description": "Выключено — SMS не отправляются, код показывается прямо на странице входа "
                           "(войти можно под любым номером).",
        },
        "debug_phones_enabled": {
            "description": "Включено — номера из поля ниже получают код прямо на странице входа, без SMS, "
                           "даже когда вход по SMS включён. Включайте только на время проверки сайта.",
        },
        "debug_phones": {
            "validators": [_validate_phone_list],
            "description": "Через запятую, например +7 999 999-99-99, +7 888 888-88-88. "
                           "Не вписывайте номера настоящих клиентов: под таким номером войдёт любой, кто его знает.",
        },
        # Контакты видят клиенты на сайте; пустое поле — контакт не показывается.
        "support_phone": {
            "validators": [Optional(), Regexp(r"^\+?[\d\s()-]{10,20}$", message="Телефон: цифры, пробелы, +, -, скобки")],
            "description": "Как показывать на сайте, например +7 912 384-19-67",
        },
        "support_telegram": {
            "description": "Имя пользователя: VITALII_PRIHODKO, @VITALII_PRIHODKO или ссылка t.me/…",
        },
        "support_email": {
            "validators": [Optional(), Regexp(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", message="Неверный email")],
        },
        "notify_emails": {
            "validators": [_validate_email_list],
            "description": "Куда приходят письма о новых заказах и сбоях оплаты. Несколько адресов — через запятую, "
                           "например oper1@mail.ru, oper2@yandex.ru. Пусто — письма не отправляются.",
        },
    }

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        # Отладочные номера храним в одном виде: «+7 999 999-99-99, +7 888 888-88-88».
        if "debug_phones" in data:
            data["debug_phones"] = ", ".join(
                f"+{d[0]} {d[1:4]} {d[4:7]}-{d[7:9]}-{d[9:]}" for d in parse_phone_list(data["debug_phones"] or "")
            )
        # Часы приёма храним в одном виде: «07:30».
        for field in ("order_accept_from", "order_accept_to"):
            if data.get(field):
                minutes = time_to_minutes(data[field])
                data[field] = f"{minutes // 60:02d}:{minutes % 60:02d}"
        # Адреса для уведомлений храним в одном виде: «a@mail.ru, b@yandex.ru».
        if "notify_emails" in data:
            data["notify_emails"] = ", ".join(parse_email_list(data["notify_emails"] or ""))
        # Пустые поля формы приходят как None, а колонки NOT NULL — храним пустую строку.
        for field in ("support_phone", "support_telegram", "support_email", "promo_label"):
            if field in data:
                data[field] = (data[field] or "").strip()
        # Telegram храним как голое имя пользователя: сайт сам строит ссылку https://t.me/<имя>.
        if data.get("support_telegram"):
            data["support_telegram"] = re.sub(
                r"^(https?://)?(t\.me/|telegram\.me/)?@?", "", data["support_telegram"]
            ).strip("/")


class SiteTextAdmin(BaseAdmin, model=SiteText):
    """Тексты окон сайта: оферта, «Подробнее о сервисе», политика ПДн. Правка видна на сайте сразу."""

    name = "Текст сайта"
    name_plural = "Тексты сайта"
    icon = "fa-solid fa-file-lines"

    column_list = ["name", SiteText.title, SiteText.updated_at]
    column_labels = {"name": "Окно на сайте", "title": "Заголовок", "body": "Текст", "updated_at": "Изменён", "slug": "Код"}
    column_formatters = {
        "name": lambda m, a: SITE_TEXT_NAMES.get(m.slug, m.slug),
        **_msk_formatters("updated_at"),
    }
    column_details_list = ["name", SiteText.title, SiteText.body, SiteText.updated_at]
    column_formatters_detail = column_formatters

    can_create = False
    can_delete = False
    form_columns = [SiteText.title, SiteText.body]
    form_overrides = {"title": StringField, "body": TextAreaField}
    form_args = {
        "title": {"description": "Заголовок окна. Можно оставить пустым."},
        "body": {
            "render_kw": {"rows": 30, "style": "font-family: monospace; font-size: 13px"},
            "description": Markup(
                "Разметка: строка с <code>## </code> в начале — заголовок раздела, с <code>- </code> — пункт списка, "
                "<code>**слово**</code> — жирный, остальные строки — абзацы. Адреса сайтов и email становятся ссылками."
            ),
        },
    }

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        data["title"] = (data.get("title") or "").strip()
        # Переводы строк Windows (\r\n) из браузера — в обычные, чтобы разметка распознавалась одинаково.
        data["body"] = (data.get("body") or "").replace("\r\n", "\n").strip()


class SmsSendAdmin(BaseAdmin, model=SmsSend):
    """Отправленные SMS-коды за 30 дней: видно, если с одного IP перебирают номера."""

    name = "SMS-код"
    name_plural = "Отправленные SMS"
    icon = "fa-solid fa-comment-sms"

    column_list = [SmsSend.sent_at, SmsSend.ip, SmsSend.phone]
    column_labels = {"id": "ID", "sent_at": "Отправлено", "ip": "IP-адрес", "phone": "Номер"}
    column_formatters = _msk_formatters("sent_at")
    column_formatters_detail = column_formatters
    column_searchable_list = [SmsSend.ip, SmsSend.phone]
    column_sortable_list = [SmsSend.sent_at, SmsSend.ip]
    column_default_sort = [(SmsSend.sent_at, True)]
    column_filters = [date_filter(SmsSend.sent_at, "Отправлено")]

    def search_placeholder(self) -> str:
        return "IP-адрес или номер"

    can_create = False
    can_edit = False
    can_delete = False


class OrderStatusHistoryAdmin(BaseAdmin, model=OrderStatusHistory):
    name = "История статуса"
    name_plural = "История статусов"
    icon = "fa-solid fa-clock-rotate-left"

    column_list = [
        OrderStatusHistory.id,
        OrderStatusHistory.order_id,
        "status",
        OrderStatusHistory.changed_at,
        OrderStatusHistory.changed_by,
    ]
    column_default_sort = [(OrderStatusHistory.changed_at, True)]
    column_labels = {
        "id": "ID",
        "order_id": "Заказ №",
        "status": "Статус",
        "status_id": "Статус ID",
        "changed_at": "Изменён",
        "changed_by": "Кем",
        "order": "Заказ",
    }
    column_formatters = {
        "order_id": lambda m, a: f"ST-{m.order_id}",
        "status": lambda m, a: str(m.status) if m.status else "—",
        "changed_by": lambda m, a: _CHANGED_BY_LABELS.get(m.changed_by, m.changed_by),
        **_msk_formatters("changed_at"),
    }
    column_formatters_detail = column_formatters

    can_create = False
    can_edit = False
    can_delete = False


def _ad_preview(image_path: str | None, height: int) -> Markup:
    if not image_path:
        return Markup("—")
    src = escape(image_path)
    return Markup(f'<a href="{src}" target="_blank"><img src="{src}" style="height:{height}px"></a>')


class AdAdmin(BaseAdmin, model=Ad):
    """Модерация рекламы: загрузка, включение/выключение, удаление картинок."""
    name = "Картинка"
    name_plural = "Реклама"
    icon = "fa-solid fa-image"

    column_list = [Ad.id, "preview", Ad.title, Ad.is_active, Ad.created_at]
    column_details_list = [Ad.id, "preview", Ad.title, Ad.image_path, Ad.is_active, Ad.created_at]
    column_default_sort = [(Ad.id, True)]
    column_labels = {
        "id": "ID",
        "preview": "Картинка",
        "title": "Название",
        "image_path": "Файл",
        "is_active": "Показывать",
        "created_at": "Добавлена",
        "image": "Файл картинки",
    }
    column_formatters = {
        "preview": lambda m, a: _ad_preview(m.image_path, 60),
        **_msk_formatters("created_at"),
    }
    column_formatters_detail = {
        "preview": lambda m, a: _ad_preview(m.image_path, 300),
        **_msk_formatters("created_at"),
    }

    # Файл задаётся только при создании; заменить картинку = загрузить новую, старую выключить.
    form_create_rules = ["title", "image", "is_active"]
    form_edit_rules = ["title", "is_active"]
    form_columns = [Ad.title, Ad.is_active]

    async def scaffold_form(self, rules=None):
        base = await super().scaffold_form(None)

        class AdForm(base):
            image = FileField(
                "Файл картинки",
                description=f"{', '.join(sorted(ALLOWED_EXTENSIONS))}, до 5 МБ",
            )

        if rules:
            # убирает из формы поля, которых нет в rules (на редактировании — image)
            self._validate_form_class(rules, AdForm)
        return AdForm

    async def insert_model(self, request: Request, data: dict) -> Any:
        upload = data.pop("image", None)
        content = await upload.read() if upload else b""
        try:
            data["image_path"] = save_ad_file(upload.filename if upload else "", content)
        except AdUploadError as e:
            raise ValueError(str(e)) from e
        try:
            return await super().insert_model(request, data)
        except Exception:
            delete_ad_file(data["image_path"])
            raise

    async def after_model_delete(self, model: Any, request: Request) -> None:
        delete_ad_file(model.image_path)


class AdViewStatsAdmin(BaseAdmin, model=AdViewStats):
    name = "Реклама"
    name_plural = "Статистика рекламы"
    icon = "fa-solid fa-chart-bar"

    column_list = [AdViewStats.title, AdViewStats.image_path, AdViewStats.total_views, AdViewStats.unique_viewers]
    column_sortable_list = [AdViewStats.total_views, AdViewStats.unique_viewers]
    column_default_sort = [(AdViewStats.total_views, True)]

    column_labels = {
        "title": "Название",
        "image_path": "Файл",
        "total_views": "Просмотров всего",
        "unique_viewers": "Уникальных зрителей",
    }
    column_formatters = {
        "image_path": lambda m, a: m.image_path.rsplit("/", 1)[-1],
        "title": lambda m, a: m.title or "— (удалена)",
    }

    can_create = False
    can_edit = False
    can_delete = False


class LandingVisitStatsAdmin(BaseAdmin, model=LandingVisitStats):
    name = "Посещения"
    name_plural = "Посещения сайта"
    icon = "fa-solid fa-chart-line"

    column_list = [LandingVisitStats.day, LandingVisitStats.visits, LandingVisitStats.unique_visitors]
    column_sortable_list = [LandingVisitStats.day, LandingVisitStats.visits, LandingVisitStats.unique_visitors]
    column_default_sort = [(LandingVisitStats.day, True)]

    column_labels = {
        "day": "День (МСК)",
        "visits": "Заходов",
        "unique_visitors": "Уникальных посетителей",
    }
    column_formatters = {
        "day": lambda m, a: m.day.strftime("%d.%m.%Y"),
    }

    can_create = False
    can_edit = False
    can_delete = False


def create_admin(app) -> Admin:
    settings = AppSettings()
    auth_backend = AdminAuth(
        secret_key=settings.SECRET_KEY,
        username=settings.ADMIN_USERNAME,
        password=settings.ADMIN_PASSWORD,
    )
    admin = Admin(
        app,
        engine,
        title="Стирки ON — Админка",
        authentication_backend=auth_backend,
        templates_dir=str(_TEMPLATES_DIR),
    )
    # Свой sqladmin/base.html (перевод интерфейса) наследуется от оригинала — он доступен по префиксу «original/».
    admin.templates.env.loader = ChoiceLoader([
        admin.templates.env.loader,
        PrefixLoader({"original": PackageLoader("sqladmin", "templates")}),
    ])
    admin.add_base_view(HelpView)
    admin.add_view(OrderAdmin)
    admin.add_view(OrderStatusAdmin)
    admin.add_view(ClientAdmin)
    admin.add_view(ServiceAdmin)
    admin.add_view(SystemSettingsAdmin)
    admin.add_view(OrderStatusHistoryAdmin)
    admin.add_view(AdAdmin)
    admin.add_view(AdViewStatsAdmin)
    admin.add_view(LandingVisitStatsAdmin)
    admin.add_view(SiteTextAdmin)
    admin.add_view(SmsSendAdmin)
    return admin
