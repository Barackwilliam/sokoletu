from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Category, Shop, Product, ProductImage, ProductView, SponsoredRequest, SearchHistory,HomeSlider
from .forms import CategoryAdminForm, ShopAdminForm, ProductImageForm,HomeSliderForm
# Uploadcare Public Key - Replace with your actual key
UPLOADCARE_PUBLIC_KEY = '5ff964c3b9a85a1e2697'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ['name', 'slug', 'parent', 'is_active', 'image_preview', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_active', 'parent']
    readonly_fields = ['image_preview_large']
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'image':
            formfield.widget.attrs.update({
                'role': 'uploadcare-uploader',
                'data-public-key': UPLOADCARE_PUBLIC_KEY,
                'data-images-only': 'true',
            })
        return formfield

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.get_image_preview_url()}" style="max-height: 50px;" />')
        return "No Image"
    image_preview.short_description = 'Image'
    
    def image_preview_large(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.get_image_url()}" style="max-height: 200px;" />')
        return "No Image"
    image_preview_large.short_description = 'Image Preview'

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    form = ShopAdminForm
    list_display = ['name', 'slug', 'seller', 'is_verified', 'is_active', 'logo_preview', 'created_at']
    search_fields = ['name', 'slug', 'seller__username']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['is_verified', 'is_active', 'rating']
    readonly_fields = ['logo_preview_large', 'banner_preview_large']
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name in ['logo', 'banner']:
            formfield.widget.attrs.update({
                'role': 'uploadcare-uploader',
                'data-public-key': UPLOADCARE_PUBLIC_KEY,
                'data-images-only': 'true',
            })
        return formfield

    def logo_preview(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.get_logo_url()}" style="max-height: 50px;" />')
        return "No Logo"
    logo_preview.short_description = 'Logo'
    
    def logo_preview_large(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.get_logo_url()}" style="max-height: 100px;" />')
        return "No Logo"
    logo_preview_large.short_description = 'Logo Preview'
    
    def banner_preview_large(self, obj):
        if obj.banner:
            return mark_safe(f'<img src="{obj.get_banner_url()}" style="max-height: 200px;" />')
        return "No Banner"
    banner_preview_large.short_description = 'Banner Preview'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'category', 'shop', 'price', 'stock_quantity', 'is_active', 'is_featured', 'status']
    search_fields = ['name', 'slug', 'category__name', 'shop__name']
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ['status', 'category', 'shop', 'is_active', 'is_featured']
    actions = ['make_published', 'make_draft']

    def make_published(self, request, queryset):
        queryset.update(status='published')
    make_published.short_description = "Mark selected products as published"

    def make_draft(self, request, queryset):
        queryset.update(status='draft')
    make_draft.short_description = "Mark selected products as draft"

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    form = ProductImageForm
    list_display = ['product', 'is_primary', 'order', 'image_preview', 'created_at']
    search_fields = ['product__name']
    list_filter = ['is_primary']
    readonly_fields = ['image_preview_large']
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'image':
            formfield.widget.attrs.update({
                'role': 'uploadcare-uploader',
                'data-public-key': UPLOADCARE_PUBLIC_KEY,
                'data-images-only': 'true',
                'data-preview-step': 'true',
            })
        return formfield

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.get_thumbnail_url()}" style="max-height: 50px;" />')
        return "No Image"
    image_preview.short_description = 'Image'
    
    def image_preview_large(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.get_image_url()}" style="max-height: 300px;" />')
        return "No Image"
    image_preview_large.short_description = 'Image Preview'

@admin.register(ProductView)
class ProductViewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']

@admin.register(SponsoredRequest)
class SponsoredRequestAdmin(admin.ModelAdmin):
    list_display = ['product', 'seller', 'title', 'status', 'start_date', 'end_date', 'created_at']
    search_fields = ['title', 'product__name', 'seller__username']
    list_filter = ['status', 'start_date', 'end_date']
    actions = ['approve_campaign', 'reject_campaign']

    def approve_campaign(self, request, queryset):
        queryset.update(status='approved')
    approve_campaign.short_description = "Approve selected sponsored campaigns"

    def reject_campaign(self, request, queryset):
        queryset.update(status='rejected')
    reject_campaign.short_description = "Reject selected sponsored campaigns"

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'query', 'results_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['query', 'user__email']

@admin.register(HomeSlider)
class HomeSliderAdmin(admin.ModelAdmin):
    form = HomeSliderForm
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.get_image_preview_url()}" style="max-height:150px;"/>')
        return "No Image"
    image_preview.short_description = "Image Preview"

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'image':
            formfield.widget.attrs.update({
                'role': 'uploadcare-uploader',
                'data-public-key': UPLOADCARE_PUBLIC_KEY,
                'data-images-only': 'true',
                'data-multiple': 'false',
                'data-tabs': 'file camera url',
                'data-preview-step': 'true',
            })
        return formfield