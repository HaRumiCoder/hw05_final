from django.test import TestCase, Client

UNEXISTING_PAGE = '/unexisting_page/'


class CoreURLTests(TestCase):
    def setUp(self):
        self.guest = Client()

    def test_urls_uses_correct_template(self):
        self.assertTemplateUsed(
            self.guest.get(UNEXISTING_PAGE), 'core/404.html')
