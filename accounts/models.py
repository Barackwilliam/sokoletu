from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import UserManager


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('buyer', _('Buyer')),
        ('seller', _('Seller')),
        ('both', _('Buyer & Seller')),
        ('admin', _('Administrator')),
    )
    
    username = None
    email = models.EmailField(_('email address'), unique=True)
    user_type = models.CharField(_('user type'), max_length=10, choices=USER_TYPE_CHOICES, default='buyer')
    phone_number = models.CharField(_('phone number'), max_length=15, blank=True)
    
    # ✅ Uploadcare UUID-based image
    profile_picture = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('profile picture'))
    
    date_of_birth = models.DateField(_('date of birth'), blank=True, null=True)
    is_email_verified = models.BooleanField(_('email verified'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    # ✅ IMAGE HELPERS
    def get_image_url(self):
        """Return proper Uploadcare image URL."""
        if not self.profile_picture:
            return None

        image_str = str(self.profile_picture).strip()

        # Kama ni full link sahihi
        if image_str.startswith('http'):
            return image_str

        # Kama ni UUID pekee
        project_domain = "32b2svpniy.ucarecd.net"
        return f"https://{project_domain}/{image_str}/"

    def get_thumbnail_url(self):
        """Return smaller thumbnail version."""
        if not self.profile_picture:
            return None

        image_str = str(self.profile_picture).strip()

        if image_str.startswith('http'):
            return f"{image_str}-/resize/300x300/-/format/auto/-/quality/70/"

        project_domain = "32b2svpniy.ucarecd.net"
        return f"https://{project_domain}/{image_str}/-/resize/300x300/-/format/auto/-/quality/70/"

    @property
    def shop(self):
        try:
            return self.shop_set.first()
        except:
            return None

    @property
    def is_buyer(self):
        return self.user_type in ['buyer', 'both']

    @property
    def is_seller(self):
        return self.user_type in ['seller', 'both']

    @property
    def has_completed_profile(self):
        return all([self.first_name, self.last_name, self.phone_number, self.profile_picture])


class SellerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile',
                                limit_choices_to={'user_type__in': ['seller', 'both']})
    store_name = models.CharField(_('store name'), max_length=100)
    store_description = models.TextField(_('store description'), blank=True)

    # ✅ Uploadcare UUID-based images
    store_logo = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('store logo'))
    store_banner = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('store banner'))

    region = models.CharField(_('region'), max_length=50, blank=True)
    district = models.CharField(_('district'), max_length=50, blank=True)
    ward = models.CharField(_('ward'), max_length=50, blank=True)
    street_address = models.TextField(_('street address'), blank=True)
    business_license = models.CharField(_('business license'), max_length=50, blank=True)
    tax_id = models.CharField(_('tax ID'), max_length=50, blank=True)

    website = models.URLField(_('website'), blank=True)
    facebook = models.URLField(_('facebook'), blank=True)
    instagram = models.URLField(_('instagram'), blank=True)
    twitter = models.URLField(_('twitter'), blank=True)

    is_verified = models.BooleanField(_('verified'), default=False)
    is_active = models.BooleanField(_('active'), default=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('seller profile')
        verbose_name_plural = _('seller profiles')

    def __str__(self):
        return f"{self.store_name} - {self.user.email}"

    # ✅ IMAGE HELPERS
    def get_image_url(self):
        if not self.store_logo:
            return None
        img = str(self.store_logo).strip()
        if img.startswith('http'):
            return img
        return f"https://32b2svpniy.ucarecd.net/{img}/"

    def get_thumbnail_url(self):
        if not self.store_logo:
            return None
        img = str(self.store_logo).strip()
        if img.startswith('http'):
            return f"{img}-/resize/300x300/-/format/auto/-/quality/70/"
        return f"https://32b2svpniy.ucarecd.net/{img}/-/resize/300x300/-/format/auto/-/quality/70/"

    @property
    def has_complete_business_info(self):
        return all([self.store_name, self.region, self.district, self.business_license])
