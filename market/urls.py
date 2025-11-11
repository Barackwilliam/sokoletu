from django.urls import path, include
from .views import *
from . import views

app_name = 'market'

urlpatterns = [
    # Shop management URLs - PUT THESE FIRST with clear prefixes
    path('shop/<slug:slug>/', views.shop_detail, name='shop_detail'),
    path('shop/<slug:shop_slug>/add-product/', views.add_product, name='add_product'),
    path('categories/json/', views.categories_json, name='categories_json'),

    path('shop/create/', views.create_shop, name='create_shop'),
    path('shop/dashboard/', views.shop_dashboard, name='shop_dashboard'),
    path('shop/edit/', views.shop_edit, name='shop_edit'),
    
    # Products
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Search & Features
    path('search/', views.ProductSearchView.as_view(), name='product_search'),
    path('search/analytics/', views.search_analytics, name='search_analytics'),
    path('search/suggestions/', views.search_suggestions, name='search_suggestions'),
    path('sponsored/<int:sponsored_id>/click/', views.track_sponsored_click, name='track_sponsored_click'),
    
    # Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('category/<slug:slug>/', views.ProductListView.as_view(), name='category_products'),
    
    # Featured & Sponsored
    path('featured/', views.featured_products, name='featured_products'),
    path('sponsored/', views.sponsored_products, name='sponsored_products'),
    
    # Marketplace homepage and shop detail - KEEP THESE LAST
    # path('shop/<slug:slug>/', views.shop_detail, name='shop_detail'), 
]