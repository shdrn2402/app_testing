from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст!!!',
        )

    def setUp(self):
        self.test_post = PostModelTest.post
        self.test_group = PostModelTest.group

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__
        __str__ post - это первые 15 символов post.text,
        __str__ group - это строка post.title."""

        strs_to_check = {self.test_post: self.test_post.text[:15],
                         self.test_group: self.test_group.title,
                         }

        for to_check, expected_value in strs_to_check.items():
            with self.subTest():
                self.assertEqual(expected_value, str(to_check))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.test_post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {'text': 'Текст нового поста',
                            'group': ('Группа, к которой будет '
                                      'относиться пост'),
                            }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.test_post._meta.get_field(field).help_text,
                    expected_value
                )
