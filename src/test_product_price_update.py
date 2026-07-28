from simulator.product import Product


product = Product(
    product_id="SKU-101",
    name="Pink Frock",
    category="Kids Wear",
    cost_price=350,
    selling_price=800,
    inventory=20,
    demand_level="High"
)


product.apply_price_percentage(
    "INCREASE",
    10
)

assert product.selling_price == 880


product.apply_price_percentage(
    "DECREASE",
    10
)

assert product.selling_price == 792


product.apply_price_percentage(
    "MAINTAIN",
    0
)

assert product.selling_price == 792


print("Product price update test passed.")