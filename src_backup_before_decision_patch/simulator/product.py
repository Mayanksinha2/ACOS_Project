class Product:

    def __init__(
        self,
        product_id,
        name,
        category,
        cost_price,
        selling_price,
        inventory,
        demand_level
    ):
        self.product_id = product_id
        self.name = name
        self.category = category
        self.cost_price = cost_price
        self.selling_price = selling_price
        self.inventory = inventory
        self.demand_level = demand_level

    def profit_per_unit(self):
        return self.selling_price - self.cost_price

    def update_inventory(self, quantity):
        if quantity < 0:
            raise ValueError(
                "Inventory quantity cannot be negative."
            )

        if quantity > self.inventory:
            raise ValueError(
                "Insufficient inventory."
            )

        self.inventory -= quantity

    def update_price(self, new_price):
        if new_price <= 0:
            raise ValueError(
                "Selling price must be greater than zero."
            )

        if new_price < self.cost_price:
            raise ValueError(
                "Selling price cannot be lower than cost price."
            )

        self.selling_price = round(
            float(new_price),
            2
        )

    def apply_price_percentage(
        self,
        operation,
        percentage
    ):
        if percentage < 0:
            raise ValueError(
                "Percentage cannot be negative."
            )

        current_price = self.selling_price

        if operation == "INCREASE":
            new_price = current_price * (
                1 + percentage / 100
            )

        elif operation == "DECREASE":
            new_price = current_price * (
                1 - percentage / 100
            )

        elif operation == "MAINTAIN":
            new_price = current_price

        else:
            raise ValueError(
                f"Unsupported price operation: {operation}"
            )

        self.update_price(new_price)

        return self.selling_price