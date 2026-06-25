import random
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

import psycopg2
from faker import Faker
from psycopg2.extras import execute_values

# pip install psycopg2-binary faker

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "notsteam",
    "user": "postgres",
    "password": "13098283",  # <- впиши свій пароль тут
}

SEED = 42
PAGE_SIZE = 5000
TRUNCATE_BEFORE_INSERT = True

USERS_COUNT = 50_000
PROFILES_COUNT = 50_000
DEVELOPERS_COUNT = 500
GAMES_COUNT = 5_000
GENRES_COUNT = 20
GAME_GENRES_TARGET = 12_500
PLATFORMS_COUNT = 3
GAME_PLATFORMS_TARGET = 9_000
CARTS_COUNT = 50_000
CART_ITEMS_TARGET = 50_000
ORDERS_COUNT = 200_000
ORDER_ITEMS_TARGET = 500_000
PAYMENTS_COUNT = 200_000
LIBRARIES_COUNT = 50_000

COUNTRIES = [
    "USA", "UKR", "POL", "FRA", "DEU", "CAN", "ITA", "ESP", "JPN", "GBR",
    "CZE", "SVK", "ROU", "SWE", "NOR", "FIN", "DNK", "NLD", "AUS", "KOR",
]

# У вимогах написано 20 genres, але в наданому списку було 19 назв.
# "indie" додано як 20-й жанр, щоб виконати кількість 20.
GENRE_NAMES = [
    "action", "adventure", "rpg", "strategy", "simulation", "sports", "racing",
    "puzzle", "horror", "shooter", "fighting", "platformer", "survival",
    "sandbox", "stealth", "rhythm", "visual novel", "card game", "mmo", "indie",
]

PLATFORM_NAMES = ["windows", "macos", "linux"]

fake = Faker("en_US")
Faker.seed(SEED)
random.seed(SEED)


def random_date(start: date, end: date) -> date:
    if end < start:
        return start
    days = (end - start).days
    return start + timedelta(days=random.randint(0, days))


def random_price() -> Decimal:
    return (Decimal(random.randint(0, 10_000)) / Decimal("100")).quantize(Decimal("0.01"))


def insert_rows(cur, sql: str, rows, page_size: int = PAGE_SIZE) -> None:
    if rows:
        execute_values(cur, sql, rows, page_size=page_size)


def truncate_tables(cur) -> None:
    cur.execute(
        """
        truncate table
            library_games,
            libraries,
            payments,
            order_items,
            orders,
            cart_items,
            carts,
            game_platforms,
            game_genres,
            platforms,
            genres,
            games,
            developers,
            profiles,
            users;
        """
    )


def generate_users(cur):
    print("inserting users...")
    start = date(2020, 1, 1)
    today = date.today()

    rows = []
    registered_dates = [None] * (USERS_COUNT + 1)

    for user_id in range(1, USERS_COUNT + 1):
        role = "admin" if random.random() < 0.01 else "customer"

        status_rand = random.random()
        if status_rand < 0.90:
            status = "active"
        elif status_rand < 0.97:
            status = "blocked"
        else:
            status = "deleted"

        registered_at = random_date(start, today)
        registered_dates[user_id] = registered_at

        rows.append(
            (
                user_id,
                f"user{user_id}@notsteam.local",
                "password123",
                role,
                status,
                registered_at,
            )
        )

    insert_rows(
        cur,
        """
        insert into users (id, email, password, role, status, registered_at)
        values %s
        """,
        rows,
    )
    return registered_dates


def generate_profiles(cur):
    print("inserting profiles...")
    rows = []

    for user_id in range(1, PROFILES_COUNT + 1):
        nickname = f"{fake.user_name()[:80]}_{user_id}"
        rows.append(
            (
                user_id,
                fake.first_name(),
                fake.last_name(),
                nickname,
                random.randint(1960, 2008),
                random.choice(COUNTRIES),
            )
        )

    insert_rows(
        cur,
        """
        insert into profiles (user_id, first_name, last_name, nickname, birthday_year, country)
        values %s
        """,
        rows,
    )


