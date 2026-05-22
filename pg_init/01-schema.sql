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

    street text not null default '',
    house text not null default '',
    entrance int not null default 1,
    floor int not null default 1,
    apartment int not null default 0,
    comment text,

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

create table landing_visits (
    id bigserial primary key,
    ref_code text not null,
    visited_at timestamptz default now()
);

create index idx_landing_visits_ref_code on landing_visits (ref_code);

-- отслеживаем для каждой рекламной картинки то, сколько раз её просмотрели
create table ad_views (
    id bigserial primary key,
    image_path text not null,
    client_id bigint references clients(id),
    viewed_at timestamptz default now()
);
create index idx_ad_views_image_path on ad_views (image_path);

create view ad_view_stats as
select
    image_path,
    count(*)                    as total_views,
    count(distinct client_id)   as unique_viewers
from ad_views
group by image_path
order by total_views desc;

-- аналитика по переходам по ссылке в приложение
create table qr_codes (
    code int primary key,         -- числовой код из ?ref=N; 0 = невалидный/неизвестный
    address_slug text not null,   -- slug адреса или 'invalid'
    address_name text not null,   -- название на кириллице или 'Неизвестный код'
    visit_count int not null default 0
);

-- таблица для глобальных настроек сервиса (одна строка)
create table system_settings (
    id int primary key default 1,
    free_tariff_is_available bool not null default true,
    free_bag_slots int not null default 1,
    free_piece_slots int not null default 0,
    paid_bag_slots int not null default 5,
    paid_piece_slots int not null default 1,
    constraint system_settings_singleton check (id = 1)
);

insert into system_settings (id, free_tariff_is_available, free_bag_slots, free_piece_slots, paid_bag_slots, paid_piece_slots)
values (1, true, 1, 0, 5, 1);

insert into order_statuses (name, slug) values
('Заказ принят','new'), ('В пути','courier_pickup'), ('Забрали','picked_up'),
('Чистим','washing'),  ('Идём отдавать','courier_delivery'), ('Доставлено','delivered'),
('Отменено','canceled');

insert into services (name, slug, price_rub, is_active) values
('Стирка', 'base', 1490, true),
('Стирка одной вещи', 'piece', 390, true),
('Глажка', 'ironing', 190, true),
('Кондиционер для белья', 'conditioner', 100, true),
('Вакуумный пакет', 'vacuum_pack', 150, true),
('Пятновыводитель', 'stain_remover', 80, false),
('Отбеливатель', 'bleach', 80, false),
('Салфетки против окрашивания', 'color_catcher_sheets', 100, true),
('Мешок для стирки', 'wash_bag', 30, false);

insert into qr_codes (code, address_slug, address_name) values
(142, 'rozhdestvenskaya-11',   'Рождественская, 11'),
(287, 'rozhdestvenskaya-9',    'Рождественская, 9'),
(391, 'rozhdestvenskaya-7',    'Рождественская, 7'),
(516, 'rozhdestvenskaya-5',    'Рождественская, 5'),
(634, 'rozhdestvenskaya-3',    'Рождественская, 3'),
(78,  'rozhdestvenskaya-2',    'Рождественская, 2'),
(203, 'novomytishchinskay-4a', 'Новомытищинский проспект, 4а'),
(457, 'komarova-2k1',          'Комарова, 2к1'),
(819, 'komarova-2k2',          'Комарова, 2к2'),
(563, 'komarova-2k3',          'Комарова, 2к3'),
(721, 'vorovskogo-10',         'Воровского, 10'),
(345, 'sharapovskaya-vl2-st3', 'Шараповский проезд, вл2 ст3'),
(0,   'invalid',               'Неизвестный код');
