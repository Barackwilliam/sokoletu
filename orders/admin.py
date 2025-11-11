from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Cart, CartItem, Order, OrderItem

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_items', 'subtotal', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'total_price']
    list_filter = ['added_at']
    search_fields = ['cart__user__email', 'product__name']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_price', 'quantity', 'total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'status', 'payment_status', 
        'payment_method', 'total', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__email', 'shipping_name']
    readonly_fields = [
        'order_number', 'created_at', 'updated_at', 
        'confirmed_at', 'shipped_at', 'delivered_at'
    ]
    inlines = [OrderItemInline]
    fieldsets = (
        (_('Order Information'), {
            'fields': ('order_number', 'user', 'status')
        }),
        (_('Payment Information'), {
            'fields': ('payment_status', 'payment_method', 'payment_reference', 'payment_date')
        }),
        (_('Pricing'), {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'total')
        }),
        (_('Shipping Information'), {
            'fields': (
                'shipping_name', 'shipping_phone', 'shipping_email',
                'shipping_address', 'shipping_region', 'shipping_district', 'shipping_ward'
            )
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'shipped_at', 'delivered_at')
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'product_price', 'total_price']
    list_filter = ['order__status']
    search_fields = ['order__order_number', 'product_name']
    readonly_fields = ['product_name', 'product_price', 'total_price']