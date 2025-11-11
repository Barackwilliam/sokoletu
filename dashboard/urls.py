from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [

    # path('', views.seller_dashboard, name='seller_dashboard'),
    # path('analytics/', views.analytics_view, name='analytics_view'),
    # path('chat/<str:room_id>/', views.chat_room, name='chat_room'),
    # path('api/quick-stats/', views.quick_stats, name='quick_stats'),
    # # path('', views.seller_dashboard, name='dashboard'),
    # path('chat/', views.chat_dashboard, name='chat_dashboard'),
    # path('api/analytics/', views.get_analytics_data, name='analytics_api'),


    path('', views.seller_dashboard, name='dashboard'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('chat/', views.chat_dashboard, name='chat_dashboard'),
    path('chat/<str:room_id>/', views.chat_room, name='chat_room'),
    path('api/analytics/', views.get_analytics_data, name='get_analytics_data'),
    path('api/quick-stats/', views.quick_stats, name='quick_stats'),
]