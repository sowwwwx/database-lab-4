NotSteam database for online game store with users, profiles, developers, games, carts, orders, payments and libraries.
Disclaimer: all coincidences are random, all rights reserved

- users: registered users with email, password, role, status and registration date
- profiles: user profile data with first name, last name, nickname, birthday year and country
- developers: game developers with name, country and founded year
- games: game catalog with developer, name, price, release year and status
- genres: game genres
- platforms: supported game platforms
- carts: user carts
- cart_items: games added to carts
- orders: completed user orders
- order_items: games inside each order
- payments: payment information for orders
- libraries: user game libraries
- library_games: games owned by users

--relationships--

1:1 relation between users and profiles, carts, libraries  
1:many relation between developers and games  
1:many relation between users and orders  
many:many relation between games and genres + platforms  
many:many relation between libraries and games  

--constraints--

primary keys and foreign keys are used to connect tables
unique constraints are used for email, nickname, developer name, genre name, platform name and transaction number
check constraints are used for user role, user status, game price, game status, order total amount, order status, payment amount, payment status and library games count

--trigger--

update_cart_date trigger automatically updates cart updated_at date after adding a new game to cart_items

--procedure--

purchase_cart procedure creates a paid order from user cart:
- finds user cart
- calculates total amount
- creates order
- creates order_items from cart_items
- creates payment
- clears cart after purchase

--view--

game_catalog view shows game catalog with game name, developer name, price, release year, status

--database users--

notsteam_admin has full access to main tables

catalog_manager can select, insert, update and delete catalog tables

notsteam_analyst can select data from game_catalog, orders, order_items and payments

--indexes--

idx_order_items_game_id index is used to optimize search in order_items by game_id

--tests--

- select games from game_catalog
- find users with not empty cart
- call purchase_cart for selected user
- compare explain analyze before and after index

///insert data for tables was generated with ai help https://chatgpt.com/share/6a3d3d28-d764-83ed-9bb0-77d7b5bb92a1
