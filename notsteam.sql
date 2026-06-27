--update cart date--
create function update_cart_date()
returns trigger
language plpgsql
as $$
begin
    update carts
    set updated_at = current_date
    where id = new.cart_id;

    return new;
end;
$$;

create trigger update_cart_date_trigger
after insert on cart_items
for each row
execute function update_cart_date();



--purchase cart--
create procedure purchase_cart(
    p_user_id integer
)
language plpgsql
as $$
declare
    v_cart_id integer;
    v_order_id integer;
    v_total_amount numeric(12, 2);
begin
    select id
    into v_cart_id
    from carts
    where user_id = p_user_id;

    select sum(g.price)
    into v_total_amount
    from cart_items ci
    join games g
        on g.id = ci.game_id
    where ci.cart_id = v_cart_id;

    insert into orders (
        user_id,
        created_at,
        total_amount,
        status
    )
    values (
        p_user_id,
        current_date,
        v_total_amount,
        'paid'
    )
    returning id into v_order_id;

    insert into order_items (
        order_id,
        game_id,
        purchase_price
    )
    select
        v_order_id,
        ci.game_id,
        g.price
    from cart_items ci
    join games g
        on g.id = ci.game_id
    where ci.cart_id = v_cart_id;

    insert into payments (
        order_id,
        amount,
        status,
        transaction_number
    )
    values (
        v_order_id,
        v_total_amount,
        'successful',
        'trans-num-' || v_order_id
    );

    delete from cart_items
    where cart_id = v_cart_id;
end;
$$;

--game catalog--
create view game_catalog as
select
    g.id as game_id,
    g.name as game_name,
    d.name as developer_name,
    g.price,
    g.release_year,
    g.status
from games g
join developers d
    on d.id = g.developer_id;


--database users--
create role notsteam_admin
login password 'admin';

create role catalog_manager
login password 'manager';

create role notsteam_analyst
login password 'analyst';




--admin permissions--
grant connect on database notsteam to notsteam_admin;
grant usage on schema public to notsteam_admin;
grant all privileges on users, profiles, developers, games, genres, game_genres,
    platforms, game_platforms, carts, cart_items, orders, order_items,
    payments, libraries, library_games to notsteam_admin;

--manager permissions--
grant connect on database notsteam to catalog_manager;
grant usage on schema public to catalog_manager;
grant select, insert, update, delete on developers, games, genres, game_genres, platforms, game_platforms to catalog_manager;
grant select on game_catalog to catalog_manager;

--analyst permissions--
grant connect on database notsteam to notsteam_analyst;
grant usage on schema public to notsteam_analyst;
grant select on game_catalog, orders, order_items, payments to notsteam_analyst;



--find users with not empty cart--
select u.id
from users u
join carts c
    on c.user_id = u.id
join cart_items ci
    on ci.cart_id = c.id
group by u.id
limit 10;
--test procedure--
call purchase_cart(10);



--test without index--
explain analyze
select *
from order_items
where game_id = 1;

--create index--
create index idx_order_items_game_id
on order_items(game_id);

--test with index--
explain analyze
select *
from order_items
where game_id = 1;


--test view--
select *
from game_catalog
limit 20;