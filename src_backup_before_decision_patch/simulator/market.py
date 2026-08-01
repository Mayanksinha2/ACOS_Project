class Market:


    def __init__(
        self,
        season,
        demand_multiplier,
        competitor_price_factor,
        advertising_cost
    ):

        self.season = season
        self.demand_multiplier = demand_multiplier
        self.competitor_price_factor = competitor_price_factor
        self.advertising_cost = advertising_cost



    def get_market_condition(self):

        return {

            "season": self.season,

            "demand_multiplier":
            self.demand_multiplier,

            "competitor_price_factor":
            self.competitor_price_factor,

            "advertising_cost":
            self.advertising_cost

        }
