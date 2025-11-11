from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import User, SellerProfile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_email_verified', 'image_preview')

    def image_preview(self, obj):
        if obj.profile_picture:
            return mark_safe(f'<img src="{obj.get_image_url()}" style="max-height: 100px; border-radius:50%;" />')
        return "No Image"
    image_preview.short_description = 'Profile Picture'


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'is_verified', 'logo_preview')

    def logo_preview(self, obj):
        if obj.store_logo:
            return mark_safe(f'<img src="{obj.get_image_url()}" style="max-height: 100px;" />')
        return "No Logo"
    logo_preview.short_description = 'Store Logo'
