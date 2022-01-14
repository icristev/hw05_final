from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from yatube.settings import POSTS_ON_INDEX

from ..models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='no_name')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание'
        )

        Post.objects.bulk_create([
            Post(
                author=cls.user,
                text=f'Тестовый текст {num}',
                group=cls.group
            )
            for num in range(1, 18)]
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Paginator выводит 10 записей на одной странице."""
        reverse_dict_for_paginator_test = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={
                    'slug': self.group.slug}),
            reverse('posts:profile', kwargs={
                    'username': self.user.username})
        ]
        for reverse_name in reverse_dict_for_paginator_test:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']),
                                 POSTS_ON_INDEX)

    def test_second_page_contains_three_records(self):
        """Paginator выводит оставшиеся 5 записей на второй странице."""
        reverse_dict_for_paginator_test = [
            reverse('posts:index') + '?page=2',
            reverse(
                'posts:group_posts', kwargs={
                    'slug': self.group.slug}) + '?page=2',
            reverse(
                'posts:profile', kwargs={
                    'username': self.user.username}) + '?page=2'
        ]
        for reverse_name in reverse_dict_for_paginator_test:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name + '?page=2')
                self.assertEqual(Post.objects.count() %
                                 len(response.context['page_obj']),
                                 (Post.objects.count() % POSTS_ON_INDEX))
