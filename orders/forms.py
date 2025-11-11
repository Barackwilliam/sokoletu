from django import forms
from django.utils.translation import gettext_lazy as _

class CheckoutForm(forms.Form):
    # Shipping Information
    shipping_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Full Name')
        })
    )
    shipping_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Phone Number')
        })
    )
    shipping_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Email Address')
        })
    )
    shipping_region = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Region')
        })
    )
    shipping_district = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('District')
        })
    )
    shipping_ward = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ward (Optional)')
        })
    )
    shipping_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Full Street Address')
        })
    )
    
    # Payment Method
    payment_method = forms.ChoiceField(
        choices=[
            ('mpesa', _('M-Pesa')),
            ('tigopesa', _('Tigo Pesa')),
            ('airtelmoney', _('Airtel Money')),
            ('selcom', _('Selcom')),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    # Terms and Conditions
    accept_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class CartItemForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1'
        })
    )