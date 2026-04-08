# Завдання 1: Створення класів
class Product:
    def __init__(self, name, category, price, quantity):
        self.name = name
        self.category = category
        self._price = price
        self._quantity = quantity

    def __str__(self):
        return f"Gadget: {self.name} | Category: {self.category} | Price: {self._price}$ | Quantity in stock: {self._quantity}"

    def change_price(self, new_price):
        if isinstance(new_price, (int, float)) and new_price > 0:
            old_price = self._price
            self._price = new_price
            print(f"The old price for '{self.name}' was changed from {old_price}$ to {new_price}$.)")
        else:
            print("Invalid price. Please enter a number (integer or float).")
            return

        if new_price <= 0:
            print("Invalid price. Please enter a positive number.")


    def change_quantity(self, new_quantity):
        if isinstance(new_quantity, int) and new_quantity >= 0:
            old_quantity = self._quantity
            self._quantity = new_quantity
            print(f"Initial number of '{self.name}' in stock: {old_quantity}.\n"
                  f"Current number of '{self.name}': {self._quantity}.")

            if self._quantity == 0:
                print(f"{self.name} is out of stock.")

        else:
            print("Error: Invalid quantity. Please enter an integer.")



iPhone17Pro = Product("iPhone 17 Pro", "Smartphones", 1099, 30)
iPhoneAir = Product("iPhone Air", "Smartphones", 999, 50)
iPadMini = Product("iPad Mini", "Tablets", 499, 40)
MacBookNeo = Product("MacBook Neo", "Laptops", 599, 45)
AppleWatch11 = Product("Apple Watch 11", "Smart Watch", 399, 100)

# print(iPhone17Pro)
# iPhone17Pro.change_price(200)
# iPhoneAir.change_price(100)

# iPhone17Pro.change_quantity(10)