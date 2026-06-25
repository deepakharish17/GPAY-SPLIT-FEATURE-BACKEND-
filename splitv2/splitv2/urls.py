from django.urls import path
from splitv2 import views

urlpatterns = [
    path('add_user/', views.add_user, name='add_user'),
    path('add_money/', views.add_money, name='add_money'),
    path('add_splits/', views.add_splits, name='add_splits'),
    path('remove_split/', views.remove_split, name='remove_split'),
    path('split_payment/', views.split_payment, name='split_payment'),
    path('get_all_split_by_user/',views.get_all_split_by_user, name='get_all_split_by_user'),
    path('pay_multiple_splits/',views.pay_multiple_splits, name='pay_multiple_splits'),
]
