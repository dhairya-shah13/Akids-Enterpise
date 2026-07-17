from django.contrib import admin
from .models import Product, Inquiry

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'description')


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'contact_number', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'contact_number', 'product__name')
