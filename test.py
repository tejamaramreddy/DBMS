from datetime import datetime
import sys
import mysql.connector
from tabulate import tabulate # type: ignore

def open_database(hostname, user_name, mysql_pw, database_name):
    global connection, cursor
    try:
        connection = mysql.connector.connect(
            host=hostname,
            user=user_name,
            password=mysql_pw,
            database="rm090"
        )
        cursor = connection.cursor()
        print("Connected to MySQL database")
    except mysql.connector.Error as error:
        print("Error connecting to MySQL database:", error)


def printFormat(result):
    header = []
    for cd in cursor.description:  
        header.append(cd[0])
    print('')
    print('Query Result:')
    print('')
    print(tabulate(result, headers=header)) 


def executeSelect(query):
    cursor.execute(query)
    printFormat(cursor.fetchall())


def insert(table, values):
    query = "INSERT into " + table + " values (" + values + ")" + ';'
    cursor.execute(query)
    connection.commit()


def executeUpdate(query):  # use this function for delete and update
    cursor.execute(query)
    connection.commit()


def close_db():  # use this function to close db
    cursor.close()
    connection.close()

mysql_username = 'rm090'  
mysql_password = 'giexahR6'  

# mysql_username = 'root'  
# mysql_password = 'welcome'  

open_database('localhost', mysql_username, mysql_password,
              mysql_username)


def find_available_menu_items():


    try:

        if connection.is_connected():
            #Restaurant name
            restaurant_name = input("Enter restaurant name: ")
            #City of restaurant
            city = input("Enter city: ")
            # Check if the restaurant exists
            cursor.execute("SELECT restaurantID FROM Restaurant WHERE restaurantName = %s AND city = %s", (restaurant_name, city))
            restaurant_id = cursor.fetchone()
            if restaurant_id:
                print(f"\nMenu items available at {restaurant_name} in {city}:\n")
                # Fetch menu items for the given restaurant

                query = f"""
                        SELECT d.dishName, mi.price
                        FROM Restaurant r
                        JOIN MenuItem mi ON r.restaurantID = mi.restaurantNo
                        JOIN Dish d ON mi.dishNo = d.dishNo
                        WHERE r.restaurantName = '{restaurant_name}' AND r.city = '{city}'
                        """

                executeSelect(query)

            else:
                print("Restaurant not found in the given city.")
        else:
            print("Disconnected from database")
    except mysql.connector.Error as error:
        print("Error connecting to MySQL database:", error)

def order_menu_item():
    dish_name = input("Enter the dish name you want to order: ")

    try:

        if connection.is_connected():
          
            # Find the dish
            cursor.execute("SELECT mi.itemNo, r.restaurantName, r.city, mi.price FROM MenuItem mi JOIN Restaurant r ON mi.restaurantNo = r.restaurantID JOIN Dish d ON mi.dishNo = d.dishNo WHERE d.dishName = %s", (dish_name,))
            menu_items = cursor.fetchall()

            if menu_items:
                print("\nAvailable menu items:")
                for item in menu_items:
                    print(f"ItemNo: {item[0]}, Restaurant: {item[1]} ({item[2]}), Price: ${item[3]:.2f}")

                item_no = input("Enter the item number you want to order: ")

                # Add the order to FoodOrder table
                curr_date = datetime.today().strftime('%Y-%m-%d')
                curr_time = datetime.now().strftime("%H:%M")
                insert_string = f"10, {item_no}, {curr_date}, {curr_time}"
                insert_string = ", ".join(insert_string.split(", "))
                cursor.execute("INSERT INTO FoodOrder ( itemNo, date, time) VALUES (%s, %s, %s)", ( item_no, curr_date, curr_time))
                connection.commit()
                #insert("FoodOrder", insert_string)
                print("Order placed successfully!")
            else:
                print("Dish not found.")

    except mysql.connector.Error as error:
        print("Error connecting to MySQL database:", error)

