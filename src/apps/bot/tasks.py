from datetime import datetime

from apps.bot.models import TelegramUser
from apps.bot.utils.tools import WBPersonalApiClient
from core.celery import app
from django.db.models import Q
from django.utils import timezone


@app.task(name='Send new feedbacks notification')
def send_new_feedback_notification():
    for user in TelegramUser.objects.filter(Q(notification=True) and ~Q(WBToken=None)):
        fetch_new_feedbacks(user.pk)


@app.task(name='Fetch new feedbacks')
def fetch_new_feedbacks(pk):
    if TelegramUser.objects.filter(pk=pk).exists():
        user = TelegramUser.objects.get(pk=pk)
        for personal in user.personal_set.all():
            client = WBPersonalApiClient(personal.supplierId, user.WBToken)
            feedbacks = client.get_feedbacks()
            if feedbacks[0]:
                for feedback in feedbacks[1]:
                    if personal.trackedarticle_set.filter(nmId=str(feedback['nmId'])).exists() and feedback['productValuation'] <= user.notification_stars:
                        article = personal.trackedarticle_set.get(nmId=str(feedback['nmId']))
                        if not article.feedback_set.filter(id=feedback['id']).exists():
                            new_feedback = article.feedback_set.create(
                                id=feedback['id'],
                                text=feedback['text'],
                                stars=feedback['productValuation'],
                                created_date=timezone.make_aware(datetime.strptime(feedback['createdDate'], '%Y-%m-%dT%H:%M:%SZ'))
                            )
                            if len(feedback['photoLinks']) != 0:
                                for photo_link in feedback['photoLinks']:
                                    new_feedback.feedbackphoto_set.create(url=photo_link['miniSize'])
                            new_feedback.send_notify()
            else:
                user.reset_WBToken()
                break
