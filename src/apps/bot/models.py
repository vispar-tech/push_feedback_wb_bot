from django.db import models
from django.utils.translation import gettext as _


class TelegramUser(models.Model):
    username = models.CharField(_('Имя пользователя'), max_length=200, null=True, blank=True)
    user_id = models.CharField(_('ИД'), max_length=30, unique=True, default=None)
    phone_number = models.CharField(_('Номер телефона'), max_length=50, blank=True)
    unactive = models.BooleanField(_('Пользователь заблокировал бота?'), default=False)

    class Meta:
        verbose_name = _('Пользователь телеграмма')
        verbose_name_plural = _('Пользователи телеграмма')

    def __str__(self):
        return self.username if self.username is not None else str(self.user_id)
