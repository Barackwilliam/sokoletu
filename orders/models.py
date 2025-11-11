from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


User = get_user_model()

class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_('user')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('cart')
        verbose_name_plural = _('carts')

    def __str__(self):
        return f"Cart for {self.user.email}"


    @property
    def get_free_shipping_remaining(self):
        """Calculate remaining amount for free shipping"""
        free_shipping_threshold = Decimal('50000')
        if self.subtotal >= free_shipping_threshold:
            return Decimal('0')
        return free_shipping_threshold - self.subtotal

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def tax_amount(self):
        return self.subtotal * Decimal('0.18')  # 18% VAT

    @property
    def shipping_cost(self):
        # Free shipping for orders above 50,000 TSh
        if self.subtotal > Decimal('50000'):
            return Decimal('0')
        return Decimal('5000')  # 5,000 TSh standard shipping

    @property
    def total(self):
        return self.subtotal + self.tax_amount + self.shipping_cost

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('cart')
    )
    product = models.ForeignKey(
        'market.Product',
        on_delete=models.CASCADE,
        verbose_name=_('product')
    )
    quantity = models.PositiveIntegerField(
        _('quantity'),
        default=1,
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField(_('added at'), auto_now_add=True)

    class Meta:
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.product.price * self.quantity

    @property
    def is_available(self):
        return self.product.is_in_stock and self.quantity <= self.product.stock_quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('confirmed', _('Confirmed')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
        ('refunded', _('Refunded')),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
    )

    PAYMENT_METHOD_CHOICES = (
        ('mpesa', _('M-Pesa')),
        ('tigopesa', _('Tigo Pesa')),
        ('airtelmoney', _('Airtel Money')),
        ('selcom', _('Selcom')),
        ('card', _('Credit Card')),
        ('cash', _('Cash on Delivery')),
    )

    # Order Information
    order_number = models.CharField(_('order number'), max_length=20, unique=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('user')
    )
    
    # Status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_status = models.CharField(
        _('payment status'),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_method = models.CharField(
        _('payment method'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )
    
    # Pricing
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=12,
        decimal_places=2
    )
    tax_amount = models.DecimalField(
        _('tax amount'),
        max_digits=12,
        decimal_places=2
    )
    shipping_cost = models.DecimalField(
        _('shipping cost'),
        max_digits=12,
        decimal_places=2
    )
    total = models.DecimalField(
        _('total'),
        max_digits=12,
        decimal_places=2
    )
    
    # Customer Information
    shipping_name = models.CharField(_('shipping name'), max_length=100)
    shipping_phone = models.CharField(_('shipping phone'), max_length=15)
    shipping_email = models.EmailField(_('shipping email'))
    shipping_address = models.TextField(_('shipping address'))
    shipping_region = models.CharField(_('shipping region'), max_length=50)
    shipping_district = models.CharField(_('shipping district'), max_length=50)
    shipping_ward = models.CharField(_('shipping ward'), max_length=50, blank=True)
    
    # Payment Information
    payment_reference = models.CharField(
        _('payment reference'),
        max_length=100,
        blank=True
    )
    payment_date = models.DateTimeField(_('payment date'), blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    confirmed_at = models.DateTimeField(_('confirmed at'), blank=True, null=True)
    shipped_at = models.DateTimeField(_('shipped at'), blank=True, null=True)
    delivered_at = models.DateTimeField(_('delivered at'), blank=True, null=True)

    class Meta:
        verbose_name = _('order')
        verbose_name_plural = _('orders')
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            import uuid
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def is_paid(self):
        return self.payment_status == 'paid'

    @property
    def can_be_cancelled(self):
        return self.status in ['pending', 'confirmed']

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('order')
    )
    product = models.ForeignKey(
        'market.Product',
        on_delete=models.PROTECT,
        verbose_name=_('product')
    )
    product_name = models.CharField(_('product name'), max_length=200)
    product_price = models.DecimalField(
        _('product price'),
        max_digits=10,
        decimal_places=2
    )
    quantity = models.PositiveIntegerField(_('quantity'))
    total_price = models.DecimalField(
        _('total price'),
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        verbose_name = _('order item')
        verbose_name_plural = _('order items')

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    def save(self, *args, **kwargs):
        if not self.product_name:
            self.product_name = self.product.name
        if not self.product_price:
            self.product_price = self.product.price
        self.total_price = self.product_price * self.quantity
        super().save(*args, **kwargs)