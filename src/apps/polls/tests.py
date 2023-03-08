from django.test import TestCase  # noqa
from django.utils import timezone


class WBPersonalApiClientTestCase(TestCase):

    def setUp(self):
        self.start_time = timezone.now()

    def tearDown(self):
        t = timezone.now() - self.start_time
        print(f'{self.id()}: {t}')
