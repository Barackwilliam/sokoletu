from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from .models import Product, ProductView, SearchHistory

class RecommendationEngine:
    def __init__(self, request):
        self.request = request
        self.user = request.user if request.user.is_authenticated else None
        self.session_key = request.session.session_key
    
    def get_recommendations(self, product=None, limit=8):
        """Get personalized product recommendations"""
        cache_key = f"recommendations_{self.session_key}"
        recommendations = cache.get(cache_key)
        
        if recommendations is None:
            if product:
                recommendations = self._get_similar_products(product, limit)
            elif self.user:
                recommendations = self._get_personalized_recommendations(limit)
            else:
                recommendations = self._get_popular_products(limit)
            
            # Cache for 15 minutes
            cache.set(cache_key, recommendations, 900)
        
        return recommendations
    
    def _get_similar_products(self, product, limit):
        """Get products similar to the current one"""
        similar_products = Product.objects.filter(
            category=product.category,
            is_active=True,
            status='published'
        ).exclude(id=product.id).select_related('shop').prefetch_related('images')[:limit]
        
        return similar_products
    
    def _get_personalized_recommendations(self, limit):
        """Get personalized recommendations based on user behavior"""
        # Get user's viewed products
        viewed_products = ProductView.objects.filter(
            user=self.user
        ).select_related('product').order_by('-viewed_at')[:10]
        
        if not viewed_products:
            return self._get_popular_products(limit)
        
        # Get categories from viewed products
        viewed_categories = set([vp.product.category_id for vp in viewed_products])
        
        # Get search history for additional context
        search_terms = SearchHistory.objects.filter(
            user=self.user
        ).values_list('query', flat=True)[:5]
        
        # Build recommendations query
        recommendations = Product.objects.filter(
            Q(category_id__in=viewed_categories) |
            Q(name__icontains=search_terms[0]) if search_terms else Q(),
            is_active=True,
            status='published'
        ).exclude(
            id__in=[vp.product_id for vp in viewed_products]
        ).select_related('shop').prefetch_related('images')[:limit]
        
        return recommendations
    
    def _get_popular_products(self, limit):
        """Get currently popular products"""
        return Product.objects.filter(
            is_active=True,
            status='published'
        ).order_by('-total_views', '-created_at')[:limit]
    
    def get_trending_products(self, limit=6):
        """Get trending products based on recent views"""
        cache_key = f"trending_products"
        trending = cache.get(cache_key)
        
        if trending is None:
            trending = Product.objects.filter(
                is_active=True,
                status='published'
            ).annotate(
                recent_views=Count('views', filter=Q(views__viewed_at__gte=timezone.now()-timezone.timedelta(days=7)))
            ).order_by('-recent_views', '-total_views')[:limit]
            
            cache.set(cache_key, trending, 1800)  # Cache for 30 minutes
        
        return trending