import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()
login_create_post = reverse('users:login')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='no_name')
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Описание',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
            group=cls.group,)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Правильная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
            'author': self.post.author
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.user}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_object = Post.objects.order_by('-id').first()
        self.assertEqual(form_data['text'], last_object.text)
        self.assertEqual(form_data['group'], last_object.group.pk)
        self.assertEqual(form_data['author'], last_object.author)

    def test_edit_post(self):
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
            'author': self.post.author,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(form_data['text'], self.post.text)
        self.assertEqual(form_data['group'], self.group.pk)
        self.assertEqual(form_data['author'], self.post.author)

    def test_create_post_guest_client(self):
        """Попытка создать запись как гостевой пользователь"""
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.pk,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post_create_url = reverse('posts:post_create')
        post_create_redirect = f'{login_create_post}?next={post_create_url}'
        self.assertRedirects(response, post_create_redirect)
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_guest_client(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Иной новый текст поста',
            'group': self.group.pk,
        }
        response = self.client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        post_edit_url = reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}
        )
        post_edit_redirect = f'{login_create_post}?next={post_edit_url}'
        self.assertRedirects(response, post_edit_redirect)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertNotEqual(self.post.text, form_data['text'])
