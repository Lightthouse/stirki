create table clients (
    id bigserial primary key,
    phone text unique not null,
    name text,

    auth_token text unique,
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
    name text unique not null
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

    bags_number int default 1,
    ironing boolean default false,
    conditioner boolean default false,
    vacuum_pack boolean default false,
    stain_remover boolean default false,
    wash_bag boolean default false,
    bleach boolean default false,
    color_catcher_sheets boolean default false,

    total_price_rub int not null check (total_price_rub >= 0),
    payment_status text default 'pending' check (payment_status in ('pending', 'waiting_for_capture', 'succeeded', 'canceled')),
    yookassa_payment_id text,
    yookassa_confirmation_url text,

    kaiten_card_id int,

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

create table promo_codes (
    id serial primary key,
    code text unique not null,
    discount_rub int default 0,
    discount_percent int check (discount_percent between 1 and 100),
    usage_limit int,
    used_count int default 0,
    valid_until timestamptz,
    created_at timestamptz default now()
);

create table promo_code_uses (
    promo_code_id int references promo_codes(id),
    client_id bigint references clients(id),
    order_id bigint references orders(id),
    used_at timestamptz default now(),
    primary key (promo_code_id, client_id)
);


insert into order_statuses (name) values
('waiting_for_capture'), ('new'), ('courier_pickup'), ('picked_up'), ('washing'), ('drying'),
('ironing'), ('packing'), ('courier_delivery'), ('delivered'), ('canceled');

insert into services (name, slug, price_rub) values
('Стирка', 'base', 890),
('Глажка', 'ironing', 990),
('Кондиционер для белья', 'conditioner', 50),
('Вакуумный пакет', 'vacuum_pack', 150),
('Пятновыводитель', 'stain_remover', 80),
('Отбеливатель', 'bleach', 80),
('Салфетки против окрашивания', 'color_catcher_sheets', 30),
('Мешок для стирки', 'wash_bag', 30);
