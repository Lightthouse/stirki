create table clients (
    id bigserial primary key,
    phone text unique not null,
    name text,
    email text,

    auth_token text unique,
    auth_token_expires_at timestamptz,
    is_verified boolean default false,
    verification_code text,
    verification_expires_at timestamptz,
    verification_attempts int not null default 0,
    verification_sent_at timestamptz,

    street text not null default '',
    house text not null default '',
    entrance int not null default 1,
    floor int not null default 1,
    apartment int not null default 0,
    comment text,

    -- согласия, данные при входе (галочки под номером телефона): время последнего входа с галочкой.
    -- Оферта и политика обязательны; рассылка — по желанию, null = согласия нет (или отозвано)
    offer_accepted_at timestamptz,
    sms_marketing_consent_at timestamptz,

    registered_at timestamptz default now(),
    total_orders int default 0
);

create table order_statuses (
    id serial primary key,
    name text unique not null,
    slug text unique not null
);

create table services (
    id serial primary key,
    name text not null,
    slug text unique not null,
    price_rub int not null,
    is_active boolean default true
);

create table orders (
    id bigserial primary key,
    client_id bigint not null references clients(id),
    status_id int not null references order_statuses(id),

    street text not null,
    house text not null,
    entrance int not null default 1,
    floor int not null default 1,
    apartment int not null,
    comment text,

    washing_type text not null default 'bag' check (washing_type in ('bag', 'piece', 'mixed')),
    bags_number int not null default 0,
    pieces_number int not null default 0,
    ironing boolean default false,
    conditioner boolean default false,
    vacuum_pack boolean default false,
    stain_remover boolean default false,
    wash_bag boolean default false,
    bleach boolean default false,
    color_catcher_sheets boolean default false,

    is_free boolean not null default false,
    total_price_rub int not null check (total_price_rub >= 0),
    payment_status text default 'pending' check (payment_status in ('pending', 'succeeded', 'canceled')),
    payment_token text unique,
    payment_link_id text,
    operation_id text,
    payment_link text,

    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table order_status_history (
    id bigserial primary key,
    order_id bigint not null references orders(id) on delete cascade,
    status_id int not null references order_statuses(id),
    changed_at timestamptz default now(),
    changed_by text
);

-- заходы неавторизованных посетителей на главную: QR на листовках ведёт на сайт без параметров,
-- поэтому источник не различаем — считаем все заходы
create table landing_visits (
    id bigserial primary key,
    visitor_id uuid not null,     -- случайный id браузера (localStorage) — для подсчёта уникальных посетителей
    visited_at timestamptz default now()
);

create index idx_landing_visits_visited_at on landing_visits (visited_at);

create view landing_visit_stats as
select
    (visited_at at time zone 'Europe/Moscow')::date as day,
    count(*)                                        as visits,
    count(distinct visitor_id)                      as unique_visitors
from landing_visits
group by 1;

-- рекламные картинки (админка «Реклама»): файл лежит в advertising/, показываются только is_active
create table ads (
    id serial primary key,
    title text not null,
    image_path text unique not null,
    is_active boolean not null default true,
    created_at timestamptz default now()
);

insert into ads (title, image_path) values
('Сплетницы', '/advertising/сплетницы.jpg'),
('Счастливые часы', '/advertising/счастливыечасы.jpg');

-- отслеживаем для каждой рекламной картинки то, сколько раз её просмотрели
create table ad_views (
    id bigserial primary key,
    image_path text not null,
    client_id bigint references clients(id),
    viewed_at timestamptz default now()
);
create index idx_ad_views_image_path on ad_views (image_path);

-- статистика по пути картинки; title — из ads (null, если картинку удалили)
create view ad_view_stats as
select
    v.image_path,
    a.title,
    count(*)                    as total_views,
    count(distinct v.client_id) as unique_viewers
from ad_views v
left join ads a on a.image_path = v.image_path
group by v.image_path, a.title
order by total_views desc;

-- таблица для глобальных настроек сервиса (одна строка)
create table system_settings (
    id int primary key default 1,
    free_tariff_is_available bool not null default true,
    free_bag_slots int not null default 1,
    free_piece_slots int not null default 0,
    paid_bag_slots int not null default 5,
    paid_piece_slots int not null default 1,
    -- приём заказов, часы по МСК: [order_accept_from_hour, order_accept_to_hour)
    order_accept_from_hour int not null default 9,
    order_accept_to_hour int not null default 22,
    -- сколько бесплатных заказов в сутки (МСК) допускается на один адрес (улица+дом+квартира)
    free_orders_per_address_per_day int not null default 1,
    -- реклама на бесплатном тарифе: сколько картинок показывать и сколько секунд каждую
    ad_count int not null default 1,
    ad_duration_sec int not null default 1,
    constraint system_settings_singleton check (id = 1)
);

insert into system_settings (id, free_tariff_is_available, free_bag_slots, free_piece_slots, paid_bag_slots, paid_piece_slots)
values (1, true, 1, 0, 5, 1);

insert into order_statuses (name, slug) values
('В пути','courier_pickup'), ('Забрали','picked_up'),
('Чистим','washing'),  ('Идём отдавать','courier_delivery'), ('Доставлено','delivered'),
('Отменено','canceled'), ('Ожидает оплаты','waiting_payment');

insert into services (name, slug, price_rub, is_active) values
('Стирка', 'base', 990, true),
('Стирка одной вещи', 'piece', 190, true),
('Глажка', 'ironing', 190, true),
('Кондиционер для белья', 'conditioner', 100, true),
('Вакуумный пакет', 'vacuum_pack', 150, true),
('Пятновыводитель', 'stain_remover', 80, false),
('Отбеливатель', 'bleach', 80, false),
('Салфетки против окрашивания', 'color_catcher_sheets', 100, false),
('Мешок для стирки', 'wash_bag', 30, false),
-- цена глажки за пакет; ironing — за вещь (src/services/pricing.py, BAG_PRICE_SUFFIX)
('Глажка пакета', 'ironing_bag', 990, true);

