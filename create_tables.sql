create table users (
    id integer primary key,
    email varchar(255) not null unique,
    password varchar(255) not null
        check (length(password) > 8),
    role varchar(20) not null
        check (role in ('customer', 'admin')),
    status varchar(20) not null
        check (status in ('active', 'blocked', 'deleted')),
    registered_at date not null
);

create table profiles (
    user_id integer primary key
        references users(id),
    first_name varchar(100) not null,
    last_name varchar(100) not null,
    nickname varchar(100) not null unique,
    birthday_year integer not null,
    country varchar(100) not null
);

create table developers (
    id integer primary key,
    name varchar(200) not null unique,
    country varchar(100) not null,
    founded_year integer not null
);

create table games (
    id integer primary key,
    developer_id integer not null
        references developers(id),
    name varchar(200) not null,
    price numeric(10, 2) not null
        check (price >= 0),
    release_year integer not null,
    status varchar(20) not null
        check (status in ('available', 'unavailable')),
    unique (developer_id, name)
);

create table genres (
    id integer primary key,
    name varchar(100) not null unique
);

create table game_genres (
    game_id integer not null
        references games(id),
    genre_id integer not null
        references genres(id),
    primary key (game_id, genre_id)
);

create table platforms (
    id integer primary key,
    name varchar(100) not null unique
);

create table game_platforms (
    game_id integer not null
        references games(id),
    platform_id integer not null
        references platforms(id),
    primary key (game_id, platform_id)
);

create table carts (
    id integer primary key,
    user_id integer not null unique
        references users(id),
    created_at date not null,
    updated_at date not null,
    check (updated_at >= created_at)
);

create table cart_items (
    cart_id integer not null
        references carts(id),
    game_id integer not null
        references games(id),
    added_at date not null,
    primary key (cart_id, game_id)
);

create table orders (
    id integer primary key,
    user_id integer not null
        references users(id),
    created_at date not null,
    total_amount numeric(12, 2) not null
        check (total_amount >= 0),
    status varchar(20) not null
        check (status in ('paid', 'cancelled', 'refunded'))
);

create table order_items (
    id integer primary key,
    order_id integer not null
        references orders(id),
    game_id integer not null
        references games(id),
    purchase_price numeric(10, 2) not null
        check (purchase_price >= 0),
    unique (order_id, game_id)
);

create table payments (
    id integer primary key,
    order_id integer not null unique
        references orders(id),
    amount numeric(12, 2) not null
        check (amount >= 0),
    status varchar(20) not null
        check (status in ('successful', 'failed', 'refunded')),
    transaction_number varchar(100) not null unique
);

create table libraries (
    id integer primary key,
    user_id integer not null unique
        references users(id),
    games_count integer not null
        check (games_count >= 0)
);

create table library_games (
    library_id integer not null
        references libraries(id),
    game_id integer not null
        references games(id),
    order_item_id integer not null unique
        references order_items(id),
    purchased_at date not null,
    primary key (library_id, game_id)
);

