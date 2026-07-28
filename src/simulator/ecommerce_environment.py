class EcommerceEnvironment:


    def __init__(
        self,
        products,
        customers,
        market
    ):

        self.products = products
        self.customers = customers
        self.market = market

        self.total_sales = 0
        self.total_revenue = 0



    def simulate_customer_purchase(
        self,
        customer,
        product
    ):


        probability = customer.purchase_probability(product)


        if probability >= 0.7 and product.inventory > 0:


            product.update_inventory(1)


            self.total_sales += 1


            self.total_revenue += product.selling_price


            return True


        return False



    def get_business_status(self):

        return {

            "sales":
            self.total_sales,


            "revenue":
            self.total_revenue

        }
