# models.py
from django.db import models
from django.utils.translation import gettext_lazy as _

class SmallBannerAd(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    cta_text = models.CharField(max_length=100)
    cta_url = models.URLField()
    style = models.CharField(max_length=50, default='default-style')  # e.g., 'mobile-money', 'tigo'
    badge_icon = models.CharField(max_length=50, default='fas fa-ad')
    badge_text = models.CharField(max_length=50, default=_("OFFICIAL PARTNER"))
    decoration_text = models.CharField(max_length=50, blank=True, null=True)  # e.g., "M-PESA", "VIP"
    priority = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['priority']
