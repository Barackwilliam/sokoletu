from django.contrib.postgres.search import (
    SearchQuery, SearchVector, SearchRank, SearchHeadline
)
from django.db.models import Q, F, Value, BooleanField, Case, When
from django.db.models.functions import Coalesce
from .models import Product, SponsoredRequest, SearchHistory, Category

class AdvancedProductSearch:
    def __init__(self, request, query=None):
        self.request = request
        self.query = query
        self.user = request.user if request.user.is_authenticated else None
        self.session_key = request.session.session_key
    
    def search(self, category_slug=None, filters=None):
        if not self.query:
            return Product.objects.none()
        
        # Save search history
        self._save_search_history()
        
        # Base queryset
        base_products = Product.objects.filter(
            is_active=True, 
            status='published'
        ).select_related('category', 'shop').prefetch_related('images')
        
        # Apply category filter
        if category_slug:
            category = Category.objects.filter(slug=category_slug, is_active=True).first()
            if category:
                base_products = base_products.filter(category=category)
        
        # Apply additional filters
        if filters:
            base_products = self._apply_filters(base_products, filters)
        
        # Full-text search with PostgreSQL
        search_vector = (
            SearchVector('name', weight='A', config='english') +
            SearchVector('description', weight='B', config='english') +
            SearchVector('short_description', weight='B', config='english') +
            SearchVector('brand', weight='C', config='english') +
            SearchVector('category__name', weight='C', config='english')
        )
        
        search_query = SearchQuery(self.query, config='english')
        
        # Perform search with ranking
        products = base_products.annotate(
            rank=SearchRank(search_vector, search_query),
            search_headline=SearchHeadline(
                'description',
                search_query,
                start_sel='<mark class="search-highlight">',
                stop_sel='</mark>',
                max_words=50
            )
        ).filter(
            Q(search_vector=search_query) |
            Q(name__icontains=self.query) |
            Q(description__icontains=self.query) |
            Q(short_description__icontains=self.query) |
            Q(brand__icontains=self.query) |
            Q(category__name__icontains=self.query)
        ).distinct()
        
        return self._apply_sponsored_ranking(products)
    
    def _apply_filters(self, queryset, filters):
        """Apply price and other filters"""
        min_price = filters.get('min_price')
        max_price = filters.get('max_price')
        
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        return queryset
    
    def _apply_sponsored_ranking(self, products):
        """Apply sponsored product ranking"""
        active_sponsored = SponsoredRequest.objects.filter(
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).select_related('product')
        
        sponsored_product_ids = [sp.product.id for sp in active_sponsored]
        
        # Record impressions for sponsored products
        for sponsored in active_sponsored:
            sponsored.record_impression()
        
        # Annotate with sponsored flag and boost ranking
        products = products.annotate(
            is_sponsored=Case(
                When(id__in=sponsored_product_ids, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),
            boosted_rank=Case(
                When(id__in=sponsored_product_ids, then=F('rank') + Value(1.0)),
                default=F('rank'),
                output_field=models.FloatField()
            )
        )
        
        # Order by sponsored first, then by boosted rank
        return products.order_by('-is_sponsored', '-boosted_rank', '-created_at')
    
    def _save_search_history(self):
        """Save user search history"""
        if self.query.strip():
            results_count = Product.objects.filter(
                Q(search_vector=SearchQuery(self.query)) |
                Q(name__icontains=self.query) |
                Q(description__icontains=self.query)
            ).count()
            
            SearchHistory.objects.create(
                user=self.user,
                query=self.query,
                results_count=results_count,
                session_key=self.session_key
            )
    
    def get_search_suggestions(self, limit=5):
        """Get search suggestions based on history and popular searches"""
        if not self.query or len(self.query) < 2:
            return []
        
        # Get similar products for suggestions
        products = Product.objects.filter(
            Q(name__icontains=self.query) |
            Q(category__name__icontains=self.query),
            is_active=True,
            status='published'
        ).select_related('category')[:limit]
        
        suggestions = []
        for product in products:
            suggestions.append({
                'type': 'product',
                'name': product.name,
                'category': product.category.name,
                'url': product.get_absolute_url()
            })
        
        return suggestions







# from django.db import models
# from django.db.models import Q, F, Value, BooleanField, Case, When
# from django.db.models.functions import Coalesce
# from .models import Product, SponsoredRequest, SearchHistory, Category
# from django.utils import timezone

# class AdvancedProductSearch:
#     def __init__(self, request, query=None):
#         self.request = request
#         self.query = query
#         self.user = request.user if request.user.is_authenticated else None
#         self.session_key = request.session.session_key
    
#     def search(self, category_slug=None, filters=None):
#         if not self.query:
#             return Product.objects.none()
        
#         # Save search history
#         self._save_search_history()
        
#         # Base queryset
#         base_products = Product.objects.filter(
#             is_active=True, 
#             status='published'
#         ).select_related('category', 'shop').prefetch_related('images')
        
#         # Apply category filter
#         if category_slug:
#             category = Category.objects.filter(slug=category_slug, is_active=True).first()
#             if category:
#                 base_products = base_products.filter(category=category)
        
#         # Apply additional filters
#         if filters:
#             base_products = self._apply_filters(base_products, filters)
        
#         # SQLite-compatible search (removed PostgreSQL-specific code)
#         products = base_products.filter(
#             Q(name__icontains=self.query) |
#             Q(description__icontains=self.query) |
#             Q(short_description__icontains=self.query) |
#             Q(brand__icontains=self.query) |
#             Q(category__name__icontains=self.query)
#         ).distinct()
        
#         # Apply ranking based on relevance (simple SQLite-compatible ranking)
#         products = self._apply_sqlite_ranking(products)
        
#         return self._apply_sponsored_ranking(products)
    
#     def _apply_sqlite_ranking(self, products):
#         """Apply simple relevance ranking for SQLite"""
#         # Simple ranking based on field matches
#         products = products.annotate(
#             relevance_score=Case(
#                 # Name matches get highest score
#                 When(name__icontains=self.query, then=Value(100)),
#                 # Brand matches
#                 When(brand__icontains=self.query, then=Value(80)),
#                 # Category matches
#                 When(category__name__icontains=self.query, then=Value(60)),
#                 # Description matches
#                 When(description__icontains=self.query, then=Value(40)),
#                 default=Value(20),
#                 output_field=models.IntegerField()
#             )
#         )
        
#         return products.order_by('-relevance_score', '-created_at')
    
#     def _apply_filters(self, queryset, filters):
#         """Apply price and other filters"""
#         min_price = filters.get('min_price')
#         max_price = filters.get('max_price')
        
#         if min_price:
#             queryset = queryset.filter(price__gte=min_price)
#         if max_price:
#             queryset = queryset.filter(price__lte=max_price)
        
#         return queryset
    
#     def _apply_sponsored_ranking(self, products):
#         """Apply sponsored product ranking"""
#         active_sponsored = SponsoredRequest.objects.filter(
#             status='active',
#             start_date__lte=timezone.now(),
#             end_date__gte=timezone.now()
#         ).select_related('product')
        
#         sponsored_product_ids = [sp.product.id for sp in active_sponsored]
        
#         # Record impressions for sponsored products
#         for sponsored in active_sponsored:
#             sponsored.record_impression()
        
#         # Annotate with sponsored flag
#         products = products.annotate(
#             is_sponsored=Case(
#                 When(id__in=sponsored_product_ids, then=Value(True)),
#                 default=Value(False),
#                 output_field=BooleanField()
#             )
#         )
        
#         # Order by sponsored first, then by relevance
#         return products.order_by('-is_sponsored', '-relevance_score', '-created_at')
    
#     def _save_search_history(self):
#         """Save user search history"""
#         if self.query.strip():
#             # Simple count for SQLite compatibility
#             results_count = Product.objects.filter(
#                 Q(name__icontains=self.query) |
#                 Q(description__icontains=self.query) |
#                 Q(brand__icontains=self.query)
#             ).count()
            
#             SearchHistory.objects.create(
#                 user=self.user,
#                 query=self.query,
#                 results_count=results_count,
#                 session_key=self.session_key
#             )
    
#     def get_search_suggestions(self, limit=5):
#         """Get search suggestions based on history and popular searches"""
#         if not self.query or len(self.query) < 2:
#             return []
        
#         # Get similar products for suggestions
#         products = Product.objects.filter(
#             Q(name__icontains=self.query) |
#             Q(category__name__icontains=self.query),
#             is_active=True,
#             status='published'
#         ).select_related('category')[:limit]
        
#         suggestions = []
#         for product in products:
#             suggestions.append({
#                 'type': 'product',
#                 'name': product.name,
#                 'category': product.category.name,
#                 'url': product.get_absolute_url()
#             })
        
#         return suggestions