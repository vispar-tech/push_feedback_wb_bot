from django.apps import AppConfig
from django.utils.translation import gettext as _


class BotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.bot'
    verbose_name = _('Телеграмм БОТ')
