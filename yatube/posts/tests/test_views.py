from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class TemplateViewsTests(TestCase):
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
        self.author_client = Client()
        self.author_client.force_login(TemplateViewsTests.author_user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Ключ:  reverse(name)
        # Значение: имя_html_шаблона
        page_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            (reverse('posts:post_edit',
                     kwargs={'post_id': TemplateViewsTests.post.pk})
             ): 'posts/create_post.html',
            (reverse('posts:post_detail',
                     kwargs={'post_id': TemplateViewsTests.post.pk})
             ): 'posts/post_detail.html',
            (reverse('posts:profile',
                     kwargs={'username':
                             TemplateViewsTests.author_user.username})
             ): 'posts/profile.html',
            (reverse('posts:group_list',
                     kwargs={'slug': TemplateViewsTests.group.slug})
             ): 'posts/group_list.html',
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in page_names_templates.items():
            with self.subTest(template=template):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='author_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.desired_posts_amount = 13
        cls.test_group_posts_amount = cls.desired_posts_amount
        cls.author_posts_amount = cls.desired_posts_amount
        for i in range(cls.desired_posts_amount):
            Post.objects.create(
                text='Текст ' + str(i + 1),
                author=cls.author_user,
                group=cls.group,
            )

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        self.pages_with_paginator = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': PaginatorViewsTest.group.slug}),
            reverse('posts:profile',
                    kwargs={'username':
                            PaginatorViewsTest.author_user.username}),
        ]
        self.pages_without_paginator = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            reverse('posts:post_detail', kwargs={'post_id': '1'}),
        ]

        if PaginatorViewsTest.desired_posts_amount // 10 == 0:
            self.expected_posts_amount = (PaginatorViewsTest.
                                          desired_posts_amount)
        else:
            self.expected_posts_amount = 10
        self.expected_last_page_posts_amount = (
            PaginatorViewsTest.desired_posts_amount % 10)

    def test_pages_contain_correct_number_of_posts(self):
        '''Проверка правильного количества постов на странице'''
        for page in self.pages_with_paginator:
            with self.subTest(page=page):
                page_data = self.guest_client.get(page)
                posts_amount = len(
                    page_data.context.get('page_obj').object_list)
                self.assertEqual(posts_amount, self.expected_posts_amount)
                while page_data.context.get('page_obj').has_next():
                    page_data = self.guest_client.get(
                        page + '?page='
                        + str(page_data.context.get('page_obj'
                                                    ).next_page_number()))
                    self.assertEqual(posts_amount, self.expected_posts_amount)

    def test_posts_sorting_on_page(self):
        '''Проверка верной сорировки постов'''
        expected_page_pk_sequence = list(
            range(PaginatorViewsTest.desired_posts_amount, 0, -1))

        for page in self.pages_with_paginator:
            real_page_pk_sequence = []
            with self.subTest(page=page):
                page_data = self.guest_client.get(page)
                for pk in [post.pk for post in
                           page_data.context.get('page_obj').object_list]:
                    real_page_pk_sequence.append(pk)
                while page_data.context.get('page_obj').has_next():
                    page_data = self.guest_client.get(
                        page + '?page='
                        + str(page_data.context.get('page_obj'
                                                    ).next_page_number()))
                    for pk in [post.pk for post in
                               page_data.context.get('page_obj').object_list]:
                        real_page_pk_sequence.append(pk)

                self.assertEqual(expected_page_pk_sequence,
                                 real_page_pk_sequence)

    def test_group_page_has_correct_posts(self):
        '''Проверка что на страницу группы попадают
        только посты нужной группы'''
        group_name_list = []
        page = reverse('posts:group_list',
                       kwargs={'slug': PaginatorViewsTest.group.slug})
        page_data = self.guest_client.get(page)
        for group_name in [post.group.title for post in
                           page_data.context.get('page_obj').object_list]:
            group_name_list.append(group_name)
        while page_data.context.get('page_obj').has_next():
            page_data = self.guest_client.get(
                page + '?page='
                + str(page_data.context.get('page_obj'
                                            ).next_page_number()))
            for group_name in [post.group.title for post in
                               page_data.context.get('page_obj').object_list]:
                group_name_list.append(group_name)

        self.assertEqual(group_name_list,
                         [PaginatorViewsTest.group.title]
                         * PaginatorViewsTest.test_group_posts_amount)

    def test_author_profile_page_has_correct_posts(self):
        '''Проверка что на страницу профайла попадают
        только посты автора'''
        author_posts_list = []
        page = reverse('posts:profile',
                       kwargs={'username':
                               PaginatorViewsTest.author_user.username})
        page_data = self.guest_client.get(page)
        for author_name in [post.author.username for post in
                            page_data.context.get('page_obj').object_list]:
            author_posts_list.append(author_name)
        while page_data.context.get('page_obj').has_next():
            page_data = self.guest_client.get(
                page + '?page='
                + str(page_data.context.get('page_obj'
                                            ).next_page_number()))
            for author_name in [post.author.username for post in
                                page_data.context.get('page_obj').object_list]:
                author_posts_list.append(author_name)

        self.assertEqual(author_posts_list,
                         [PaginatorViewsTest.author_user.username]
                         * PaginatorViewsTest.author_posts_amount)


