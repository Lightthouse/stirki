import re
from datetime import datetime
from pathlib import Path
from typing import Any

from markupsafe import Markup, escape
from sqladmin import Admin, BaseView, ModelView, expose
from sqladmin.fields import FileField
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy import Select
from starlette.requests import Request
from wtforms import SelectField, StringField
from wtforms.validators import NumberRange, Optional, Regexp

from src.addresses import STREETS_SLUG
from src.enums import HANDOVER_LABELS
from src.database import async_session, engine
from src.models.analytics import Ad, AdViewStats, LandingVisitStats
from src.models.client import Client
from src.models.order import Order, OrderStatus, OrderStatusHistory
from src.models.service import Service
from src.models.system_settings import SystemSettings
from src.services.ads import ALLOWED_EXTENSIONS, AdUploadError, delete_ad_file, save_ad_file
from src.services.schedule import MSK
from src.settings import AppSettings

_SLUG_TO_STREET = {slug: name for name, slug in STREETS_SLUG.items()}

_TEMPLATES_DIR = Path(__file__).parent / "admin_templates"


def _msk(value: datetime | None) -> str:
    """Время из БД (UTC) → московское, в читаемом виде для сотрудников."""
    return value.astimezone(MSK).strftime("%d.%m.%Y %H:%M") if value else "—"


def _msk_formatters(*fields: str) -> dict:
    return {f: (lambda m, a, f=f: _msk(getattr(m, f))) for f in fields}


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


class OrderAdmin(ModelView, model=Order):
    name = "Заказ"
    name_plural = "Заказы"
    icon = "fa-solid fa-basket-shopping"

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
    column_sortable_list = [Order.id, Order.created_at, Order.total_price_rub]
    column_default_sort = [(Order.created_at, True)]

    column_labels = {
        "id": "№",
        "client_id": "Клиент ID",
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
        "wash_bag": "Мешок",
        "bleach": "Отбеливатель",
        "color_catcher_sheets": "Цветоуловитель",
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
    # Передачу можно поменять, если клиент попросил по телефону; список вместо textarea для Text.
    form_overrides = {"handover": SelectField}
    form_args = {"handover": {"choices": [(k.value, v) for k, v in HANDOVER_LABELS.items()]}}
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


class OrderStatusAdmin(ModelView, model=OrderStatus):
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


class ClientAdmin(ModelView, model=Client):
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
        **_msk_formatters("registered_at", "offer_accepted_at", "sms_marketing_consent_at"),
    }
    column_formatters_detail = column_formatters

    # email — чтобы найти клиента по кассовому чеку
    column_searchable_list = [Client.phone, Client.name, Client.email]
    column_sortable_list = [Client.id, Client.registered_at, Client.total_orders]
    column_default_sort = [(Client.registered_at, True)]

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
    }

    can_create = False
    can_delete = False
    form_columns = [Client.name, Client.email, Client.comment]


class ServiceAdmin(ModelView, model=Service):
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


class SystemSettingsAdmin(ModelView, model=SystemSettings):
    name = "Настройки"
    name_plural = "Системные настройки"
    icon = "fa-solid fa-sliders"

    column_list = [
        SystemSettings.free_tariff_is_available,
        SystemSettings.sms_enabled,
        SystemSettings.free_bag_slots,
        SystemSettings.free_piece_slots,
        SystemSettings.paid_bag_slots,
        SystemSettings.paid_piece_slots,
        SystemSettings.order_accept_from_hour,
        SystemSettings.order_accept_to_hour,
        SystemSettings.next_day_delivery_from_hour,
        SystemSettings.free_orders_per_address_per_day,
        SystemSettings.ad_count,
        SystemSettings.ad_duration_sec,
        SystemSettings.support_phone,
        SystemSettings.support_telegram,
        SystemSettings.support_email,
    ]
    column_labels = {
        "id": "ID",
        "free_tariff_is_available": "Бесплатный тариф доступен",
        "sms_enabled": "Вход по SMS (отправлять коды)",
        "free_bag_slots": "Бесплатный: пакеты (макс.)",
        "free_piece_slots": "Бесплатный: вещи (макс.)",
        "paid_bag_slots": "Платный: пакеты (макс.)",
        "paid_piece_slots": "Платный: вещи (макс.)",
        "order_accept_from_hour": "Приём заказов с (час, МСК)",
        "order_accept_to_hour": "Приём заказов до (час, МСК)",
        "next_day_delivery_from_hour": "Доставка на след. день для заказов с (час, МСК)",
        "free_orders_per_address_per_day": "Бесплатных заказов на адрес в сутки",
        "ad_count": "Реклама: картинок за просмотр",
        "ad_duration_sec": "Реклама: секунд на картинку",
        "support_phone": "Поддержка: телефон",
        "support_telegram": "Поддержка: Telegram",
        "support_email": "Поддержка: email",
    }

    can_create = False
    can_delete = False
    form_columns = [
        SystemSettings.free_tariff_is_available,
        SystemSettings.sms_enabled,
        SystemSettings.free_bag_slots,
        SystemSettings.free_piece_slots,
        SystemSettings.paid_bag_slots,
        SystemSettings.paid_piece_slots,
        SystemSettings.order_accept_from_hour,
        SystemSettings.order_accept_to_hour,
        SystemSettings.next_day_delivery_from_hour,
        SystemSettings.free_orders_per_address_per_day,
        SystemSettings.ad_count,
        SystemSettings.ad_duration_sec,
        SystemSettings.support_phone,
        SystemSettings.support_telegram,
        SystemSettings.support_email,
    ]
    # Контакты — однострочные поля, а не textarea, которую sqladmin делает для Text.
    form_overrides = {f: StringField for f in ("support_phone", "support_telegram", "support_email")}
    form_args = {
        "order_accept_from_hour": {"validators": [NumberRange(0, 23)]},
        "order_accept_to_hour": {"validators": [NumberRange(1, 24)]},
        # 24 — доставка на следующий день не применяется никогда.
        "next_day_delivery_from_hour": {"validators": [NumberRange(0, 24)]},
        "free_orders_per_address_per_day": {"validators": [NumberRange(0, 100)]},
        "ad_count": {"validators": [NumberRange(0, 10)]},
        "ad_duration_sec": {"validators": [NumberRange(1, 60)]},
        "sms_enabled": {
            "description": "Выключено — SMS не отправляются, код показывается прямо на странице входа "
                           "(войти можно под любым номером). Отладочные номера +7 999 999-99-99 и "
                           "+7 888 888-88-88 получают код на странице всегда.",
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
    }

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        # Пустые поля формы приходят как None, а колонки NOT NULL — храним пустую строку.
        for field in ("support_phone", "support_telegram", "support_email"):
            if field in data:
                data[field] = (data[field] or "").strip()
        # Telegram храним как голое имя пользователя: сайт сам строит ссылку https://t.me/<имя>.
        if data.get("support_telegram"):
            data["support_telegram"] = re.sub(
                r"^(https?://)?(t\.me/|telegram\.me/)?@?", "", data["support_telegram"]
            ).strip("/")


class OrderStatusHistoryAdmin(ModelView, model=OrderStatusHistory):
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
    }
    column_formatters = {
        "order_id": lambda m, a: f"ST-{m.order_id}",
        "status": lambda m, a: str(m.status) if m.status else "—",
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


class AdAdmin(ModelView, model=Ad):
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


class AdViewStatsAdmin(ModelView, model=AdViewStats):
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


class LandingVisitStatsAdmin(ModelView, model=LandingVisitStats):
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
    return admin
