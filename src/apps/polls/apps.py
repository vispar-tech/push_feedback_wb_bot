from django.apps import AppConfig
from django.utils.translation import gettext as _


class PollsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.polls'
    verbose_name = _('Опции')
