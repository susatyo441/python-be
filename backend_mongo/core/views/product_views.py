# core/views/product_views.py
from core.models.product import Product
from core.utils.response import api_response

def get_all_products(request):
    products = Product.objects()
    result = [p.to_mongo().to_dict() for p in products]
    return api_response(result, message="Produk berhasil diambil")
