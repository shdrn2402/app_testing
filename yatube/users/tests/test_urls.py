from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class PostURLTests(TestCase):

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        # Ключи: страницы, доступные только для авторизованных пользователей
        # Значения: адреса редиректа и шаблоны к страницам
        self.available_to_authorized_users = {
            '/auth/password_change/': {
                'template': 'users/password_change_form.html',
                'redirect_url': '/auth/login/?next=/auth/password_change/'
            },
            '/auth/password_change/done/': {
                'template': 'users/password_change_done.html',
                'redirect_url': '/auth/login/?next=/auth/password_change/done/'
            },
        }
        # Ключи: страницы, доступные для неавторизованных пользователей
        # Значения: шаблоны к страницам
        self.available_to_unauthorized_users = {
            '/auth/login/': 'users/login.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/logout/': 'users/logged_out.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
        }

    def test_pages_available_to_unauthorized_users(self):
        """Проверка страниц, доступных неавторизованным пользователям."""
        for url in self.available_to_unauthorized_users:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.reason_phrase, 'OK')

    def test_pages_available_to_authorized_users(self):
        """Проверка существования страниц, доступных тольком авторизованным
        пользователям и редирект для неавторизованных пользователей."""
        for url in self.available_to_authorized_users:
            expected_redirect = (
                self.available_to_authorized_users[url]['redirect_url'])
            with self.subTest():
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, expected_redirect)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for adress, template in self.available_to_unauthorized_users.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
        for adress in self.available_to_authorized_users:
            template = self.available_to_authorized_users[adress]['template']
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
