from django.db import models

class Citys(models.Model):
    REGIONS = (('A','Akdeniz'), ('DA','Dogu Anadolu'), ('E','Ege'), ('GA','Guneydogu Anadolu'), ('IA','Ic Anadolu'), ('M','Marmara'), ('K','Karadeniz'))

    city_name = models.CharField(max_length=50, primary_key=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    population = models.IntegerField()
    region = models.CharField(max_length=50, choices=REGIONS) 

    def __str__(self):
        return "city: {}".format(self.city_name)

class Customers(models.Model):
    customer_name = models.ForeignKey(Citys, on_delete=models.CASCADE)
    demand = models.IntegerField()

    def __str__(self):
        return "Customer, {}".format(self.customer_name)

class Suppliers(models.Model):
    supplier_name = models.ForeignKey(Citys, on_delete=models.CASCADE)
    operating_cost = models.FloatField()
    capacity = models.IntegerField() 

    def __str__(self):
        return "Supplier, {}".format(self.supplier_name)

class Shipping(models.Model):
    supplier = models.ForeignKey(Suppliers, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    distance = models.FloatField()
    unit_cost = models.FloatField()

    def __str__(self):
        return "Shipping from {} to {}".format(self.supplier, self.customer)

class Sales(models.Model):
    sale_date = models.CharField(max_length=50)
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    amount = models.IntegerField()

    def __str__(self):
        return "Amount of {} sold on {} for customer id: {}".format(self.amount, self.sale_date, self.customer)