def list_food_orders():
    restaurant_name = input("Enter restaurant name: ")
    city = input("Enter city: ")

    try:

        if connection.is_connected():
            
            # Check if the restaurant exists
            cursor.execute("SELECT restaurantID FROM Restaurant WHERE restaurantName = %s AND city = %s", (restaurant_name, city))
            restaurant_id = cursor.fetchone()

            if restaurant_id:
                print(f"\nFood orders for {restaurant_name} in {city}:\n")

                # Fetch food orders for the given restaurant
                query = f"""
                SELECT d.dishName, mi.price, fo.date, fo.time
                    FROM FoodOrder fo
                    JOIN MenuItem mi ON fo.itemNo = mi.itemNo
                    JOIN Dish d ON mi.dishNo = d.dishNo
                    JOIN Restaurant r ON mi.restaurantNo = r.restaurantID
                    WHERE r.restaurantName = '{restaurant_name}' AND r.city = '{city}'
"""
                executeSelect(query)
            else:
                print("Restaurant not found in the given city.")

    except mysql.connector.Error as error:
        print("Error connecting to MySQL database:", error)

def cancel_food_order():
    try:

        if connection.is_connected():

            # Display all food orders
            executeSelect("""
                SELECT fo.orderNo, d.dishName, r.restaurantName, fo.date, fo.time
                FROM FoodOrder fo
                JOIN MenuItem mi ON fo.itemNo = mi.itemNo
                JOIN Dish d ON mi.dishNo = d.dishNo
                JOIN Restaurant r ON mi.restaurantNo = r.restaurantID
            """)

            order_no = input("Enter the order number you want to cancel: ")
            cursor.execute("SELECT orderNo FROM FoodOrder WHERE orderNo = %s", (order_no,))
            if cursor.fetchone():
                # Remove the order from FoodOrder table
                cursor.execute("DELETE FROM FoodOrder WHERE orderNo = %s", (order_no,))
                connection.commit()
                print("Order canceled successfully!")
            else:
                print("orderNo is not found in Orders")
    except mysql.connector.Error as error:
        print("Error connecting to MySQL database:", error)


def add_new_dish():
    restaurant_name = input("Enter restaurant name: ")
    city = input("Enter city: ")

    try:

        if connection.is_connected():

            # Check if the restaurant exists
            cursor.execute("SELECT restaurantID FROM Restaurant WHERE restaurantName = %s AND city = %s", (restaurant_name, city))
            restaurant_id = cursor.fetchone()

            if restaurant_id:
                dish_name = input("Enter the name of the new dish: ")
                cursor.execute("SELECT dishName FROM Dish WHERE dishName = %s",(dish_name,))
                is_dish = cursor.fetchone()
                if is_dish is None:
                    dish_type = input("Enter the type of the new dish: ")
                    price = float(input("Enter the price of the new dish: "))
                    cursor.execute("select max(DishNo) from Dish;")
                    dish_no = cursor.fetchone()
                    # Insert the new dish into Dish table
                    cursor.execute("INSERT INTO Dish (dishNo, dishName, type) VALUES (%s, %s, %s)", (dish_no[0] + 1, dish_name, dish_type))
                    connection.commit()

                    # Get the dish number of the new dish
                    cursor.execute("select max(itemNo) from MenuItem;")
                    item_no = cursor.fetchone()
                    # Insert the new dish into MenuItem table
                    cursor.execute("INSERT INTO MenuItem (itemNo, restaurantNo, dishNo, price) VALUES (%s, %s, %s, %s)", (item_no[0] + 1, restaurant_id[0], dish_no[0], price))
                    connection.commit()

                    print("New dish added successfully!")
                else:
                    print("Dish is already in menu.")
            else:
                print("Restaurant not found in the given city.")

    except mysql.connector.Error as error:
        print("Error connecting to MySQL database:", error)


def quit_program():
    print("Disconnecting from the database and exiting the program.")
    close_db()
    sys.exit()

menu_options = {
    1: find_available_menu_items,
    2: order_menu_item,
    3: list_food_orders,
    4: cancel_food_order,
    5: add_new_dish,
    6: quit_program
}

def display_menu():
    print("\nMenu:")
    print("1. Find all available menu items at any restaurant")
    print("2. Order an available menu item from a particular restaurant")
    print("3. List all food orders for a particular restaurant")
    print("4. Cancel a food order")
    print("5. Add a new dish for a restaurant")
    print("6. Quit")

if __name__ == "__main__":
    while True:
        display_menu()
        option = int(input("Enter your choice (1-6): "))

        if option in menu_options:
            menu_options[option]()
        else:
            print("Invalid option. Please enter a number between 1 and 6.")