class CorrectPostsCreationViewsTest(TestCase):
    @ classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='author_user')
        cls.other_user = User.objects.create_user(username='other_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',)
        cls.other_group = Group.objects.create(
            title='Еще одна тестовая группа',
            slug='other_test_slug',
            description='Еще одно тестовое описание',)

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Значения словаря - ожидаемое количество записей на страницах (ключи)
        # после добавления постов.
        self.page_post_amount = {
            reverse('posts:index'): Post.objects.count(),
            reverse('posts:group_list',
                    kwargs={'slug': CorrectPostsCreationViewsTest.group.slug}
                    ):
            Post.objects.filter(
                group=CorrectPostsCreationViewsTest.group).count(),
            reverse('posts:profile',
                    kwargs={'username':
                            CorrectPostsCreationViewsTest.author_user.username}
                    ):
            Post.objects.filter(
                    author=CorrectPostsCreationViewsTest.author_user).count(),
            reverse('posts:profile',
                    kwargs={'username':
                            CorrectPostsCreationViewsTest.other_user.username}
                    ):
            Post.objects.filter(
                    author=CorrectPostsCreationViewsTest.other_user).count(),
            reverse('posts:group_list',
                    kwargs={'slug':
                            CorrectPostsCreationViewsTest.other_group.slug}
                    ):
            Post.objects.filter(
                    group=CorrectPostsCreationViewsTest.other_group).count(),
        }
        # Словарь с ключом - описанием нового поста
        # и значениями - данные для нового поста
        self.new_posts_data = {
            'main_author_group_post': {
                'text': 'Текст автора остальных постов',
                'author': CorrectPostsCreationViewsTest.author_user,
                'group': CorrectPostsCreationViewsTest.group,
                'to_add': (
                    reverse('posts:profile',
                            kwargs={'username':
                                    CorrectPostsCreationViewsTest.author_user.username}
                            ),
                    reverse('posts:group_list',
                            kwargs={
                                'slug':
                                CorrectPostsCreationViewsTest.group.slug})
                ),
            },
            'main_author_other_group_post': {
                'text': 'Текст автора остальных постов новой группы',
                'author': CorrectPostsCreationViewsTest.author_user,
                'group': CorrectPostsCreationViewsTest.other_group,
                'to_add': (
                    reverse('posts:profile',
                            kwargs={'username':
                                    CorrectPostsCreationViewsTest.author_user.username}
                            ),
                    reverse('posts:group_list', kwargs={
                            'slug':
                            CorrectPostsCreationViewsTest.other_group.slug})
                ),
            },
            'other_author_group_post': {
                'text': 'Текст другого автора существующей группы',
                'author': CorrectPostsCreationViewsTest.other_user,
                'group': CorrectPostsCreationViewsTest.group,
                'to_add': (
                    reverse('posts:profile',
                            kwargs={'username':
                                    CorrectPostsCreationViewsTest.other_user.username}
                            ),
                    reverse('posts:group_list',
                            kwargs={'slug':
                                    CorrectPostsCreationViewsTest.group.slug})
                ),
            },
            'other_author_other_group_post': {
                'text': 'Текст другого автора новой группы',
                'author': CorrectPostsCreationViewsTest.other_user,
                'group': CorrectPostsCreationViewsTest.other_group,
                'to_add': (
                    reverse('posts:profile',
                            kwargs={'username':
                                    CorrectPostsCreationViewsTest.other_user.username}),
                    reverse('posts:group_list',
                            kwargs={'slug':
                                    CorrectPostsCreationViewsTest.other_group.slug})
                ),
            }
        }

    def add_posts(self, text, author, group):
        # Добавление поста основного автора с группой
        Post.objects.create(text=text,
                            author=author,
                            group=group
                            )
        return 0

    def test_created_post_goes_to_database(self):
        '''После создания посты попадают в базу данных.'''
        # Добавление постов. Должно добавится 4 поста.
        # 2 автора остальных постов, два нового атвора.
        # Из них два с новой группой
        for new_post in self.new_posts_data:
            text = self.new_posts_data[new_post]['text']
            author = self.new_posts_data[new_post]['author']
            group = self.new_posts_data[new_post]['group']
            self.add_posts(text, author, group)
            self.page_post_amount[reverse('posts:index')] += 1
            for to_add in self.new_posts_data[new_post]['to_add']:
                self.page_post_amount[to_add] += 1
        # Проверка изменения общего количества постов в базе
        self.assertEqual(Post.objects.count(),
                         self.page_post_amount[
                             reverse('posts:index')])
        # Проверка изменения количества постов автора в базе
        self.assertEqual(Post.objects.filter(
            author=CorrectPostsCreationViewsTest.author_user).count(),
            self.page_post_amount[
                reverse('posts:profile',
                        kwargs={'username':
                                CorrectPostsCreationViewsTest.author_user.username})]
        )
        # Проверка количества постов нового автора в базе
        self.assertEqual(Post.objects.filter(
            author=CorrectPostsCreationViewsTest.other_user).count(),
            self.page_post_amount[
                reverse('posts:profile',
                        kwargs={'username':
                                CorrectPostsCreationViewsTest.other_user.username})]
        )
        # Проверка изменения количества постов группы в базе
        self.assertEqual(Post.objects.filter(
            group=CorrectPostsCreationViewsTest.group).count(),
            self.page_post_amount[
                reverse('posts:group_list',
                        kwargs={'slug':
                                CorrectPostsCreationViewsTest.group.slug})]
        )
        # Проверка изменения количества постов новой группы в базе
        self.assertEqual(Post.objects.filter(
            group=CorrectPostsCreationViewsTest.other_group).count(),
            self.page_post_amount[
                reverse('posts:group_list',
                        kwargs={'slug':
                                CorrectPostsCreationViewsTest.other_group.slug})]
        )

    # Не уверен, что этот тест не является дублирубщим предыдущий
    def test_created_post_goes_to_correct_page(self):
        '''После создания посты попадают на нужные страницы.'''
        # Добавление постов
        for new_post in self.new_posts_data:
            text = self.new_posts_data[new_post]['text']
            author = self.new_posts_data[new_post]['author']
            group = self.new_posts_data[new_post]['group']
            self.add_posts(text, author, group)
            self.page_post_amount[reverse('posts:index')] += 1
            for to_add in self.new_posts_data[new_post]['to_add']:
                self.page_post_amount[to_add] += 1
        # Проверяем, что количество постов на нужной
        # странице изменилось и составляет ожидаемое значение
        for page in self.page_post_amount:
            with self.subTest(page=page):
                page_data = self.guest_client.get(page)
                posts_amount = len(
                    page_data.context.get('page_obj').object_list)
                while page_data.context.get('page_obj').has_next():
                    page_data = self.guest_client.get(
                        page + '?page='
                        + str(page_data.context.get('page_obj'
                                                    ).next_page_number()))
                    posts_amount += len(
                        page_data.context.get('page_obj').object_list)
                self.assertEqual(posts_amount, self.page_post_amount[page])

    def test_created_post_goes_to_correct_place_on_page(self):
        '''После создания посты попадают на первую позицию
        на своей странице.'''
        # Добавление поста существующего автора в существующую группу
        text = self.new_posts_data['main_author_group_post']['text']
        author = self.new_posts_data['main_author_group_post']['author']
        group = self.new_posts_data['main_author_group_post']['group']
        self.add_posts(text, author, group)
        # Теперь этот пост должен быть первым на главной странице,
        # на странице группы и на странице автора
        pages_to_check = list(self.page_post_amount.keys())[:3]
        for page in pages_to_check:
            with self.subTest(page=page):
                page_data = self.guest_client.get(page)
                self.assertEqual(
                    page_data.context.get('page_obj')[0].text,
                    self.new_posts_data['main_author_group_post']['text'])
                self.assertEqual(
                    page_data.context.get('page_obj')[0].author.username,
                    self.new_posts_data['main_author_group_post'
                                        ]['author'].username)
                self.assertEqual(
                    page_data.context.get('page_obj')[0].group.title,
                    self.new_posts_data['main_author_group_post'
                                        ]['group'].title)
        # Добавление поста существующего автора с новой группой
        # оставит первым постом на странице старой группы вышедобавленный пост
        text = self.new_posts_data['main_author_other_group_post']['text']
        author = self.new_posts_data['main_author_other_group_post']['author']
        group = self.new_posts_data['main_author_other_group_post']['group']
        self.add_posts(text, author, group)
        # на главной странице первый пост поменялся
        page_data = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            page_data.context.get('page_obj')[0].text,
            self.new_posts_data['main_author_other_group_post']['text'])
        # на странице группы первым остался пост добавленный ранее
        # соответствует значению 'main_author_group_post' словаря
        page_data = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug':
                            CorrectPostsCreationViewsTest.group.slug}))
        self.assertEqual(
            page_data.context.get('page_obj')[0].text,
            self.new_posts_data['main_author_group_post']['text'])
        # на странице пользователя первым стал последний добавленный пост
        page_data = self.guest_client.get(
            reverse('posts:profile',
                    kwargs={'username':
                            CorrectPostsCreationViewsTest.author_user.username}))
        self.assertEqual(
            page_data.context.get('page_obj')[0].text,
            self.new_posts_data['main_author_other_group_post']['text'])
        # на странице новой группы первым и единственным стал
        # последний добавленный пост
        page_data = self.guest_client.get(
            reverse('posts:group_list',
                    kwargs={'slug':
                            CorrectPostsCreationViewsTest.other_group.slug}))
        self.assertEqual(
            page_data.context.get('page_obj')[0].text,
            self.new_posts_data['main_author_other_group_post']['text'])
        self.assertEqual(len(page_data.context.get('page_obj')), 1)


