from django.db import models


class TelegramUser(models.Model):

    username = models.CharField('Имя пользователя', max_length=200, null=True, blank=True)
    user_id = models.CharField('ИД', max_length=30, unique=True, null=False, blank=False)
    phone_number = models.CharField('Номер телефона', max_length=50, blank=True)
    WBToken = models.TextField('WBToken', default=None, null=True)
    temp_token = models.TextField('Временный токен для авторизации', default=None, null=True)
    notification = models.BooleanField('Уведомления включены?', default=True)
    notification_stars = models.SmallIntegerField('Кол-во звезд для уведомлений', null=False, blank=False, default=5)
    unactive = models.BooleanField('Пользователь заблокировал бота?', default=False)

    class Meta:
        verbose_name = 'Пользователь телеграмма'
        verbose_name_plural = 'Пользователи телеграмма'

    def reset_temp_token(self):
        self.temp_token = None
        self.save()

    def set_temp_token(self, token: str):
        self.temp_token = token
        self.save()

    def set_WBToken(self, WBToken: str):
        self.WBToken = WBToken
        self.save()

    def reset_WBToken(self):
        self.WBToken = None
        self.personal_set.all().delete()
        self.save()

    def __str__(self):
        return self.username if self.username is not None else str(self.user_id)