def generate_developers(cur):
    print("inserting developers...")
    rows = []

    for developer_id in range(1, DEVELOPERS_COUNT + 1):
        name = f"{fake.unique.company()} Studio {developer_id}"
        rows.append(
            (
                developer_id,
                name[:200],
                random.choice(COUNTRIES),
                random.randint(1980, 2025),
            )
        )

    insert_rows(
        cur,
        """
        insert into developers (id, name, country, founded_year)
        values %s
        """,
        rows,
    )


def generate_games(cur):
    print("inserting games...")
    rows = []
    game_prices = {}
    game_release_years = {}
    available_games = []

    for game_id in range(1, GAMES_COUNT + 1):
        developer_id = random.randint(1, DEVELOPERS_COUNT)
        name = f"{fake.catch_phrase()} {game_id}"[:200]
        price = random_price()
        release_year = random.randint(1990, 2026)
        status = "available" if random.random() < 0.95 else "unavailable"

        game_prices[game_id] = price
        game_release_years[game_id] = release_year
        if status == "available":
            available_games.append(game_id)

        rows.append((game_id, developer_id, name, price, release_year, status))

    insert_rows(
        cur,
        """
        insert into games (id, developer_id, name, price, release_year, status)
        values %s
        """,
        rows,
    )

    return game_prices, game_release_years, available_games


def generate_genres(cur):
    print("inserting genres...")
    rows = [(genre_id, name) for genre_id, name in enumerate(GENRE_NAMES, start=1)]
    insert_rows(cur, "insert into genres (id, name) values %s", rows)


def generate_game_genres(cur):
    print("inserting game_genres...")
    assigned = {game_id: set() for game_id in range(1, GAMES_COUNT + 1)}
    rows = []

    # кожна гра має мінімум 1 жанр
    for game_id in range(1, GAMES_COUNT + 1):
        genre_id = random.randint(1, GENRES_COUNT)
        assigned[game_id].add(genre_id)
        rows.append((game_id, genre_id))

    # додаємо жанри до рівно 12 500 пар, але не більше 4 жанрів на гру
    while len(rows) < GAME_GENRES_TARGET:
        game_id = random.randint(1, GAMES_COUNT)
        if len(assigned[game_id]) >= 4:
            continue

        available_genres = [genre_id for genre_id in range(1, GENRES_COUNT + 1) if genre_id not in assigned[game_id]]
        genre_id = random.choice(available_genres)
        assigned[game_id].add(genre_id)
        rows.append((game_id, genre_id))

    insert_rows(
        cur,
        """
        insert into game_genres (game_id, genre_id)
        values %s
        """,
        rows,
    )


def generate_platforms(cur):
    print("inserting platforms...")
    rows = [(platform_id, name) for platform_id, name in enumerate(PLATFORM_NAMES, start=1)]
    insert_rows(cur, "insert into platforms (id, name) values %s", rows)


def generate_game_platforms(cur):
    print("inserting game_platforms...")
    assigned = {game_id: set() for game_id in range(1, GAMES_COUNT + 1)}
    rows = []

    # кожна гра має мінімум 1 платформу, більшість підтримує windows
    for game_id in range(1, GAMES_COUNT + 1):
        platform_id = random.choices(
            population=[1, 2, 3],
            weights=[80, 10, 10],
            k=1,
        )[0]
        assigned[game_id].add(platform_id)
        rows.append((game_id, platform_id))

    # ціль — 9 000 пар, тобто в межах 8 000–10 000
    while len(rows) < GAME_PLATFORMS_TARGET:
        game_id = random.randint(1, GAMES_COUNT)
        if len(assigned[game_id]) >= 3:
            continue

        available_platforms = [platform_id for platform_id in range(1, PLATFORMS_COUNT + 1) if platform_id not in assigned[game_id]]
        platform_id = random.choice(available_platforms)
        assigned[game_id].add(platform_id)
        rows.append((game_id, platform_id))

    insert_rows(
        cur,
        """
        insert into game_platforms (game_id, platform_id)
        values %s
        """,
        rows,
    )


