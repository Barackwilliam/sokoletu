# dashboard/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count, Avg
from django.db import OperationalError
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta

from .models import SellerAnalytics, DailyStats, ChatRoom, ChatMessage
from market.models import Product, Shop
from orders.models import Order, OrderItem


@login_required
def seller_dashboard(request):
    """Main seller dashboard"""
    # FIX: Use proper user check
    if not request.user.is_seller:
        return render(request, 'dashboard/access_denied.html')
    
    try:
        shop = Shop.objects.get(seller=request.user)
    except Shop.DoesNotExist:
        return redirect('market:create_shop')
    
    # Calculate analytics
    analytics = calculate_seller_analytics(request.user)
    
    # Get recent orders
    recent_orders = Order.objects.filter(
        items__product__shop=shop
    ).distinct().select_related('user').prefetch_related('items')[:5]

    # Get popular products
    popular_products = Product.objects.filter(
        shop=shop
    ).annotate(
        total_orders=Count('orderitem')
    ).order_by('-total_orders')[:5]
    
    context = {
        'shop': shop,
        'analytics': analytics,
        'recent_orders': recent_orders,
        'popular_products': popular_products,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def analytics_view(request):
    """Detailed analytics view - FIXED VERSION"""
    if not request.user.is_seller:
        return render(request, 'dashboard/access_denied.html')
    
    try:
        shop = Shop.objects.get(seller=request.user)
    except Shop.DoesNotExist:
        return redirect('market:create_shop')
    
    try:
        analytics = calculate_seller_analytics(request.user)
        chart_data = get_sales_chart_data_safe(request.user)
        
        # Get top performing products
        top_products = Product.objects.filter(
            shop=shop
        ).annotate(
            total_sales=Sum('orderitem__total_price'),
            total_orders=Count('orderitem')
        ).order_by('-total_sales')[:10]
        
        context = {
            'shop': shop,
            'analytics': analytics,
            'chart_data': chart_data,
            'top_products': top_products,
        }
        
        return render(request, 'dashboard/analytics.html', context)
    
    except Exception as e:
        print(f"Error in analytics view: {e}")
        return render(request, 'dashboard/error.html', {
            'error_message': 'Kuna tatizo la kupakia data ya takwimu.'
        })


def get_sales_chart_data_safe(user):
    """Safe version without ambiguous column errors"""
    try:
        shop = Shop.objects.get(seller=user)
        
        # Last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # FIX: Use 'total' field instead of 'total_amount'
        daily_data = Order.objects.filter(
            items__product__shop=shop,
            created_at__gte=thirty_days_ago,
            payment_status='paid'
        ).annotate(
            sales_date=TruncDate('created_at')
        ).values('sales_date').annotate(
            daily_sales=Sum('total'),  # CHANGED: total_amount -> total
            daily_orders=Count('id', distinct=True)
        ).order_by('sales_date')
        
        # Format data for charts
        dates = []
        sales_data = []
        orders_data = []
        
        for day in daily_data:
            dates.append(day['sales_date'].strftime('%Y-%m-%d'))
            sales_data.append(float(day['daily_sales'] or 0))
            orders_data.append(day['daily_orders'])
        
        return {
            'dates': dates,
            'sales': sales_data,
            'orders': orders_data,
        }
        
    except Exception as e:
        print(f"Error in chart data: {e}")
        return {
            'dates': [],
            'sales': [],
            'orders': [],
        }


def calculate_seller_analytics(user):
    """Calculate seller analytics - FIXED VERSION"""
    try:
        shop = Shop.objects.get(seller=user)
    except Shop.DoesNotExist:
        return get_empty_analytics()
    
    # Date ranges for different periods
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # FIX: Use 'total' field instead of 'total_amount'
    all_orders = Order.objects.filter(items__product__shop=shop, payment_status='paid')
    today_orders = all_orders.filter(created_at__date=today)
    week_orders = all_orders.filter(created_at__date__gte=week_ago)
    month_orders = all_orders.filter(created_at__date__gte=month_ago)
    
    # FIX: Use 'total' field for all calculations
    total_sales = all_orders.aggregate(total=Sum('total'))['total'] or 0
    total_orders = all_orders.count()
    monthly_revenue = month_orders.aggregate(total=Sum('total'))['total'] or 0
    
    # Today's performance
    today_sales = today_orders.aggregate(total=Sum('total'))['total'] or 0
    today_orders_count = today_orders.count()
    
    # Weekly performance
    weekly_sales = week_orders.aggregate(total=Sum('total'))['total'] or 0
    
    # Product stats
    total_products = Product.objects.filter(shop=shop).count()
    active_products = Product.objects.filter(shop=shop, is_active=True).count()
    low_stock_products = Product.objects.filter(shop=shop, stock_quantity__lte=10).count()  # FIX: stock_quantity not quantity
    
    # Customer stats
    total_customers = all_orders.values('user').distinct().count()
    new_customers_week = all_orders.filter(
        created_at__date__gte=week_ago
    ).values('user').distinct().count()
    
    return {
        # Overall metrics
        'total_sales': total_sales,
        'total_orders': total_orders,
        'monthly_revenue': monthly_revenue,
        'total_products': total_products,
        'total_customers': total_customers,
        
        # Today's performance
        'today_sales': today_sales,
        'today_orders': today_orders_count,
        
        # Weekly performance
        'weekly_sales': weekly_sales,
        'weekly_orders': week_orders.count(),
        
        # Product status
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        
        # Customer growth
        'new_customers_week': new_customers_week,
        
        # Ratings
        'average_rating': shop.rating or 4.5,
        'total_views': 0,  # Placeholder - add if needed
    }


def get_empty_analytics():
    """Return empty analytics when no shop exists"""
    return {
        'total_sales': 0,
        'total_orders': 0,
        'monthly_revenue': 0,
        'total_products': 0,
        'total_customers': 0,
        'today_sales': 0,
        'today_orders': 0,
        'weekly_sales': 0,
        'weekly_orders': 0,
        'active_products': 0,
        'low_stock_products': 0,
        'new_customers_week': 0,
        'average_rating': 0,
        'total_views': 0,
    }


@login_required
def chat_dashboard(request):
    """Chat dashboard for sellers"""
    if not request.user.is_seller:
        return render(request, 'dashboard/access_denied.html')
    
    # Get seller's chat rooms
    chat_rooms = ChatRoom.objects.filter(
        participants=request.user
    ).prefetch_related('participants', 'messages').distinct()
    
    # Get unread message counts
    for room in chat_rooms:
        room.unread_count = ChatMessage.objects.filter(
            room=room,
            is_read=False
        ).exclude(sender=request.user).count()
    
    context = {
        'chat_rooms': chat_rooms,
    }
    
    return render(request, 'dashboard/chat_dashboard.html', context)


@login_required
def chat_room(request, room_id):
    """Individual chat room"""
    room = get_object_or_404(ChatRoom, room_id=room_id, participants=request.user)
    messages = room.messages.select_related('sender').all()[:100]
    
    # Mark messages as read
    room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    context = {
        'room': room,
        'messages': messages,
    }
    
    return render(request, 'dashboard/chat_room.html', context)


@login_required
def get_analytics_data(request):
    """API endpoint for analytics data"""
    if not request.user.is_seller:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    analytics = calculate_seller_analytics(request.user)
    chart_data = get_sales_chart_data_safe(request.user)
    
    return JsonResponse({
        'analytics': analytics,
        'chart_data': chart_data,
    })


@login_required
def quick_stats(request):
    """API for quick stats (for AJAX updates)"""
    if not request.user.is_seller:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    analytics = calculate_seller_analytics(request.user)
    
    # Return only essential stats
    quick_stats = {
        'today_sales': analytics['today_sales'],
        'today_orders': analytics['today_orders'],
        'weekly_sales': analytics['weekly_sales'],
        'active_products': analytics['active_products'],
    }
    
    return JsonResponse(quick_stats)