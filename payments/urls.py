from django.urls import path
from . import views

urlpatterns = [
    path('', views.initiate_payment, name='initiate_payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('get-rate/', views.get_rate, name='get_rate')

]