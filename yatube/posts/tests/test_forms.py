from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class FormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='author_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',)
        cls.post = Post.objects.create(
            text='Тестовый текст!!!',
            author=cls.author_user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(FormsTest.author_user)

    def tearDown(self):
        FormsTest.post.text = 'Тестовый текст!!!'
        FormsTest.post.group = Group.objects.get(slug='test_slug')

    def test_created_no_group_author_post_forms(self):
        posts_amount = Post.objects.count()
        context = {
            'text': 'Пост создан без группы авторизованным пользователем',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=context,
            follow=True
        )
        latest_post = Post.objects.order_by('-id').first()
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': FormsTest.author_user}))
        self.assertEqual(Post.objects.count(), posts_amount + 1)
        self.assertEqual(latest_post.text, context['text'])
        self.assertEqual(latest_post.group, None)

    def test_created_group_author_post_forms(self):
        posts_amount = Post.objects.count()
        context = {
            'text': 'Пост создан в группе авторизованным пользователем',
            'group': FormsTest.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=context,
            follow=True
        )
        latest_post = Post.objects.order_by('-id').first()
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': FormsTest.author_user}))
        self.assertEqual(Post.objects.count(), posts_amount + 1)
        self.assertEqual(latest_post.text, context['text'])
        self.assertEqual(latest_post.group, FormsTest.group)

    def test_created_no_group_guest_post_forms(self):
        posts_amount = Post.objects.count()
        context = {
            'text': 'Пост гостя без группы',
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=context,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse('posts:post_create'))
        self.assertEqual(Post.objects.count(), posts_amount)

    def test_created_group_guest_post_forms(self):
        posts_amount = Post.objects.count()
        context = {
            'text': 'Пост гостя в группе',
            'group': FormsTest.group.id
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=context,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse('posts:post_create'))
        self.assertEqual(Post.objects.count(), posts_amount)

    def test_author_post_edit_form(self):
        posts_amount = Post.objects.count()
        context = {
            'text': 'Тестовый текст отредактирован без группы',
            'group': ''
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': FormsTest.post.id}),
            data=context,
            follow=True
        )
        FormsTest.post.refresh_from_db()
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': FormsTest.post.id}))
        self.assertEqual(Post.objects.count(), posts_amount)
        self.assertEqual(FormsTest.post.text, context['text'])
        self.assertEqual(FormsTest.post.group, None)

    def test_guest_post_edit_form(self):
        context = {
            'text': 'Тестовый текст отредактирован без группы',
            'group': ''
        }
        response = self.client.post(
            reverse('posts:post_edit', kwargs={'post_id': FormsTest.post.id}),
            data=context,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse(
                'posts:post_edit', kwargs={'post_id': FormsTest.post.id}))
        self.assertNotEqual(FormsTest.post.text, context['text'])
        self.assertNotEqual(FormsTest.post.group.title, None)
