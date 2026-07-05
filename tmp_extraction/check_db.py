"""Check current database state."""
import django, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','little_fingers.settings')
django.setup()
from products.models import Product

print(f'Total products: {Product.objects.count()}')
print(f'INDOORS: {Product.objects.filter(category="INDOORS").count()}')
print(f'OUTDOORS: {Product.objects.filter(category="OUTDOORS").count()}')
print(f'PARTS: {Product.objects.filter(category="PARTS").count()}')
print(f'MRSPORTS: {Product.objects.filter(category="MRSPORTS").count()}')

for p in Product.objects.filter(category="INDOORS"):
    print(f'  ID={p.id} | {p.name[:60]} | SKU={p.sku} | Rs.{p.price}')
