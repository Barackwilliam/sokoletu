from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import User, SellerProfile

# Uploadcare Public Key
UPLOADCARE_PUBLIC_KEY = '5ff964c3b9a85a1e2697' 
class UserRegistrationForm(UserCreationForm):
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='buyer'
    )
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'user_type', 'password1', 'password2']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Enter your email')}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('First name')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Last name')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['user_type']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

class UserLoginForm(AuthenticationForm):
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email address')})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': _('Password')})
    )

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'date_of_birth', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            # CHANGED: Using custom widget for Uploadcare
            'profile_picture': forms.TextInput(attrs={
                'class': 'form-control',
                'role': 'uploadcare-uploader',
                'data-public-key': UPLOADCARE_PUBLIC_KEY,
                'data-images-only': 'true',
                'placeholder': _('Select profile picture')
            }),
        }

class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = [
            'store_name', 'store_description', 'store_logo', 'store_banner',
            'region', 'district', 'ward', 'street_address',
            'business_license', 'tax_id', 'website', 'facebook', 'instagram', 'twitter'
        ]
        widgets = {
            'store_name': forms.TextInput(attrs={'class': 'form-control'}),
            'store_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'store_logo': forms.TextInput(attrs={
                'class': 'form-control',
                'role': 'uploadcare-uploader',
                'data-public-key': UPLOADCARE_PUBLIC_KEY,
                'data-images-only': 'true',
                'placeholder': _('Select store logo')
            }),
            'store_banner': forms.TextInput(attrs={
                'class': 'form-control',
                'role': 'uploadcare-uploader',
                'data-public-key': UPLOADCARE_PUBLIC_KEY,
                'data-images-only': 'true',
                'placeholder': _('Select store banner')
            }),
            'region': forms.TextInput(attrs={'class': 'form-control'}),
            'district': forms.TextInput(attrs={'class': 'form-control'}),
            'ward': forms.TextInput(attrs={'class': 'form-control'}),
            'street_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'business_license': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
        }