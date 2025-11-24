
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from market.models import Category, Product,HomeSlider
from core.models import SmallBannerAd

def home(request):
    # Get featured categories and products
    featured_categories = Category.objects.filter(is_active=True)[:6]
    sliders = HomeSlider.objects.filter(is_active=True).order_by('order')
    ads = SmallBannerAd.objects.all()
    featured_products = Product.objects.filter(
        is_active=True, 
        status='published',
        is_featured=True
    )[:8]
    
    sponsored_products = Product.objects.filter(
        is_active=True,
        status='published',
        is_sponsored=True
    )[:4]

    context = {
        'welcome_message': _('Welcome to SokoLetu'),
        'tagline': _('Your Modern Tanzanian Online Marketplace'),
        'featured_categories': featured_categories,
        'featured_products': featured_products,
        'sponsored_products': sponsored_products,
        'sliders':sliders,
        'ads': ads
    }
    return render(request, 'home.html', context)