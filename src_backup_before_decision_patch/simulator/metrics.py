class Metrics:


    def __init__(self):

        self.visitors = 0
        self.sales = 0
        self.revenue = 0
        self.cost = 0



    def record_visit(self):

        self.visitors += 1



    def record_sale(self, product):

        self.sales += 1

        self.revenue += product.selling_price

        self.cost += product.cost_price



    def profit(self):

        return self.revenue - self.cost



    def conversion_rate(self):

        if self.visitors == 0:
            return 0

        return self.sales / self.visitors



    def report(self):

        return {

            "Visitors":
            self.visitors,

            "Sales":
            self.sales,

            "Revenue":
            self.revenue,

            "Profit":
            self.profit(),

            "Conversion Rate":
            self.conversion_rate()

        }
