from django.urls import path
from core.views import product_views

urlpatterns = [
    path('products/', product_views.get_all_products),
]
