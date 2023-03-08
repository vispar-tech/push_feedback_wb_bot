from apps.bot.models import TelegramUser
from django.test import TestCase  # noqa
from django.utils import timezone


class WBPersonalApiClientTestCase(TestCase):

    def setUp(self):
        self.start_time = timezone.now()
        user = TelegramUser.objects.create(
            user_id=5035911222,
            username='vispar_work',
            phone_number='79956280206',
            WBToken='AsKHsQWKscXADIrtrsEMQq7rh2k9YLw8Ao47WRoFT5YeahiG8W5XF-QJi9W3BGwZ761R7oxWWiVoxO30bgahbzJIC2dGsnEhDyv84XvKzmaFeg'
        )
        user.personal_set.create(
            supplierId='816b3e7f-6c8f-4589-a1c5-dacde727d32f',
            oldId=133977,
            name='ИП Сагиров Алексей Николаевич',
            full_name='Индивидуальный предприниматель Сагиров Алексей Николаевич'
        )

    def tearDown(self):
        t = timezone.now() - self.start_time
        print(f'{self.id()}: {t}')

    def test_login_personal(self):
        pass
