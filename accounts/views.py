from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, SellerProfileForm
from .models import User, SellerProfile

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Registration successful! Welcome to SokoLetu.'))
            return redirect('accounts:profile')
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, _('Welcome back!'))
                next_url = request.GET.get('next', 'core:home')
                return redirect(next_url)
        else:
            messages.error(request, _('Invalid email or password.'))
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, _('You have been logged out successfully.'))
    return redirect('core:home')

@login_required
def profile(request):
    user = request.user
    seller_profile = None
    
    if user.is_seller:
        seller_profile, created = SellerProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, request.FILES, instance=user)
        seller_form = None
        
        if user.is_seller:
            seller_form = SellerProfileForm(request.POST, request.FILES, instance=seller_profile)
            
        if user_form.is_valid():
            user_form.save()
            messages.success(request, _('Profile updated successfully!'))
            
            if user.is_seller and seller_form and seller_form.is_valid():
                seller_form.save()
                messages.success(request, _('Seller profile updated successfully!'))
            
            return redirect('accounts:profile')
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        user_form = UserProfileForm(instance=user)
        seller_form = SellerProfileForm(instance=seller_profile) if user.is_seller else None
    
    context = {
        'user_form': user_form,
        'seller_form': seller_form,
        'seller_profile': seller_profile,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def become_seller(request):
    if request.user.user_type == 'buyer':
        request.user.user_type = 'both'
        request.user.save()
        SellerProfile.objects.get_or_create(user=request.user)
        messages.success(request, _('You are now a seller! Complete your seller profile.'))
    return redirect('accounts:profile')


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

@login_required
def upgrade_to_seller(request):
    """Upgrade user to seller account"""
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        
        if user_type in ['seller', 'both']:
            request.user.user_type = user_type
            request.user.save()
            
            messages.success(
                request, 
                f'Umefanikiwa kuboresha akaunti yako! Sasa unaweza { "kuuza tu" if user_type == "seller" else "nunua na kuuza" } bidhaa kwenye SokoLetu.'
            )
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Tafadhali chagua aina sahihi ya akaunti.')
    
    context = {
        'user': request.user,
    }
    return render(request, 'accounts/upgrade_seller.html', context)