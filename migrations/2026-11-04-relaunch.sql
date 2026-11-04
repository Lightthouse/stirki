-- Миграция для БД, созданной до 2026-11-04 (на новой БД всё уже есть в pg_init/01-schema.sql).
-- Идемпотентна — можно запускать повторно:
--   docker compose exec -T postgres psql -U stirki -d stirki < migrations/2026-11-04-relaunch.sql

insert into order_statuses (name, slug)
select 'Ожидает оплаты', 'waiting_payment'
where not exists (select 1 from order_statuses where slug = 'waiting_payment');

alter table system_settings add column if not exists order_accept_from_hour int not null default 9;
alter table system_settings add column if not exists order_accept_to_hour int not null default 22;
alter table system_settings add column if not exists free_orders_per_address_per_day int not null default 1;
alter table system_settings add column if not exists ad_count int not null default 1;
alter table system_settings add column if not exists ad_duration_sec int not null default 1;
