from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Count, Q
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.core.cache import cache
from django.utils import timezone
from django.utils.functional import cached_property
from .utils import apply_watermark

import uuid

User = get_user_model()

class Category(models.Model):
    name = models.CharField(_('name'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    
    # CHANGED: Using Uploadcare UUID instead of ImageField
    image = models.CharField(
        _('image'), 
        max_length=255, 
        blank=True, 
        null=True,
        help_text=_('Uploadcare UUID for category image')
    )
    
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children',
        verbose_name=_('parent category')
    )
    is_active = models.BooleanField(_('active'), default=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        indexes = [
            models.Index(fields=['slug', 'is_active']),
            models.Index(fields=['parent', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('market:category_products', kwargs={'slug': self.slug})

    # ADDED: Uploadcare URL methods
    def get_image_url(self):
        """Get optimized image URL for frontend display"""
        if self.image:
            return f"https://ucarecdn.com/{self.image}/-/format/jpg/-/quality/smart/"
        return None
    
    def get_image_preview_url(self):
        """Get preview image URL for category listing"""
        if self.image:
            return f"https://ucarecdn.com/{self.image}/-/resize/300x300/-/format/jpg/-/quality/smart/"
        return None
    
    def get_og_image_url(self):
        """Get Open Graph optimized image URL"""
        if self.image:
            return f"https://ucarecdn.com/{self.image}/-/resize/1200x630/-/format/auto/"
        return None

    @cached_property
    def product_count(self):
        return self.products.filter(status='published', is_active=True).count()

class Shop(models.Model):
    seller = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='shop',
        limit_choices_to={'user_type__in': ['seller', 'both']},
        verbose_name=_('seller')
    )
    name = models.CharField(_('shop name'), max_length=100)
    slug = models.SlugField(_('slug'), max_length=100, unique=True)
    description = models.TextField(_('description'), blank=True)
    
    # CHANGED: Using Uploadcare UUID for logo
    logo = models.CharField(
        _('logo'), 
        max_length=255, 
        blank=True, 
        null=True,
        help_text=_('Uploadcare UUID for shop logo')
    )
    
    # CHANGED: Using Uploadcare UUID for banner
    banner = models.CharField(
        _('banner'), 
        max_length=255, 
        blank=True, 
        null=True,
        help_text=_('Uploadcare UUID for shop banner')
    )
    
    # Contact Information
    phone = models.CharField(_('phone number'), max_length=15, blank=True)
    email = models.EmailField(_('contact email'), blank=True)
    
    # Location
    region = models.CharField(_('region'), max_length=50, blank=True)
    district = models.CharField(_('district'), max_length=50, blank=True)
    ward = models.CharField(_('ward'), max_length=50, blank=True)
    street_address = models.TextField(_('street address'), blank=True)
    
    # Social Media
    website = models.URLField(_('website'), blank=True)
    facebook = models.URLField(_('facebook'), blank=True)
    instagram = models.URLField(_('instagram'), blank=True)
    
    # Shop Status
    is_verified = models.BooleanField(_('verified'), default=False)
    is_active = models.BooleanField(_('active'), default=True)
    rating = models.DecimalField(_('rating'), max_digits=3, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    
    def save(self, *args, **kwargs):
        if self.banner:
            watermarked = apply_watermark(self.banner)
            self.image.save(self.banner.name, watermarked, save=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('shop')
        verbose_name_plural = _('shops')
        indexes = [
            models.Index(fields=['slug', 'is_active']),
            models.Index(fields=['is_verified', 'is_active']),
            models.Index(fields=['rating', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('market:shop_detail', kwargs={'slug': self.slug})

    # ADDED: Uploadcare URL methods for Shop
    def get_logo_url(self):
        """Get optimized logo URL"""
        if self.logo:
            return f"https://ucarecdn.com/{self.logo}/-/resize/100x100/-/format/jpg/-/quality/smart/"
        return None
    
    def get_banner_url(self):
        """Get optimized banner URL"""
        if self.banner:
            return f"https://ucarecdn.com/{self.banner}/-/resize/1200x400/-/format/jpg/-/quality/smart/"
        return None
    
    def get_banner_preview_url(self):
        """Get preview banner URL"""
        if self.banner:
            return f"https://ucarecdn.com/{self.banner}/-/resize/400x150/-/format/jpg/-/quality/smart/"
        return None

    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()

class Product(models.Model):
    CONDITION_CHOICES = (
        ('new', _('New')),
        ('used', _('Used')),
        ('refurbished', _('Refurbished')),
    )
    
    STATUS_CHOICES = (
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('out_of_stock', _('Out of Stock')),
        ('discontinued', _('Discontinued')),
    )

    # Basic Information
    name = models.CharField(_('product name'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200, unique=True)
    description = models.TextField(_('description'))
    short_description = models.TextField(_('short description'), max_length=500, blank=True)
    
    # Categorization
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products',
        verbose_name=_('category')
    )
    shop = models.ForeignKey(
        Shop,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('shop')
    )
    
    # Pricing
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(
        _('compare price'), 
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        help_text=_('Original price for showing discount')
    )
    cost_price = models.DecimalField(
        _('cost price'), 
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True
    )
    
    # Inventory
    sku = models.CharField(_('SKU'), max_length=50, unique=True, blank=True)
    stock_quantity = models.PositiveIntegerField(_('stock quantity'), default=0)
    low_stock_threshold = models.PositiveIntegerField(_('low stock threshold'), default=5)
    
    # Product Details
    condition = models.CharField(
        _('condition'), 
        max_length=20, 
        choices=CONDITION_CHOICES, 
        default='new'
    )
    brand = models.CharField(_('brand'), max_length=100, blank=True)
    weight = models.DecimalField(
        _('weight (kg)'), 
        max_digits=8, 
        decimal_places=3, 
        blank=True, 
        null=True
    )
    dimensions = models.CharField(_('dimensions'), max_length=100, blank=True)

    search_vector = SearchVectorField(null=True, blank=True)
    total_views = models.IntegerField(default=0)
    last_viewed = models.DateTimeField(auto_now=True)
    search_rank = models.FloatField(default=0.0)
    
    # Specifications (JSON field for flexible specs)
    specifications = models.JSONField(_('specifications'), default=dict, blank=True)
    
    # Status
    status = models.CharField(
        _('status'), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft'
    )
    is_active = models.BooleanField(_('active'), default=True)
    is_featured = models.BooleanField(_('featured'), default=False)
    is_sponsored = models.BooleanField(_('sponsored'), default=False)
    
    # SEO
    meta_title = models.CharField(_('meta title'), max_length=200, blank=True)
    meta_description = models.TextField(_('meta description'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    published_at = models.DateTimeField(_('published at'), blank=True, null=True)

    class Meta:
        verbose_name = _('product')
        verbose_name_plural = _('products')
        indexes = [
            GinIndex(fields=['search_vector']),
            models.Index(fields=['total_views', 'created_at']),
            models.Index(fields=['search_rank', 'is_active']),
            models.Index(fields=['slug', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['shop', 'is_active']),
            models.Index(fields=['price', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
            models.Index(fields=['is_sponsored', 'is_active']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['created_at', 'is_active']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        
        if not self.sku:
            self.sku = f"SKU-{uuid.uuid4().hex[:8].upper()}"
            
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
            
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('market:product_detail', kwargs={'slug': self.slug})

    def increment_views(self):
        """Increment view count with caching for performance"""
        cache_key = f"product_views_{self.id}"
        current_views = cache.get(cache_key, 0)
        current_views += 1
        
        if current_views >= 5:  # Update database every 5 views
            self.total_views += current_views
            self.save()
            cache.delete(cache_key)
        else:
            cache.set(cache_key, current_views, 3600)  # Cache for 1 hour
    
    def get_similar_products(self, limit=8):
        """Get similar products based on category and tags"""
        similar = Product.objects.filter(
            category=self.category,
            is_active=True,
            status='published'
        ).exclude(id=self.id).select_related('shop').prefetch_related('images')[:limit]
        
        return similar

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0 and self.status == 'published'

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def discount_percentage(self):
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0

    @property
    def view_count(self):
        return self.views.count()


     # ADD THESE PROPERTIES FOR SIMPLE TEMPLATE ACCESS
    @property
    def product_image(self):
        """Simple image URL like in your example - works with template directly"""
        if self.images.exists():
            main_img = self.images.filter(is_primary=True).first()
            if not main_img:
                main_img = self.images.first()
            return main_img.get_image_url() if main_img else None
        return None
    
    @property 
    def main_image_url(self):
        """Alias for product_image for consistency"""
        return self.product_image
    
    @property
    def thumbnail_url(self):
        """Get thumbnail URL for product listings"""
        if self.images.exists():
            main_img = self.images.filter(is_primary=True).first()
            if not main_img:
                main_img = self.images.first()
            return main_img.get_thumbnail_url() if main_img else None
        return None



class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name=_('product')
    )
    
    # CHANGED: Using Uploadcare UUID instead of ImageField
    image = models.CharField(
        _('image'), 
        max_length=255,
        help_text=_('Uploadcare UUID for product image')
    )
    
    alt_text = models.CharField(_('alt text'), max_length=200, blank=True)
    is_primary = models.BooleanField(_('primary image'), default=False)
    order = models.PositiveIntegerField(_('order'), default=0)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    
    def save(self, *args, **kwargs):
        if self.image:
            watermarked = apply_watermark(self.image)
            self.image.save(self.image.name, watermarked, save=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('product image')
        verbose_name_plural = _('product images')
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['product', 'is_primary']),
        ]

    def __str__(self):
        return f"Image for {self.product.name}"

    def get_image_url(self):
        """Return full image URL whether it's from Uploadcare subdomain or UUID."""
        if not self.image:
            return None

        image_str = str(self.image).strip()

        # Kama ni full URL (mfano https://32b2svpniy.ucarecd.net/xxxx)
        if image_str.startswith('http'):
            return image_str  # tumia kama ilivyo

        # Kama ni UUID pekee, tengeneza kwa domain yako ya Uploadcare
        # Badilisha '32b2svpniy.ucarecd.net' kwa jina lako halisi la project Uploadcare
        project_domain = "32b2svpniy.ucarecd.net"
        return f"https://{project_domain}/{image_str}/"


    def get_thumbnail_url(self):
        """Return thumbnail URL for product listing."""
        if not self.image:
            return None

        image_str = str(self.image).strip()

        if image_str.startswith('http'):
            # Ongeza transform kwa link kamili
            return f"{image_str}-/resize/300x300/-/format/auto/-/quality/70/"
        
        project_domain = "32b2svpniy.ucarecd.net"
        return f"https://{project_domain}/{image_str}/-/resize/300x300/-/format/auto/-/quality/70/"


    def get_uuid(self):
        """Optional helper if you still need the UUID only."""
        image_str = str(self.image).strip()
        if 'ucarecdn.com' in image_str or 'ucarecd.net' in image_str:
            image_str = image_str.split('/')[-2] if '/' in image_str else image_str
        return image_str




class ProductView(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='views',
        verbose_name=_('product')
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_('user')
    )
    ip_address = models.GenericIPAddressField(_('IP address'))
    user_agent = models.TextField(_('user agent'), blank=True)
    viewed_at = models.DateTimeField(_('viewed at'), auto_now_add=True)

    class Meta:
        verbose_name = _('product view')
        verbose_name_plural = _('product views')
        indexes = [
            models.Index(fields=['product', 'viewed_at']),
            models.Index(fields=['user', 'viewed_at']),
            models.Index(fields=['ip_address', 'viewed_at']),
        ]
        ordering = ['-viewed_at']

    def __str__(self):
        return f"View of {self.product.name} at {self.viewed_at}"

class SponsoredRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('active', _('Active')),
        ('completed', _('Completed')),
    )

    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='sponsored_requests',
        verbose_name=_('product')
    )
    seller = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sponsored_requests',
        verbose_name=_('seller')
    )
    
    # Campaign Details
    title = models.CharField(_('campaign title'), max_length=200)
    description = models.TextField(_('campaign description'), blank=True)
    budget = models.DecimalField(_('budget'), max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField(_('duration (days)'))
    
    # Targeting
    target_categories = models.ManyToManyField(
        Category, 
        blank=True,
        verbose_name=_('target categories')
    )
    target_regions = models.JSONField(_('target regions'), default=list, blank=True)
    
    # Status
    status = models.CharField(
        _('status'), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    
    # Timestamps
    start_date = models.DateTimeField(_('start date'), blank=True, null=True)
    end_date = models.DateTimeField(_('end date'), blank=True, null=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    clicks_count = models.IntegerField(default=0)
    impressions_count = models.IntegerField(default=0)
    ctr = models.FloatField(default=0.0)  # Click-through rate
    
    def record_click(self):
        """Record a click and update CTR"""
        self.clicks_count += 1
        self.calculate_ctr()
        self.save()
    
    def record_impression(self):
        """Record an impression and update CTR"""
        self.impressions_count += 1
        self.calculate_ctr()
        self.save()
    
    def calculate_ctr(self):
        """Calculate click-through rate"""
        if self.impressions_count > 0:
            self.ctr = (self.clicks_count / self.impressions_count) * 100
        else:
            self.ctr = 0.0

    class Meta:
        verbose_name = _('sponsored request')
        verbose_name_plural = _('sponsored requests')
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['product', 'status']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Sponsored: {self.product.name}"

    def save(self, *args, **kwargs):
        if self.status == 'approved' and not self.start_date:
            self.start_date = timezone.now()
            self.end_date = self.start_date + timezone.timedelta(days=self.duration_days)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        if self.status == 'active' and self.end_date:
            return timezone.now() <= self.end_date
        return False

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    query = models.CharField(max_length=255)
    results_count = models.IntegerField(default=0)
    session_key = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session_key', 'created_at']),
        ]
        verbose_name_plural = "Search histories"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.query} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"




UPLOADCARE_PUBLIC_KEY = '5ff964c3b9a85a1e2697'

class HomeSlider(models.Model):
    title = models.CharField(_('Title'), max_length=200, blank=True)
    subtitle = models.CharField(_('Subtitle'), max_length=300, blank=True)
    image = models.CharField(
        _('Image (Uploadcare UUID)'),
        max_length=255,
        help_text=_('Uploadcare UUID for banner image')
    )
    url = models.URLField(_('Link'), blank=True, null=True)
    is_active = models.BooleanField(_('Active'), default=True)
    order = models.PositiveIntegerField(_('Order'), default=0)
    created_at = models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated at'), auto_now=True)

    class Meta:
        verbose_name = _('Home Slider')
        verbose_name_plural = _('Home Sliders')
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title or f"Slider {self.id}"

    def get_image_url(self):
        """Return full image URL, whether it's UUID or full URL."""
        if not self.image:
            return None

        image_str = str(self.image).strip()

        # Kama tayari ni full URL
        if image_str.startswith('http'):
            return image_str

        # Kama ni UUID pekee
        project_domain = "32b2svpniy.ucarecd.net"
        return f"https://{project_domain}/{image_str}/"

    def get_image_preview_url(self):
        """Return preview/slide image URL."""
        if not self.image:
            return None

        image_str = str(self.image).strip()

        if image_str.startswith('http'):
            # Ongeza transform kwa URL kamili
            return f"{image_str}-/resize/1200x500/-/format/jpg/-/quality/smart/"

        project_domain = "32b2svpniy.ucarecd.net"
        return f"https://{project_domain}/{image_str}/-/resize/1200x500/-/format/jpg/-/quality/smart/"
