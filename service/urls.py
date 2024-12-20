from django.urls import path
from . import views

urlpatterns = [

    # for clients
    path('create_order/', views.create_order, name='create_order'),
    path('list_order_offers/<int:order_id>/', views.list_order_offers, name='list_order_offers'),
    path('list_service/', views.list_service, name='list_service'),
    path('list_orders/', views.list_client_orders, name='list_orders'),

    # final offer acceptance
    path('accept_offer/', views.accept_offer, name='accept_offer'),
    path('reject_offer/', views.reject_offer, name='reject_offer'),
    path('complete_order/', views.complete_order, name='complete_order'),
    path('cancel_order/', views.cancel_order, name='cancel_order'),


    # for providers
    path('list_provider_available_orders/', views.list_provider_available_orders, name='list_provider_available_orders'),
    
    path('create_offer/', views.create_offer, name='create_offer'),
    path('order/<int:order_id>/', views.get_order, name='order'),

]