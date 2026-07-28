from simulator.product import Product
from simulator.customer import Customer



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



score = customer.purchase_probability(product)


print(score)