class Customer:

    def __init__(
        self,
        customer_id,
        age,
        budget,
        preference,
        price_sensitivity
    ):

        self.customer_id = customer_id
        self.age = age
        self.budget = budget
        self.preference = preference
        self.price_sensitivity = price_sensitivity


    def purchase_probability(self, product):

        probability = 0.5


        # Check category preference

        if product.category == self.preference:
            probability += 0.2


        # Check budget

        if product.selling_price <= self.budget:
            probability += 0.2

        else:
            probability -= 0.2


        # Price sensitivity adjustment

        if self.price_sensitivity == "High":

            if product.selling_price > self.budget:
                probability -= 0.2


        return max(0, min(probability, 1))