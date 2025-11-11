from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.db import transaction

from .models import Cart, CartItem, Order, OrderItem
from .forms import CheckoutForm, CartItemForm
from .payment_gateways import PaymentGatewayFactory
from market.models import Product

@login_required
def cart_view(request):
    """Display user's shopping cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product', 'product__shop', 'product__category')
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'orders/cart.html', context)

@login_required
@require_POST
def add_to_cart(request, product_id):
    """Add product to cart via AJAX"""
    product = get_object_or_404(Product, id=product_id, is_active=True, status='published')
    
    if not product.is_in_stock:
        return JsonResponse({
            'success': False,
            'message': _('Product is out of stock')
        })
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Check if item already in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        # Check stock availability
        if cart_item.quantity >= product.stock_quantity:
            return JsonResponse({
                'success': False,
                'message': _('Maximum available quantity reached')
            })
        cart_item.quantity += 1
        cart_item.save()
    
    return JsonResponse({
        'success': True,
        'message': _('Product added to cart'),
        'cart_total_items': cart.total_items
    })

@login_required
@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    form = CartItemForm(request.POST, instance=cart_item)
    
    if form.is_valid():
        quantity = form.cleaned_data['quantity']
        
        # Check stock availability
        if quantity > cart_item.product.stock_quantity:
            messages.error(request, _('Requested quantity exceeds available stock'))
        else:
            form.save()
            messages.success(request, _('Cart updated successfully'))
    
    return redirect('orders:cart')

@login_required
@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, _('Item removed from cart'))
    return redirect('orders:cart')

@login_required
def checkout(request):
    """Checkout process"""
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('product')
    
    if cart.total_items == 0:
        messages.warning(request, _('Your cart is empty'))
        return redirect('orders:cart')
    
    # Check stock availability
    for item in cart_items:
        if not item.is_available:
            messages.error(request, 
                _('Some items in your cart are no longer available. Please review your cart.'))
            return redirect('orders:cart')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            return process_checkout(request, cart, form.cleaned_data)
    else:
        # Pre-fill form with user data
        initial_data = {
            'shipping_name': request.user.get_full_name(),
            'shipping_email': request.user.email,
            'shipping_phone': request.user.phone_number or '',
        }
        form = CheckoutForm(initial=initial_data)
    
    context = {
        'cart': cart,
        'form': form,
    }
    return render(request, 'orders/checkout.html', context)

@transaction.atomic
def process_checkout(request, cart, form_data):
    """Process checkout and create order"""
    try:
        # Create order
        order = Order.objects.create(
            user=request.user,
            subtotal=cart.subtotal,
            tax_amount=cart.tax_amount,
            shipping_cost=cart.shipping_cost,
            total=cart.total,
            payment_method=form_data['payment_method'],
            shipping_name=form_data['shipping_name'],
            shipping_phone=form_data['shipping_phone'],
            shipping_email=form_data['shipping_email'],
            shipping_address=form_data['shipping_address'],
            shipping_region=form_data['shipping_region'],
            shipping_district=form_data['shipping_district'],
            shipping_ward=form_data.get('shipping_ward', ''),
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_price=cart_item.product.price,
                quantity=cart_item.quantity,
                total_price=cart_item.total_price
            )
            
            # Update product stock
            cart_item.product.stock_quantity -= cart_item.quantity
            cart_item.product.save()
        
        # Process payment
        payment_gateway = PaymentGatewayFactory.get_gateway(form_data['payment_method'])
        payment_result = payment_gateway.process_payment(
            amount=float(order.total),
            phone_number=form_data['shipping_phone'],
            order_reference=order.order_number
        )
        
        if payment_result['success']:
            order.payment_status = 'paid'
            order.payment_reference = payment_result['transaction_id']
            order.status = 'confirmed'
            order.confirmed_at = timezone.now()
            order.save()
            
            # Clear cart
            cart.items.all().delete()
            
            messages.success(request, _('Order placed successfully!'))
            return redirect('orders:order_success', order_id=order.id)
        else:
            order.payment_status = 'failed'
            order.save()
            
            # Restore product stock
            for order_item in order.items.all():
                order_item.product.stock_quantity += order_item.quantity
                order_item.product.save()
            
            messages.error(request, payment_result['error'])
            return redirect('orders:checkout')
            
    except Exception as e:
        messages.error(request, _('An error occurred during checkout. Please try again.'))
        return redirect('orders:checkout')

@login_required
def order_success(request, order_id):
    """Order success page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'orders/order_success.html', context)

@login_required
def order_failed(request, order_id):
    """Order failed page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    context = {
        'order': order,
    }
    return render(request, 'orders/order_failed.html', context)

# AJAX view for cart count
@login_required
def get_cart_count(request):
    """Get cart item count for navbar"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    return JsonResponse({'count': cart.total_items})




from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order, OrderItem

@login_required
def seller_orders(request):
    """View orders for seller's products"""
    if not request.user.is_seller:
        messages.error(request, 'Unahtaji kuwa muuzaji kuona maagizo!')
        return redirect('accounts:upgrade_seller')
    
    try:
        # FIXED: using seller instead of user.shop
        shop = Shop.objects.get(seller=request.user)
        # Get orders that contain products from this seller's shop
        order_items = OrderItem.objects.filter(product__shop=shop).select_related('order', 'product')
        
        # Get unique orders
        orders = Order.objects.filter(
            items__product__shop=shop
        ).distinct().order_by('-created_at')
        
    except Shop.DoesNotExist:
        messages.error(request, 'Unahtaji kuwa na duka kwanza!')
        return redirect('market:create_shop')
    
    context = {
        'orders': orders,
        'order_items': order_items,
    }
    return render(request, 'orders/seller_orders.html', context)