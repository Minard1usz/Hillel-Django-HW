# Завдання 1: Створення класів
class Product:
    def __init__(self, name, category, price, quantity):
        self.name = name
        self.category = category
        self._price = price
        self._quantity = quantity

    def __str__(self):
        return f"Gadget: {self.name} | Category: {self.category} | Price: {self._price}$ | Quantity in stock: {self._quantity}"

    def __repr__(self):
        return self.__str__()

    def change_price(self, new_price):
        if isinstance(new_price, (int, float)) and new_price > 0:
            old_price = self._price
            self._price = new_price
            print(f"The old price for '{self.name}' was changed from {old_price}$ to {new_price}$.)")
        else:
            print("Invalid price. Please enter a number (integer or float).")

    def change_quantity(self, new_quantity):
        if isinstance(new_quantity, int) and new_quantity >= 0:
            old_quantity = self._quantity
            self._quantity = new_quantity
            print(f"The number of '{self.name}' left in stock: {self._quantity}/{old_quantity}.")

            if self._quantity == 0:
                print(f"{self.name} is out of stock.")

        else:
            print("Error: Invalid quantity. Please enter an integer.")

class Order:
    def __init__(self):
        self.list_of_products = []
        self.total_price_of_order = 0

    def add_product(self, product, amount):
        if product._quantity >= amount:
            product.change_quantity(product._quantity - amount)
            for _ in range(amount):
                self.list_of_products.append(product)
        else:
            print(f"Error: Invalid amount of {product.name}. There are only {product._quantity} products in stock.")

    def calculate_price(self):
        self.total_price_of_order = 0
        for product in self.list_of_products:
            self.total_price_of_order += product._price

        return f"{self.total_price_of_order:.2f}$"

    def __str__(self):
        return f"Items ordered: {len(self.list_of_products)}, Total price: {self.calculate_price()}"

    def __repr__(self):
        return self.__str__()

class Customer:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.list_of_orders = []

    def add_order(self, order):
        self.list_of_orders.append(order)

    def __str__(self):
        if not self.list_of_orders:
            orders_info = "No orders yet"
        else:
            orders_info = "; ".join(str(order) for order in self.list_of_orders)

        return f"Customer: {self.name} | {orders_info}"

    def __repr__(self):
        return self.__str__()




# 1. Create the list of gadgets available in our shop
# iPhone17Pro = Product("iPhone 17 Pro", "Smartphones", 1099, 30)
# iPhoneAir = Product("iPhone Air", "Smartphones", 999, 50)
# iPadMini = Product("iPad Mini", "Tablets", 499, 40)
# MacBookNeo = Product("MacBook Neo", "Laptops", 599, 45)
# AppleWatch11 = Product("Apple Watch 11", "Smart Watch", 399, 100)


# 2. Create several customers
# customer_Max = Customer("Max", "email11111@gmail.com")
# customer_Kate = Customer("Kate", "email2222222@gmail.com")


# 3. Create some orders
# order_1 = Order()
# order_2 = Order()


# 4. Add the gadgets into orders
# order_1.add_product(iPhone17Pro, 2)
# order_2.add_product(iPhoneAir, 1)
# order_2.add_product(MacBookNeo, 1)


# 5. Add the orders for customers
# customer_Max.add_order(order_1)
# customer_Kate.add_order(order_2)
# print(customer_Max)
# print(customer_Kate)

# Завдання 2: Взаємодія між класами
def read_products_file():
    all_products = []
    try:
        with open("products.txt", "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue

                data = line.split(",")
                if len(data) == 4:
                    name = data[0]
                    category = data[1]
                    price = float(data[2])
                    quantity = int(data[3])

                    product = Product(name, category, price, quantity)
                    all_products.append(product)
                else:
                    print(f"Skipping invalid line: {line}")

    except FileNotFoundError:
        print("Error: File 'products.txt' was not found.")
    except ValueError:
        print("Error: Invalid data format in file (price or quantity is not a number).")


    return all_products


print(read_products_file())