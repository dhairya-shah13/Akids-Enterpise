from django.contrib import admin
from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'order', 'is_primary')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active', 'parent')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'price', 'mrp',
                    'stock', 'is_active', 'badge', 'updated_at')
    list_editable = ('price', 'mrp', 'stock', 'is_active')
    list_filter = ('category', 'is_active', 'badge', 'is_featured')
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')
    inlines = [ProductImageInline]

    fieldsets = (
        ('Basic Info', {'fields': ('name', 'slug', 'sku', 'category',
                                   'description', 'specifications', 'tags')}),
        ('Pricing', {'fields': ('price', 'mrp')}),
        ('Inventory', {'fields': ('stock', 'is_active', 'is_featured', 'badge')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'),
                        'classes': ('collapse',)}),
    )

    actions = ['mark_active', 'mark_inactive', 'apply_10_percent_discount',
               'apply_20_percent_discount', 'clear_discount']

    @admin.action(description='Mark selected products as active')
    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} product(s) marked as active.')

    @admin.action(description='Mark selected products as inactive')
    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} product(s) marked as inactive.')

    @admin.action(description='Apply 10% discount (price = MRP × 0.90)')
    def apply_10_percent_discount(self, request, queryset):
        count = 0
        for product in queryset.filter(mrp__isnull=False):
            product.price = product.mrp * 0.90
            product.save(update_fields=['price'])
            count += 1
        self.message_user(request, f'10% discount applied to {count} product(s).')

    @admin.action(description='Apply 20% discount (price = MRP × 0.80)')
    def apply_20_percent_discount(self, request, queryset):
        count = 0
        for product in queryset.filter(mrp__isnull=False):
            product.price = product.mrp * 0.80
            product.save(update_fields=['price'])
            count += 1
        self.message_user(request, f'20% discount applied to {count} product(s).')

    @admin.action(description='Clear discount (reset price = MRP)')
    def clear_discount(self, request, queryset):
        count = 0
        for product in queryset.filter(mrp__isnull=False):
            product.price = product.mrp
            product.save(update_fields=['price'])
            count += 1
        self.message_user(request, f'Discount cleared for {count} product(s).')
