import datetime
from django.contrib import admin
from django.db.models import Sum, Count, Avg, F
from django.db.models.functions import TruncDay
from django.template.response import TemplateResponse
from django.urls import path

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'product_name_snapshot', 'sku_snapshot',
                       'price_snapshot', 'quantity', 'total')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'payment_status',
                    'total', 'created_at')
    list_filter = ('status', 'payment_status')
    search_fields = ('order_number', 'user__email')
    readonly_fields = ('order_number', 'user', 'shipping_address',
                       'subtotal', 'tax', 'shipping_charge', 'total',
                       'payment_status', 'created_at')
    list_editable = ('status',)
    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Info', {'fields': ('order_number', 'user', 'status', 'payment_status')}),
        ('Financials', {'fields': ('subtotal', 'tax', 'shipping_charge', 'total')}),
        ('Shipping', {'fields': ('shipping_address',)}),
        ('Other', {'fields': ('notes', 'warranty_start_date', 'created_at')}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name_snapshot', 'sku_snapshot',
                    'price_snapshot', 'quantity', 'total')
    list_filter = ('order__status',)
    search_fields = ('product_name_snapshot', 'sku_snapshot', 'order__order_number')


# ─── Custom Sales Report Admin View ─────────────────────────────


class SalesReportAdmin(admin.ModelAdmin):
    """Proxy model admin for the sales report custom view."""

    class Meta:
        app_label = 'orders'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_site.admin_view(self.sales_report_view),
                 name='sales_report'),
        ]
        return custom_urls + urls

    def sales_report_view(self, request):
        """Custom admin view showing revenue, orders, and top products."""
        today = datetime.date.today()
        month_start = today.replace(day=1)
        thirty_days_ago = today - datetime.timedelta(days=30)

        # Only count paid/simulated orders
        paid_orders = Order.objects.filter(payment_status__in=['SIMULATED', 'PAID'])

        # Summary cards
        total_revenue = paid_orders.aggregate(total=Sum('total'))['total'] or 0
        month_revenue = paid_orders.filter(
            created_at__date__gte=month_start
        ).aggregate(total=Sum('total'))['total'] or 0
        total_order_count = paid_orders.count()
        month_order_count = paid_orders.filter(created_at__date__gte=month_start).count()
        avg_order_value = paid_orders.aggregate(avg=Avg('total'))['avg'] or 0

        # Revenue by Day — last 30 days
        daily_revenue = (
            paid_orders
            .filter(created_at__date__gte=thirty_days_ago)
            .annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(
                order_count=Count('id'),
                revenue=Sum('total'),
            )
            .order_by('-day')
        )

        # Top 10 Best-Selling Products
        top_products = (
            OrderItem.objects
            .filter(order__payment_status__in=['SIMULATED', 'PAID'])
            .values('sku_snapshot', 'product_name_snapshot')
            .annotate(
                units_sold=Sum('quantity'),
                revenue=Sum('total'),
            )
            .order_by('-units_sold')[:10]
        )

        # Revenue by Category
        from apps.products.models import Category
        category_revenue = (
            OrderItem.objects
            .filter(order__payment_status__in=['SIMULATED', 'PAID'])
            .values(category_name=F('product__category__name'))
            .annotate(
                order_count=Count('order', distinct=True),
                revenue=Sum('total'),
            )
            .order_by('-revenue')
        )

        # Calculate percentage of total
        for cat in category_revenue:
            if total_revenue > 0:
                cat['pct'] = round(float(cat['revenue']) / float(total_revenue) * 100, 1)
            else:
                cat['pct'] = 0

        context = {
            **self.admin_site.each_context(request),
            'title': 'Sales Report',
            'total_revenue': total_revenue,
            'month_revenue': month_revenue,
            'total_order_count': total_order_count,
            'month_order_count': month_order_count,
            'avg_order_value': avg_order_value,
            'daily_revenue': daily_revenue,
            'top_products': top_products,
            'category_revenue': category_revenue,
        }

        return TemplateResponse(request, 'admin/sales_report.html', context)


# Create a proxy model to register the sales report in admin
class SalesReport(Order):
    class Meta:
        proxy = True
        verbose_name = 'Sales Report'
        verbose_name_plural = 'Sales Reports'
        app_label = 'orders'


admin.site.register(SalesReport, SalesReportAdmin)
