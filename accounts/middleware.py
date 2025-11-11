from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages

class ProfileCompletionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of URLs that don't require profile completion
        exempt_urls = [
            reverse('accounts:logout'),
            reverse('accounts:profile'),
            reverse('admin:index'),
            reverse('admin:login'),
        ]
        
        # Check if user is authenticated and profile completion is required
        if (request.user.is_authenticated and 
            not request.user.has_completed_profile and 
            request.path not in exempt_urls):
            
            # Allow access to static files and media
            if not any([
                request.path.startswith('/static/'),
                request.path.startswith('/media/'),
                request.path.startswith('/admin/'),
                '/password-reset/' in request.path,
            ]):
                messages.warning(
                    request, 
                    _('Please complete your profile to access all features.')
                )
                return redirect('accounts:profile')
        
        response = self.get_response(request)
        return response