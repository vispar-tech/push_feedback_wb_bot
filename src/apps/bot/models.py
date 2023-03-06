from django.db import models


class TelegramUser(models.Model):
    username = models.CharField('Имя пользователя', max_length=200, null=True, blank=True)
    user_id = models.CharField('ИД', max_length=30, unique=True, default=None)
    phone_number = models.CharField('Номер телефона', max_length=50, blank=True)
    unactive = models.BooleanField('Пользователь заблокировал бота?', default=False)

    class Meta:
        verbose_name = 'Пользователь телеграмма'
        verbose_name_plural = 'Пользователи телеграмма'

    def __str__(self):
        return self.username if self.username is not None else str(self.user_id)
