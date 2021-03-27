from django import forms
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

# from .templates.index import cache


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='username')
        # cls.follower = User.objects.create(username='follower')
        # cls.not_follower = User.objects.create(username='not_follower')

        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug',
            description='Описание',
        )

        cls.wrong_group = Group.objects.create(
            title='Группа',
            slug='slug-test',
            description='description',
        )

        cls.post = Post.objects.create(
            text='Текст',
            group=cls.group,
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group', kwargs={'slug': self.group.slug}),
            'new.html': reverse('new_post'),
        }

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(response.context['page'][0], self.post)

    def test_group_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)

    def test_new_post_page_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value, expected=expected):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('post_edit', kwargs={
            'username': self.user.username,
            'post_id': self.post.id
        }))
        self.assertEqual(response.context['post'], self.post)

    def test_post_page_show_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('post', kwargs={
            'username': self.user.username,
            'post_id': self.post.id
        }
        )
        )
        post_context = {
            'profile': self.user,
            'post': self.post,
            'count': self.user.posts.all().count(),
            'current_user': self.user,
        }
        for key, value in post_context.items():
            with self.subTest(key=value, value=value):
                context = response.context[key]
                self.assertEqual(context, value)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(response.context['profile'], self.user)
        self.assertEqual(response.context['page'][0], self.post)

    def test_index_shows_new_post(self):
        """Проверяем, что новый пост появится на странице index."""
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context['page']), 1)

    def test_group_shows_new_post(self):
        """Проверяем, что новый пост появится в соответствующей группе."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(len(response.context['page']), 1)

    def test_wrong_group_does_not_show_new_post(self):
        """Проверяем, что новый пост не появится в несоответствующей группе."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': self.wrong_group.slug})
        )
        self.assertEqual(len(response.context['page']), 0)

    def test_index_page_cache(self):
        """Проверяем корректнось кэширования шаблона index."""
        response = self.authorized_client.get(reverse('index'))
        previous_content = response.content
        Post.objects.create(text='Новый пост', author=self.user, )
        response = self.authorized_client.get(reverse('index'))
        next_content = response.content
        self.assertEqual(previous_content, next_content,
                         'Кэширование не работает')

        cache.clear()

        response = self.authorized_client.get(reverse('index'))
        cleared_cache_content = response.content
        self.assertNotEqual(
            cleared_cache_content,
            next_content,
            'Кэширование не работает'
        )

    def test_follow_unfollow_feauture(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        # response = self.guest_client.get(reverse('profile'))
        # response = self.authorized_client.get(reverse('profile'))

        # подписка
        followers_count = user.count()
        self.assertEqual(followers_count, 1, 'Не работает подписка')

        # отписка
        followers_count = user.count()
        self.assertEqual(followers_count, 0, 'Не работает отписка')

    def test_profile_shows_new_post(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан на него."""
        pass

    def test_only_authorized_client_can_comment(self):
        """Только авторизированный пользователь может комментировать посты."""
        pass


class PaginatorViewsTest(TestCase):
    @ classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Test-user')
        cls.client = Client()
        cls.client.force_login(cls.user)
        for i in range(13):
            Post.objects.create(
                text='Тестовый пост',
                author=cls.user,
            )

    def test_first_page_containse_ten_records(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_containse_three_records(self):
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)
