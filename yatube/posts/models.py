from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):

    GROUP_CHOICES = [
        ('Юмор', 'Юмор'),
        ('Животные', 'Животные'),
        ('Авто', 'Авто'),
        ('Книги', 'Книги'),
        ('Сериалы', 'Сериалы'),
        ('Биография', 'Биография'),
    ]
    SLUG_CHOISES = [
        ('humor', 'humor'),
        ('animals', 'animals'),
        ('auto', 'auto'),
        ('books', 'books'),
        ('serials', 'serials'),
        ('biograthy', 'biograthy'),
    ]

    title = models.CharField(max_length=200, choices=GROUP_CHOICES)
    slug = models.SlugField(
        max_length=50, unique=True, choices=SLUG_CHOISES)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField('Текст поста',  # verbose_name
                            help_text='Текст нового поста',
                            )
    pub_date = models.DateTimeField('Дата публикации',  # verbose_name
                                    auto_now_add=True,
                                    )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name='Автор',
                               )
    group = models.ForeignKey(Group,
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              related_name='posts',
                              verbose_name='Группа',
                              help_text=(
                                  'Группа, к которой будет относиться пост'),
                              )

    def __str__(self):
        return self.text[:15]

    class Meta:
        ordering = ['-pub_date', '-pk']
