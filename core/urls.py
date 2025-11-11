from django.urls import path
from . import views

app_name = 'core'  # ADD THIS LINE

urlpatterns = [
    path('', views.home, name='home'),
]