class ContextViewsTest(TestCase):
    @ classmethod
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
        self.author_client = Client()
        self.author_client.force_login(ContextViewsTest.author_user)
        self.pages_with_paginator = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug':
                                                ContextViewsTest.group.slug}),
            reverse('posts:profile', kwargs={'username':
                                             ContextViewsTest.author_user.username}),
        ]
        self.pages_with_form = [
            reverse('posts:post_create'),
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            '1'}),
        ]
        self.pages_without_form = [
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            '1'}),
        ]

    def test_pages_with_paginator_show_correct_context(self):
        """Шаблоны с паджинатором сформированы с правильным контекстом."""
        for page in self.pages_with_paginator:
            with self.subTest():
                response = self.author_client.get(page)
                self.assertEqual(
                    response.context.get('page_obj').object_list[0].text,
                    ContextViewsTest.post.text)
                self.assertEqual(
                    response.context.get(
                        'page_obj').object_list[0].author.username,
                    ContextViewsTest.author_user.username)
                self.assertEqual(
                    response.context.get(
                        'page_obj').object_list[0].group.title,
                    ContextViewsTest.group.title)
                self.assertEqual(
                    response.context.get(
                        'page_obj').object_list[0].group.slug,
                    ContextViewsTest.group.slug)
                self.assertEqual(
                    response.context.get(
                        'page_obj').object_list[0].group.description,
                    ContextViewsTest.group.description)

    def test_pages_without_form_show_correct_context(self):
        """Шаблоны без форм сформированы с правильным контекстом."""
        for page in self.pages_without_form:
            with self.subTest():
                response = self.author_client.get(page)
                self.assertEqual(
                    response.context.get('post').text,
                    ContextViewsTest.post.text)
                self.assertEqual(
                    response.context.get('post').author.username,
                    ContextViewsTest.author_user.username)
                self.assertEqual(
                    response.context.get('post').group.title,
                    ContextViewsTest.group.title)
                self.assertEqual(
                    response.context.get('post').group.slug,
                    ContextViewsTest.group.slug)
                self.assertEqual(
                    response.context.get('post').group.description,
                    ContextViewsTest.group.description)

    def test_pages_with_form_show_correct_context(self):
        """Шаблоны с формой сформированы с правильным контекстом."""
        model_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField,
        }
        for page in self.pages_with_form:
            with self.subTest(page=page):
                response = self.author_client.get(page)
                for field, expected in model_fields.items():
                    with self.subTest(field=field):
                        form_field = response.context.get(
                            'form').fields.get(field)
                        self.assertIsInstance(form_field, expected)
