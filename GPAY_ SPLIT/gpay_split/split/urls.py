from django.urls import path
from split import views

urlpatterns = [
    path('add_user/', views.add_user, name='add_user'),
    path('add_money/', views.add_money, name='add_money'),
    path('add_splits/', views.add_splits, name='add_splits'),
    path('remove_split/', views.remove_split, name='remove_split'),
    path('split_payment/', views.split_payment, name='split_payment'),
]
