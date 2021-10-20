from django.test import Client, TestCase


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.static_pages = {'/about/author/': 'about/author.html',
                             '/about/tech/': 'about/tech.html',
                             }

    def test_pages_available_to_unauthorized_users(self):
        """Проверка доступности статических страниц."""
        # Страницы, на которые можно попасть неавторизованному пользователю

        for url in self.static_pages.keys():
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.reason_phrase, 'OK')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        for adress, template in self.static_pages.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
