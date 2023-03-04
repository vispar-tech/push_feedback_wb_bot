from django.db import models
from django.utils.translation import gettext as _


class TelegramUser(models.Model):
    username = models.CharField(_('Username'), max_length=200, null=True, blank=True)
    user_id = models.CharField(_('ID'), max_length=30, unique=True, default=None)
    phone_number = models.CharField(_('Phone number'), max_length=50, blank=True)
    unactive = models.BooleanField(_('Does user block bot?'), default=False)

    class Meta:
        verbose_name = _('Telegram User')
        verbose_name_plural = _('Telegram Users')

    def __str__(self):
        return self.username if self.username is not None else str(self.user_id)
