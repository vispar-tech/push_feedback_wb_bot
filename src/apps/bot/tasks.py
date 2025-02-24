from datetime import datetime, timedelta

from apps.bot.models import TelegramUser
from apps.bot.utils import tools
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
                        if not article.feedback_set.filter(wb_id=feedback['id']).exists():
                            print(datetime.strptime(feedback['createdDate'], '%Y-%m-%dT%H:%M:%SZ'))
                            new_feedback = article.feedback_set.create(
                                wb_id=feedback['id'],
                                text=feedback['text'],
                                stars=feedback['productValuation'],
                                created_date=timezone.make_aware(datetime.strptime(feedback['createdDate'], '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=3))
                            )
                            if len(feedback['photoLinks']) != 0:
                                for photo_link in feedback['photoLinks']:
                                    new_feedback.feedbackphoto_set.create(url=photo_link['miniSize'])
                            new_feedback.send_notify()


@app.task(name='Update table sheets')
def update_table_sheets():
    service = tools.get_service_sacc()
    sheets = tools.get_spreadsheets()
    requests = []
    for sheet in sheets[1:]:
        requests.append({
            'deleteSheet': {
                'sheetId': sheet.get('properties').get('sheetId')
            }
        })
    if len(requests) != 0:
        tools.delete_sheets(service, requests)

    for user in TelegramUser.objects.filter(Q(notification=True) and ~Q(WBToken=None)):
        for personal in user.personal_set.all():
            if len(personal.trackedarticle_set.all()) != 0:
                sheet_name = f'#{personal.id} {personal.name}'
                response = tools.add_sheet(service, sheet_name)
                table_values = [
                    ['Артикул WB(ссылка)', 'Артикул поставщика', 'Кол-во отзывов']
                ]
                for article in personal.trackedarticle_set.all():
                    table_values.append([
                        f'=HYPERLINK("https://www.wildberries.ru/catalog/{article.nmId}/detail.aspx?targetUrl=SP"; "{article.nmId}")',
                        article.article,
                        '' if len(article.feedback_set.all()) == 0 else len(article.feedback_set.all())
                        ])
                tools.append_table_values(service, sheet_name, table_values)
                tools.auto_resize_sheet(service, response.get('replies')[0].get('addSheet').get('properties').get('sheetId'))
