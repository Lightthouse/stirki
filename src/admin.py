from typing import Any

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from src.addresses import STREETS_SLUG
from src.database import async_session, engine
from src.models.analytics import AdViewStats, LandingVisit, QrCode
from src.models.client import Client
from src.models.order import Order, OrderStatus, OrderStatusHistory
from src.models.service import Service
from src.models.system_settings import SystemSettings
from src.settings import AppSettings

_SLUG_TO_STREET = {slug: name for name, slug in STREETS_SLUG.items()}


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
        Order.client_id,
        Order.street,
        Order.house,
        Order.apartment,
        "status",
        Order.washing_type,
        Order.bags_number,
        Order.total_price_rub,
        Order.payment_status,
        Order.created_at,
    ]
    column_details_list = "__all__"
    column_searchable_list = [Order.street, Order.house]
    column_sortable_list = [Order.id, Order.created_at, Order.total_price_rub]
    column_default_sort = [(Order.created_at, True)]

    column_labels = {
        "id": "№",
        "client_id": "Клиент ID",
        "street": "Улица",
        "house": "Дом",
        "apartment": "Кв.",
        "entrance": "Подъезд",
        "floor": "Этаж",
        "comment": "Комментарий",
        "status": "Статус",
        "status_id": "Статус ID",
        "washing_type": "Тип стирки",
        "bags_number": "Мешков",
        "ironing": "Глажка",
        "conditioner": "Кондиционер",
        "vacuum_pack": "Вакуум",
        "stain_remover": "Пятновыводитель",
        "wash_bag": "Мешок",
        "bleach": "Отбеливатель",
        "color_catcher_sheets": "Цветоуловитель",
        "total_price_rub": "Цена (₽)",
        "payment_status": "Оплата",
        "yookassa_payment_id": "YooKassa ID",
        "yookassa_confirmation_url": "Ссылка оплаты",
        "created_at": "Создан",
        "updated_at": "Обновлён",
    }

    column_formatters = {
        "street": lambda m, a: _SLUG_TO_STREET.get(m.street, m.street),
        "status": lambda m, a: str(m.status) if m.status else "—",
    }

    form_include_pk = False
    form_columns = [
        'status',
        Order.comment,
        Order.payment_status,
    ]
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

    column_list = [OrderStatus.id, OrderStatus.name]
    column_labels = {
        "id": "ID",
        "name": "Статус",
    }
    column_formatters = {
        "name": lambda m, a: str(m),
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
        Client.total_orders,
        Client.registered_at,
    ]
    column_details_exclude_list = [
        Client.auth_token,
        Client.verification_code,
    ]
    column_formatters = {
        "street": lambda m, a: _SLUG_TO_STREET.get(m.street, m.street),
    }

    column_searchable_list = [Client.phone, Client.name]
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

    column_list = [SystemSettings.free_tariff_is_available]
    column_labels = {
        "id": "ID",
        "free_tariff_is_available": "Бесплатный тариф доступен",
    }

    can_create = False
    can_delete = False
    form_columns = [SystemSettings.free_tariff_is_available]


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
        "status": lambda m, a: str(m.status) if m.status else "—",
    }

    can_create = False
    can_edit = False
    can_delete = False


class AdViewStatsAdmin(ModelView, model=AdViewStats):
    name = "Реклама"
    name_plural = "Статистика рекламы"
    icon = "fa-solid fa-chart-bar"

    column_list = [AdViewStats.image_path, AdViewStats.total_views, AdViewStats.unique_viewers]
    column_sortable_list = [AdViewStats.total_views, AdViewStats.unique_viewers]
    column_default_sort = [(AdViewStats.total_views, True)]

    column_labels = {
        "image_path": "Картинка",
        "total_views": "Просмотров всего",
        "unique_viewers": "Уникальных зрителей",
    }
    column_formatters = {
        "image_path": lambda m, a: m.image_path.rsplit("/", 1)[-1],
    }

    can_create = False
    can_edit = False
    can_delete = False


class QrCodeAdmin(ModelView, model=QrCode):
    name = "QR-код"
    name_plural = "QR-коды (аналитика)"
    icon = "fa-solid fa-qrcode"

    column_list = [QrCode.address_name, QrCode.code, QrCode.visit_count]
    column_sortable_list = [QrCode.visit_count, QrCode.address_name, QrCode.code]
    column_default_sort = [(QrCode.visit_count, True)]

    column_labels = {
        "address_name": "Адрес",
        "address_slug": "Slug",
        "code": "Код",
        "visit_count": "Переходов",
    }

    can_create = False
    can_edit = False
    can_delete = False


class LandingVisitAdmin(ModelView, model=LandingVisit):
    name = "Визит"
    name_plural = "Визиты по QR"
    icon = "fa-solid fa-chart-line"

    column_list = [LandingVisit.id, LandingVisit.ref_code, LandingVisit.visited_at]
    column_default_sort = [(LandingVisit.visited_at, True)]

    column_labels = {
        "id": "ID",
        "ref_code": "Адрес",
        "visited_at": "Время",
    }
    column_formatters = {
        "ref_code": lambda m, a: (
            "Неизвестный код" if m.ref_code == "invalid"
            else _SLUG_TO_STREET.get(m.ref_code.rsplit("-", 1)[0], m.ref_code) + ", " + m.ref_code.rsplit("-", 1)[-1]
            if "-" in m.ref_code else m.ref_code
        ),
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
    )
    admin.add_view(OrderAdmin)
    admin.add_view(OrderStatusAdmin)
    admin.add_view(ClientAdmin)
    admin.add_view(ServiceAdmin)
    admin.add_view(SystemSettingsAdmin)
    admin.add_view(OrderStatusHistoryAdmin)
    admin.add_view(AdViewStatsAdmin)
    admin.add_view(QrCodeAdmin)
    admin.add_view(LandingVisitAdmin)
    return admin
