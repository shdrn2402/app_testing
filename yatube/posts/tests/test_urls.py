from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='author_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author_user,
            group=cls.group,
            text='Тестовый текст!!!',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_author_client = Client()
        self.other_user = User.objects.create_user(username='other_user')
        self.authorized_client.force_login(self.other_user)
        self.authorized_author_client.force_login(PostURLTests.author_user)
        # Ключи: страницы, доступные только для авторизованных пользователей
        # Значения: адреса редиректа и шаблоны к страницам
        self.available_to_authorized_users = {
            reverse('posts:post_create'): {
                'template': 'posts/create_post.html',
                'redirect_url': '/auth/login/?next=/create/'
            },
            reverse('posts:post_edit',
                    kwargs={'post_id': PostURLTests.post.pk}): {
                'template': 'posts/create_post.html',
                'redirect_url': '/auth/login/?next=/posts/1/edit/'},
        }
        # Ключи: страницы, доступные для неавторизованных пользователей
        # Значения: шаблоны к страницам
        self.available_to_unauthorized_users = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': PostURLTests.post.pk}):
            'posts/post_detail.html',
            reverse('posts:group_list',
                    kwargs={'slug': PostURLTests.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username':
                            PostURLTests.author_user.username}):
            'posts/profile.html',
        }

    def test_non_existent_page(self):
        """Проверка несуществующей страницы, на возврат кода 404."""
        response = self.guest_client.get('no_such_page')
        self.assertEqual(response.reason_phrase, 'Not Found')

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

    def test_pages_available_to_author(self):
        """Проверка страницы редактирования поста, доступной тольком автору
        и редирект для авторизованных пользователей - не авторов."""
        response = self.authorized_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(response, '/posts/1/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for adress, template in self.available_to_unauthorized_users.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
        for adress in self.available_to_authorized_users:
            template = self.available_to_authorized_users[adress]['template']
            with self.subTest(adress=adress):
                # Шаблон для аторизованного не автора не проверяется, так как в
                # случае обращения не автора происходит редирект а не рендер
                response = self.authorized_author_client.get(adress)
                self.assertTemplateUsed(response, template)