def generate_carts(cur, registered_dates):
    print("inserting carts...")
    today = date.today()
    rows = []
    cart_created_dates = [None] * (CARTS_COUNT + 1)

    for cart_id in range(1, CARTS_COUNT + 1):
        user_id = cart_id
        created_at = random_date(registered_dates[user_id], today)
        updated_at = random_date(created_at, today)
        cart_created_dates[cart_id] = created_at
        rows.append((cart_id, user_id, created_at, updated_at))

    insert_rows(
        cur,
        """
        insert into carts (id, user_id, created_at, updated_at)
        values %s
        """,
        rows,
    )

    return cart_created_dates


def build_released_available_games_by_year(game_release_years, available_games):
    result = {}
    for year in range(2020, date.today().year + 1):
        result[year] = [game_id for game_id in available_games if game_release_years[game_id] <= year]
        if len(result[year]) < 5:
            result[year] = available_games[:]
    return result


def generate_orders_items_payments(cur, registered_dates, game_prices, game_release_years, available_games):
    print("inserting orders, order_items and payments...")

    status_values = (
        ["paid"] * int(ORDERS_COUNT * 0.80)
        + ["cancelled"] * int(ORDERS_COUNT * 0.15)
        + ["refunded"] * (ORDERS_COUNT - int(ORDERS_COUNT * 0.80) - int(ORDERS_COUNT * 0.15))
    )
    random.shuffle(status_values)

    # 200 000 orders і рівно 500 000 order_items:
    # 30k*1 + 80k*2 + 60k*3 + 20k*4 + 10k*5 = 500k
    item_counts = [1] * 30_000 + [2] * 80_000 + [3] * 60_000 + [4] * 20_000 + [5] * 10_000
    random.shuffle(item_counts)
    assert len(item_counts) == ORDERS_COUNT
    assert sum(item_counts) == ORDER_ITEMS_TARGET

    released_available_games_by_year = build_released_available_games_by_year(game_release_years, available_games)

    today = date.today()
    order_item_id = 1
    payment_id = 1

    owned_by_user = defaultdict(set)
    library_games_rows = []

    for batch_start in range(1, ORDERS_COUNT + 1, PAGE_SIZE):
        batch_end = min(batch_start + PAGE_SIZE - 1, ORDERS_COUNT)
        orders_rows = []
        order_items_rows = []
        payments_rows = []

        for order_id in range(batch_start, batch_end + 1):
            index = order_id - 1
            user_id = random.randint(1, USERS_COUNT)
            created_at = random_date(registered_dates[user_id], today)
            status = status_values[index]
            items_in_order = item_counts[index]

            eligible_games = released_available_games_by_year.get(created_at.year, available_games)
            selected_games = random.sample(eligible_games, items_in_order)
            total_amount = sum((game_prices[game_id] for game_id in selected_games), Decimal("0.00")).quantize(Decimal("0.01"))

            orders_rows.append((order_id, user_id, created_at, total_amount, status))

            for game_id in selected_games:
                purchase_price = game_prices[game_id]
                order_items_rows.append((order_item_id, order_id, game_id, purchase_price))

                if status == "paid" and game_id not in owned_by_user[user_id]:
                    owned_by_user[user_id].add(game_id)
                    library_games_rows.append((user_id, game_id, order_item_id, created_at))

                order_item_id += 1

            if status == "paid":
                payment_status = "successful"
            elif status == "cancelled":
                payment_status = "failed"
            else:
                payment_status = "refunded"

            payments_rows.append((payment_id, order_id, total_amount, payment_status, f"TX-{payment_id:012d}"))
            payment_id += 1

        insert_rows(
            cur,
            """
            insert into orders (id, user_id, created_at, total_amount, status)
            values %s
            """,
            orders_rows,
        )
        insert_rows(
            cur,
            """
            insert into order_items (id, order_id, game_id, purchase_price)
            values %s
            """,
            order_items_rows,
        )
        insert_rows(
            cur,
            """
            insert into payments (id, order_id, amount, status, transaction_number)
            values %s
            """,
            payments_rows,
        )

        print(f"  inserted orders {batch_start}-{batch_end}")

    assert order_item_id - 1 == ORDER_ITEMS_TARGET
    assert payment_id - 1 == PAYMENTS_COUNT

    return owned_by_user, library_games_rows


