from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (
    ChatRoom, ChatParticipant, ChatMessage, 
    MessageReadReceipt, SellerAnalytics, DailyStats
)

# Uploadcare Public Key
UPLOADCARE_PUBLIC_KEY = '07d87a25986725d72cf5'


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('room_id', 'room_type', 'created_at', 'updated_at')
    list_filter = ('room_type', 'created_at')
    search_fields = ('room_id',)
    # REMOVED: filter_horizontal = ('participants',)  # participants uses through model


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

    # REMOVED: filter_horizontal = ('read_by',)  # read_by uses through model

    # Image preview inside list
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.get_image_preview_url()}" style="max-height: 50px;" />')
        return "No Image"
    image_preview.short_description = 'Image'

    # Large preview
    def image_preview_large(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.get_image_url()}" style="max-height: 300px;" />')
        return "No Image"
    image_preview_large.short_description = 'Image Preview'

    # Uploadcare widget config
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
            'fields': ('is_read',),  # NOT including read_by
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
