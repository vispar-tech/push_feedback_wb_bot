from apps.bot.management.commands.bot import bot
from apps.bot.utils.tools import WBPersonalApiClient
from django.db import models  # noqa
from django.utils import timezone


class Personal(models.Model):

    user = models.ForeignKey('bot.TelegramUser', on_delete=models.CASCADE)
    supplierId = models.CharField('ID продавца', max_length=255, null=False, blank=False)
    oldId = models.IntegerField('Старый ID продавца', null=False, blank=False)
    name = models.CharField('Наименование', max_length=150, null=False, blank=False)
    full_name = models.TextField('Полное наименование', null=False, blank=False)

    class Meta:
        verbose_name = 'Кабинет WB'
        verbose_name_plural = 'Кабинеты WB'

    def get_client(self):
        return WBPersonalApiClient(self.supplierId, self.user.WBToken)

    def get_tracked_articles(self):
        return self.trackedarticle_set.all()

    def __str__(self):
        return self.name


class TrackedArticle(models.Model):

    personal = models.ForeignKey('polls.Personal', on_delete=models.CASCADE, verbose_name='Кабинет')
    nmId = models.CharField('Артикул WB', max_length=20, null=False)
    article = models.CharField('Артикул', max_length=255, null=False, blank=False)
    brand = models.CharField('Бренд', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Отслеживаемый артикул'
        verbose_name_plural = 'Отслеживаемые артикулы'

    def __str__(self):
        return f'{self.nmId} {self.article}'


class Feedback(models.Model):

    wb_id = models.CharField('WB ID', max_length=255, null=False, blank=False)
    article = models.ForeignKey('polls.TrackedArticle', on_delete=models.CASCADE, verbose_name='Артикул', null=False, blank=False)
    text = models.TextField('Содержание', null=False, blank=False)
    stars = models.SmallIntegerField('Кол-во звезд', null=False, blank=False)
    created_date = models.DateTimeField('Дата отзыва на WB')

    class Meta:
        verbose_name = 'Отзыв об артикуле'
        verbose_name_plural = 'Отзывы об артикуле'

    def format_notification_message(self):
        return '<b>🍇 %s</b>\n\n' % (self.article.personal.name) + \
               '<b>🔔 Новый отзыв!</b>\n' + \
               f'🏷 <a href="https://www.wildberries.ru/catalog/{self.article.nmId}/detail.aspx?targetUrl=SP">{self.article.nmId}</a> | {self.article.article}\n\n' + \
               '<b>💫 Оценка:</b> %s\n' % ('⭐️' * self.stars) + \
               '<b>📃 Содержание отзыва:</b>\n%s\n\n' % (self.text) + \
               '<i>🕐 Дата отзыва:</i> %s' % (timezone.make_naive(self.created_date).strftime('%Y.%m.%d %H:%M:%S'))

    def send_notify(self):
        return bot.notify_new_feedback(self)

    def __str__(self):
        return f'{self.id} | {self.article}'


class FeedbackPhoto(models.Model):

    feedback = models.ForeignKey('polls.Feedback', on_delete=models.CASCADE, verbose_name='Отзыв', null=False, blank=False)
    url = models.URLField('Ссылка на фото', max_length=255)

    class Meta:
        verbose_name = 'Фотография отзыва'
        verbose_name_plural = 'Фотографии отзывов'

    def __str__(self):
        return self.url
