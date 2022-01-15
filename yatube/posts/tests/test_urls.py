from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


LOGIN_REDIRECT_URL = reverse('posts:index')

LOGIN_URL = reverse('users:login')


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.not_author = User.objects.create_user(username='ivan')
        cls.user = User.objects.create_user(username='no_name')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client(self.user)
        self.authorized_client.force_login(self.user)
        self.client_not_author = Client()
        self.client_not_author.force_login(self.not_author)
        cache.clear()

    def test_posts_urls_exist_at_desired_location(self):
        """Проверка общедоступных страниц."""
        urls = ['/', f'/group/{self.group.slug}/',
                f'/profile/{self.user.username}/',
                f'/posts/{self.post.pk}/', '/no_page/']
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                status = (HTTPStatus.NOT_FOUND if url == '/no_page/'
                          else HTTPStatus.OK)
                self.assertEqual(response.status_code, status,
                                 f'Проверьте url страницы {url}')

    def test_kod(self):
        field_urls_code = {
            reverse(
                'posts:index'): HTTPStatus.OK,
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, response_code in field_urls_code.items():
            with self.subTest(url=url):
                status_code = self.guest_client.get(url).status_code
                self.assertEqual(status_code, response_code)

    def test_redirect_if_not_logged_in(self):
        """Адрес "/create" перенаправляет
        неавторизованного пользователя"""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(response, '/accounts/login/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон,
        для авторизованного пользователя"""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
            '/follow/': 'posts/follow.html',
            '/no_page/': 'core/404.html'
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.authorized_client.get(address),
                    template)

    def test_home_url_uses_correct_template(self):
        """Страница '/create' использует шаблон 'posts/create_post.html'
         для авторизованного пользователя"""
        response = self.authorized_client.get('/create/')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_edit_page_correct_template(self):
        '''Адрес '/edit' редактирования поста использует шаблон create.html
        для автора поста'''
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}))
        self.assertTemplateUsed(response, 'posts/create_post.html')
