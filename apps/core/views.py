from django.views.generic import TemplateView
from apps.products.models import Product


class HomeView(TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Product.objects.filter(
            is_active=True, is_featured=True
        ).select_related('category')[:8]
        return context


class RFSportsView(TemplateView):
    template_name = 'core/rf_sports.html'
