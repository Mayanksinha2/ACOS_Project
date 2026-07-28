from simulator.product import Product
from simulator.customer import Customer
from simulator.market import Market
from simulator.ecommerce_environment import EcommerceEnvironment



product = Product(
    1,
    "Pink Frock",
    "Kids Wear",
    350,
    799,
    100,
    "High"
)



customer = Customer(
    101,
    30,
    1000,
    "Kids Wear",
    "Medium"
)



market = Market(
    "Diwali",
    1.5,
    0.9,
    120
)



environment = EcommerceEnvironment(
    [product],
    [customer],
    market
)



result = environment.simulate_customer_purchase(
    customer,
    product
)



print("Purchase:", result)


print(
    environment.get_business_status()
)


print(
    "Remaining Stock:",
    product.inventory
)
