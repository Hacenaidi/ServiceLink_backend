from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_provider_request, name='create_provider_request'),
    path('requests/', views.list_provider_requests, name='list_provider_requests'),
    path('approve/<int:provider_id>/', views.approve_provider, name='approve_provider'),
    # path('reject/<int:provider_id>/', views.reject_provider, name='reject_provider'),
    # path(')

]