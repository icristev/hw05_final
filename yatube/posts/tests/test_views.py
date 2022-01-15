from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug',
        )
        cls.user = User.objects.create_user(username='no_name')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
            group=cls.group,
        )
        cls.other_group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-other_slug'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес (view) использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
            'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_index_show_correct_context(self):
        """Проверяем Context страницы index"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        context_objects = {
            self.user: first_object.author,
            self.post.text: first_object.text,
            self.group: first_object.group,
            self.post.id: first_object.id,
        }
        for reverse_name, response_name in context_objects.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(response_name, reverse_name)

    def test_post_group_posts_page_show_correct_context(self):
        """Проверяем Context страницы group_posts"""
        response = self.authorized_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}))
        for post in response.context['page_obj']:
            self.assertEqual(post.group, self.group)

    def test_post_profile_page_show_correct_context(self):
        """Проверяем Context страницы profile"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))
        for post in response.context['page_obj']:
            self.assertEqual(post.author, self.user)

    def test_post_posts_edit_page_show_correct_context(self):
        """Проверяем Context страницы post_edit"""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_post_detail_page_show_correct_context(self):
        """Проверяем Context страницы post_detail"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        post_pk = response.context['post'].pk
        self.assertEqual(post_pk, self.post.pk)

    def test_post_post_create_page_show_correct_context(self):
        """Проверяем Context страницы post_create"""
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_new_create(self):
        """При создании поста он должен появляется на главной странице,
        на странице выбранной группы и в
        в профайле пользователя"""
        new_post = Post.objects.create(
            author=self.user,
            text=self.post.text,
            group=self.group
        )
        exp_pages = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.user.username})
        ]
        for rev in exp_pages:
            with self.subTest(rev=rev):
                response = self.authorized_client.get(rev)
                self.assertIn(
                    new_post, response.context['page_obj']
                )

    def test_post_new_not_in_group(self):
        """Проверяем, что созданный пост не находится в другой группе,
        где он не должен находиться."""
        new_post = Post.objects.create(
            author=self.user,
            text=self.post.text,
            group=self.group
        )
        response = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': self.other_group.slug})
        )
        self.assertNotIn(new_post, response.context['page_obj'])

    def test_cache_index(self):
        """Проверка cache главной страницы"""
        posts_count = Post.objects.count()
        response = self.authorized_client.get('posts:index').content
        Post.objects.create(
            author=self.user,
            text=self.post.text,
            group=self.group
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertEqual(response, (
            self.authorized_client.get('posts:index').content))
        cache.clear()
        self.assertEqual(response, (
            self.authorized_client.get('posts:index').content))


class FollowsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='ivan')
        cls.user2 = User.objects.create_user(username='nikolay')

    def setUp(self):
        self.auth_client1 = Client()
        self.auth_client1.force_login(FollowsTests.user1)
        self.auth_client2 = Client()
        self.auth_client2.force_login(FollowsTests.user2)
        cache.clear()

    def test_posts_auth_add_delete_follow(self):
        """Авторизованный пользователь может подписаться."""
        follows_count = Follow.objects.count()
        self.assertFalse(Follow.objects.filter(
            user=FollowsTests.user1,
            author=FollowsTests.user2).exists())
        self.auth_client1.get(reverse('posts:profile_follow',
                                      args=[FollowsTests.user2]))
        self.assertEqual(Follow.objects.count(), follows_count + 1)
        self.assertTrue(Follow.objects.filter(
            user=FollowsTests.user1, author=FollowsTests.user2).exists())

    def test_posts_auth_add_delete_follow(self):
        """Авторизованный пользователь может отписаться."""
        Follow.objects.get_or_create(user=FollowsTests.user1,
                                     author=FollowsTests.user2)
        follows_count = Follow.objects.count()
        self.auth_client1.get(reverse('posts:profile_unfollow',
                                      args=[FollowsTests.user2]))
        self.assertEqual(Follow.objects.count(), follows_count - 1)
        self.assertFalse(Follow.objects.filter(
            user=FollowsTests.user1, author=FollowsTests.user2).exists())

    def test_posts_new_post_add_to_follower(self):
        """Новый пост появляется в ленте подписчиков."""
        Follow.objects.create(user=FollowsTests.user2,
                              author=FollowsTests.user1)
        response = self.auth_client2.get(reverse('posts:follow_index'))
        count_posts = len(response.context['page_obj'])
        Post.objects.create(author=FollowsTests.user1, text='new_text')
        response = self.auth_client2.get(reverse('posts:follow_index'))
        new_count_posts = len(response.context['page_obj'])
        self.assertEqual(count_posts + 1, new_count_posts)

    def test_posts_new_post_not_add_to_not_follower(self):
        """Новый пост не появляется в ленте не подписчиков."""
        response = self.auth_client2.get(reverse('posts:follow_index'))
        count_posts = len(response.context['page_obj'])
        Post.objects.create(author=FollowsTests.user1, text='new_text')
        response = self.auth_client2.get(reverse('posts:follow_index'))
        new_count_posts = len(response.context['page_obj'])
        self.assertEqual(count_posts, new_count_posts)
