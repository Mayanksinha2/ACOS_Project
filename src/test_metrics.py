from simulator.product import Product
from simulator.metrics import Metrics



product = Product(
    1,
    "Pink Frock",
    "Kids Wear",
    350,
    799,
    100,
    "High"
)



metrics = Metrics()



for i in range(100):

    metrics.record_visit()



for i in range(10):

    metrics.record_sale(product)



print(
    metrics.report()
)
