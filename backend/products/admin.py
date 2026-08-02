from django.contrib import admin
from .models import Product, Inquiry, ProductClassSpec, ProductDimensionSpec


class ProductClassSpecInline(admin.TabularInline):
    model = ProductClassSpec
    extra = 1
    fields = ('class_label', 'age_min', 'age_max', 'order')


class ProductDimensionSpecInline(admin.TabularInline):
    model = ProductDimensionSpec
    extra = 1
    fields = ('group_label', 'component', 'length', 'width', 'height', 'unit', 'notes', 'order')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    inlines = [ProductClassSpecInline, ProductDimensionSpecInline]


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'contact_number', 'quantity', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'contact_number', 'product__name')


@admin.register(ProductClassSpec)
class ProductClassSpecAdmin(admin.ModelAdmin):
    list_display = ('product', 'class_label', 'age_min', 'age_max', 'order')
    search_fields = ('product__name', 'class_label')


@admin.register(ProductDimensionSpec)
class ProductDimensionSpecAdmin(admin.ModelAdmin):
    list_display = ('product', 'group_label', 'component', 'length', 'width', 'height', 'unit', 'notes', 'order')
    list_filter = ('unit',)
    search_fields = ('product__name', 'group_label', 'component')