def generate_libraries(cur, owned_by_user):
    print("inserting libraries...")
    rows = []

    for library_id in range(1, LIBRARIES_COUNT + 1):
        user_id = library_id
        games_count = len(owned_by_user.get(user_id, set()))
        rows.append((library_id, user_id, games_count))

    insert_rows(
        cur,
        """
        insert into libraries (id, user_id, games_count)
        values %s
        """,
        rows,
    )


def generate_library_games(cur, library_games_rows):
    print(f"inserting library_games: {len(library_games_rows)} rows...")
    insert_rows(
        cur,
        """
        insert into library_games (library_id, game_id, order_item_id, purchased_at)
        values %s
        """,
        library_games_rows,
    )


def generate_cart_items(cur, cart_created_dates, owned_by_user, available_games):
    print("inserting cart_items...")
    today = date.today()
    rows = []
    active_carts_count = int(CARTS_COUNT * 0.30)
    active_cart_ids = random.sample(
        range(1, CARTS_COUNT + 1),
        active_carts_count,
    )
    assigned_games = {cart_id: set() for cart_id in active_cart_ids}

    def choose_game(cart_id):
        owned_games = owned_by_user.get(cart_id, set())
        excluded_games = owned_games | assigned_games[cart_id]

        for _ in range(100):
            game_id = random.choice(available_games)
            if game_id not in excluded_games:
                return game_id

        possible_games = [
            game_id
            for game_id in available_games
            if game_id not in excluded_games
        ]
        if not possible_games:
            return None
        return random.choice(possible_games)

    # кожен активний кошик спочатку отримує одну гру
    for cart_id in active_cart_ids:
        game_id = choose_game(cart_id)
        if game_id is None:
            continue

        assigned_games[cart_id].add(game_id)
        added_at = random_date(cart_created_dates[cart_id], today)
        rows.append((cart_id, game_id, added_at))

    # додаємо до кошиків ще ігри, але не більше п'яти на один кошик
    carts_with_space = active_cart_ids[:]
    while len(rows) < CART_ITEMS_TARGET and carts_with_space:
        cart_id = random.choice(carts_with_space)

        if len(assigned_games[cart_id]) >= 5:
            carts_with_space.remove(cart_id)
            continue

        game_id = choose_game(cart_id)
        if game_id is None:
            carts_with_space.remove(cart_id)
            continue

        assigned_games[cart_id].add(game_id)
        added_at = random_date(cart_created_dates[cart_id], today)
        rows.append((cart_id, game_id, added_at))

    if len(rows) != CART_ITEMS_TARGET:
        raise RuntimeError(
            f"could not generate {CART_ITEMS_TARGET} cart_items; generated {len(rows)}"
        )

    insert_rows(
        cur,
        """
        insert into cart_items (cart_id, game_id, added_at)
        values %s
        """,
        rows,
    )

    print(f"  inserted cart_items: {len(rows)}")


def print_counts(cur):
    tables = [
        "users", "profiles", "developers", "games", "genres", "game_genres", "platforms",
        "game_platforms", "carts", "cart_items", "orders", "order_items", "payments",
        "libraries", "library_games",
    ]

    print("\nfinal row counts:")
    for table in tables:
        cur.execute(f"select count(*) from {table}")
        print(f"  {table}: {cur.fetchone()[0]}")


def main():
    conn = psycopg2.connect(**DB_CONFIG)

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("set local synchronous_commit = off")

                if TRUNCATE_BEFORE_INSERT:
                    print("truncating old data...")
                    truncate_tables(cur)

                registered_dates = generate_users(cur)
                generate_profiles(cur)
                generate_developers(cur)
                game_prices, game_release_years, available_games = generate_games(cur)
                generate_genres(cur)
                generate_game_genres(cur)
                generate_platforms(cur)
                generate_game_platforms(cur)
                cart_created_dates = generate_carts(cur, registered_dates)

                owned_by_user, library_games_rows = generate_orders_items_payments(
                    cur,
                    registered_dates,
                    game_prices,
                    game_release_years,
                    available_games,
                )

                generate_libraries(cur, owned_by_user)
                generate_library_games(cur, library_games_rows)
                generate_cart_items(cur, cart_created_dates, owned_by_user, available_games)

                print_counts(cur)

        print("\ndone")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
