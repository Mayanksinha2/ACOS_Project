from simulator.market import Market



market = Market(
    "Diwali",
    1.5,
    0.9,
    120
)


condition = market.get_market_condition()


print(condition)