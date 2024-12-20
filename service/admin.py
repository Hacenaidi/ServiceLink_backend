from django.contrib import admin
from .models import Order, Service, offer,OrderMedia

# Register your models here.



admin.site.register(Service)
admin.site.register(offer)
admin.site.register(Order)
admin.site.register(OrderMedia)
