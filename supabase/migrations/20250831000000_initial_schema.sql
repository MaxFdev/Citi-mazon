-- initial schema

create table departments (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    description text not null default '',
    search_terms text[] not null default '{}'
);

create table department_attributes (
    id uuid primary key default gen_random_uuid(),
    department_id uuid not null references departments (id) on delete cascade,
    name text not null,
    attribute_type text not null check (attribute_type in ('select', 'text', 'number')),
    unique (department_id, name)
);

create table attribute_options (
    id uuid primary key default gen_random_uuid(),
    attribute_id uuid not null references department_attributes (id) on delete cascade,
    value text not null,
    unique (attribute_id, value)
);

create table items (
    id uuid primary key default gen_random_uuid(),
    department_id uuid not null references departments (id) on delete restrict,
    vendor_name text not null,
    title text not null,
    description text not null default '',
    price numeric(10, 2) not null check (price >= 0),
    created_at timestamptz not null default now()
);

create table item_attributes (
    id uuid primary key default gen_random_uuid(),
    item_id uuid not null references items (id) on delete cascade,
    attribute_id uuid not null references department_attributes (id) on delete cascade,
    option_id uuid references attribute_options (id) on delete restrict,
    value_text text,
    value_number numeric,
    unique (item_id, attribute_id)
);
