from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class ChatRoom(models.Model):
    ROLE_CHOICES = (
        ('buyer_seller', _('Buyer-Seller Chat')),
        ('support', _('Customer Support')),
        ('admin', _('Admin Chat')),
    )
    
    room_id = models.CharField(_('room ID'), max_length=100, unique=True)
    participants = models.ManyToManyField(
        User, 
        through='ChatParticipant',
        related_name='chat_rooms'
    )
    room_type = models.CharField(
        _('room type'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='buyer_seller'
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('chat room')
        verbose_name_plural = _('chat rooms')

    def __str__(self):
        return f"ChatRoom {self.room_id}"

class ChatParticipant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(_('joined at'), auto_now_add=True)
    is_online = models.BooleanField(_('is online'), default=False)
    last_seen = models.DateTimeField(_('last seen'), auto_now=True)

    class Meta:
        unique_together = ['user', 'room']

class ChatMessage(models.Model):
    MESSAGE_TYPES = (
        ('text', _('Text')),
        ('image', _('Image')),
        ('file', _('File')),
        ('order', _('Order Reference')),
    )
    
    room = models.ForeignKey(
        ChatRoom, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    message_type = models.CharField(
        _('message type'),
        max_length=10,
        choices=MESSAGE_TYPES,
        default='text'
    )
    content = models.TextField(_('content'))
    
    # CHANGED: Using CharField for Uploadcare UUID instead of ImageField
    image = models.CharField(
        _('image'), 
        max_length=255, 
        blank=True, 
        null=True,
        help_text=_('Uploadcare UUID for image files')
    )
    
    # CHANGED: Using CharField for Uploadcare UUID instead of FileField
    file = models.CharField(
        _('file'), 
        max_length=255, 
        blank=True, 
        null=True,
        help_text=_('Uploadcare UUID for file attachments')
    )
    
    # For order references
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='chat_messages'
    )
    
    # Read receipts
    is_read = models.BooleanField(_('is read'), default=False)
    read_by = models.ManyToManyField(
        User, 
        through='MessageReadReceipt',
        related_name='read_messages'
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('chat message')
        verbose_name_plural = _('chat messages')
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.email} in {self.room.room_id}"

    # ADDED: Uploadcare URL methods like the example
    def get_image_url(self):
        """Get optimized image URL for frontend display"""
        if self.image:
            return f"https://ucarecdn.com/{self.image}/-/format/jpg/-/quality/smart/"
        return None
    
    def get_image_preview_url(self):
        """Get preview image URL for chat display"""
        if self.image:
            return f"https://ucarecdn.com/{self.image}/-/resize/300x300/-/format/jpg/-/quality/smart/"
        return None
    
    def get_file_url(self):
        """Get file download URL"""
        if self.file:
            return f"https://ucarecdn.com/{self.file}/"
        return None
    
    def get_og_image_url(self):
        """Get Open Graph optimized image URL"""
        if self.image:
            return f"https://ucarecdn.com/{self.image}/-/resize/1200x630/-/format/auto/"
        return None

class MessageReadReceipt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE)
    read_at = models.DateTimeField(_('read at'), auto_now_add=True)

    class Meta:
        unique_together = ['user', 'message']

class SellerAnalytics(models.Model):
    seller = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='analytics',
        limit_choices_to={'user_type__in': ['seller', 'both']}
    )
    
    # Sales Metrics
    total_sales = models.DecimalField(
        _('total sales'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total_orders = models.PositiveIntegerField(_('total orders'), default=0)
    monthly_revenue = models.DecimalField(
        _('monthly revenue'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Product Metrics
    total_products = models.PositiveIntegerField(_('total products'), default=0)
    total_views = models.PositiveIntegerField(_('total views'), default=0)
    
    # Customer Metrics
    total_customers = models.PositiveIntegerField(_('total customers'), default=0)
    repeat_customers = models.PositiveIntegerField(_('repeat customers'), default=0)
    
    # Rating
    average_rating = models.DecimalField(
        _('average rating'),
        max_digits=3,
        decimal_places=2,
        default=0
    )
    
    # Timestamps
    last_updated = models.DateTimeField(_('last updated'), auto_now=True)

    class Meta:
        verbose_name = _('seller analytics')
        verbose_name_plural = _('seller analytics')

    def __str__(self):
        return f"Analytics for {self.seller.email}"

class DailyStats(models.Model):
    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='daily_stats'
    )
    date = models.DateField(_('date'))
    
    # Daily metrics
    sales = models.DecimalField(
        _('sales'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    orders = models.PositiveIntegerField(_('orders'), default=0)
    views = models.PositiveIntegerField(_('views'), default=0)
    new_customers = models.PositiveIntegerField(_('new customers'), default=0)

    class Meta:
        verbose_name = _('daily stats')
        verbose_name_plural = _('daily stats')
        unique_together = ['seller', 'date']

    def __str__(self):
        return f"Stats for {self.seller.email} on {self.date}"