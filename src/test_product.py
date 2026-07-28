from simulator.product import Product


dress = Product(
    1,
    "Pink Frock",
    "Kids Wear",
    350,
    799,
    100,
    "High"
)


print(dress.name)

print(
    dress.profit_per_unit()
)