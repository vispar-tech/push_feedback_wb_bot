from apps.bot.models import TelegramUser
from apps.bot.utils.tools import WBPersonalApiClient
from apps.polls.models import Personal
from django.test import TestCase  # noqa
from django.utils import timezone


class WBPersonalApiClientTestCase(TestCase):

    def setUp(self):
        self.start_time = timezone.now()

    def tearDown(self):
        t = timezone.now() - self.start_time
        print(f'{self.id()}: {t}')

    def test_login_personal(self):
        user = TelegramUser.objects.create(
            username='vispar_work',
            user_id=5035911222
        )

        client = WBPersonalApiClient()
        response = client.send_login_code('+79118293291')
        if response[0]:
            token = response[1]['token']
            while True:
                verify_code = input('Введите код подтверждения: ')
                verify_response = client.verify_login_code(token, verify_code)
                if verify_response[0]:
                    user.WBToken = verify_response[1]['WBToken']
                    user.save()
                    client.WBToken = user.WBToken
                    break
                else:
                    print(response[1])
                    exit()
            suppliers_response = client.get_suppliers()
            if suppliers_response[0]:
                for supplier in suppliers_response[1]:
                    personal = Personal.objects.create(
                        user=user,
                        supplierId=supplier['id'],
                        oldId=supplier['oldID'],
                        name=supplier['name'],
                        full_name=supplier['fullName']
                    )
                    print(f'New personal added: {personal} {personal.supplierId}')
            else:
                print(response[1])
        else:
            print(response[1])
