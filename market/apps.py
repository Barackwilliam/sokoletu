from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class MarketConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'market'
    verbose_name = _('Market')