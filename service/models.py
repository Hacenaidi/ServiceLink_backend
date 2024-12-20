from django.db import models
from django.contrib.auth.models import User

from provider.models import Provider


# Create your models here. 
class Service(models.Model):  
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  

 

    def __str__(self):
        return self.name
    


class Order(models.Model):
    STATES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )

    #upload may image for the order
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    Confirmed_provider = models.ForeignKey(Provider, on_delete=models.CASCADE, null=True, blank=True)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)

    title = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=150)


    # the order can have many offers and offer can only be assigned to one order
    
    accepted_offer = models.ForeignKey("service.offer", on_delete=models.CASCADE, null=True, blank=True)

    proposed_price_range_min = models.DecimalField(max_digits=10, decimal_places=2)
    proposed_price_range_max = models.DecimalField(max_digits=10, decimal_places=2)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='TND')

    state = models.CharField(max_length=10, choices=STATES, default='pending')

    

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title



class offer(models.Model):
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)
    Order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='offers')
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2, default=0,blank=True, null=True)
    description = models.TextField(null=True, blank=True)
    #status boolean true ou flase
    accepted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Offer from {self.provider.user.username} for order {self.Order.title}"


    
class OrderMedia(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='order_media/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Media for order: {self.order.title}"