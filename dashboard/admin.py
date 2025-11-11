from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (
    ChatRoom, ChatParticipant, ChatMessage, 
    MessageReadReceipt, SellerAnalytics, DailyStats
)

# Uploadcare Public Key
UPLOADCARE_PUBLIC_KEY = '5ff964c3b9a85a1e2697'

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'room_type', 'created_at', 'updated_at')
    list_filter = ('room_type', 'created_at')
    search_fields = ('room_id',)
    filter_horizontal = ('participants',)

@admin.register(ChatParticipant)
class ChatParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'joined_at', 'is_online', 'last_seen')
    list_filter = ('is_online', 'joined_at')
    search_fields = ('user__email', 'room__room_id')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'sender', 'message_type', 'is_read', 'created_at', 'image_preview')
    list_filter = ('message_type', 'is_read', 'created_at')
    search_fields = ('content', 'sender__email', 'room__room_id')
    readonly_fields = ('created_at', 'image_preview_large')
    filter_horizontal = ('read_by',)  # ADDED: For ManyToManyField
    
    # ADDED: Image preview in list view
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.get_image_preview_url()}" style="max-height: 50px;" />')
        return "No Image"
    image_preview.short_description = 'Image'
    
    # ADDED: Large image preview in detail view
    def image_preview_large(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.get_image_url()}" style="max-height: 300px;" />')
        return "No Image"
    image_preview_large.short_description = 'Image Preview'
    
    # ADDED: Uploadcare widget configuration
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
        elif db_field.name == 'file':
            formfield.widget.attrs.update({
                'role': 'uploadcare-uploader',
                'data-public-key': UPLOADCARE_PUBLIC_KEY,
                'data-multiple': 'false',
                'data-tabs': 'file url',
                'data-input-accept-types': '.pdf,.doc,.docx,.txt',
            })
        return formfield

    # FIXED: Removed 'read_by' from fieldsets since it's ManyToManyField
    fieldsets = (
        ('Basic Information', {
            'fields': ('room', 'sender', 'message_type', 'content')
        }),
        ('Media Files', {
            'fields': ('image', 'image_preview_large', 'file'),
            'classes': ('collapse',)
        }),
        ('Order Reference', {
            'fields': ('order',),
            'classes': ('collapse',)
        }),
        ('Read Status', {
            'fields': ('is_read',),  # REMOVED: 'read_by' from here
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(MessageReadReceipt)
class MessageReadReceiptAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('user__email', 'message__content')

@admin.register(SellerAnalytics)
class SellerAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('seller', 'total_sales', 'total_orders', 'monthly_revenue', 'last_updated')
    list_filter = ('last_updated',)
    search_fields = ('seller__email',)
    readonly_fields = ('last_updated',)

@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ('seller', 'date', 'sales', 'orders', 'views', 'new_customers')
    list_filter = ('date',)
    search_fields = ('seller__email',)
    date_hierarchy = 'date'