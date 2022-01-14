from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            pub_date='21.12.1993 21:11',
        )

    def test_models_have_correct_object_names_group(self):
        """Проверяем корректную работу __str__ в модели Group."""
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_models_have_correct_object_names_post(self):
        """Проверяем корректную работу __str__ в модели Post."""
        post = PostModelTest.post
        expected_object_name_text = post.text[:15]
        self.assertEqual(expected_object_name_text, str(post))

        expected_object_name_author = post.author.username
        self.assertEqual(expected_object_name_author, self.user.username)

        expected_object_name_pub_date = post.pub_date
        self.assertEqual(expected_object_name_pub_date, post.pub_date)

    def test_verbose_name_group(self):
        """Поля verbose_name в модели Group совпадает с ожидаемым."""
        group = PostModelTest.group
        field_verboses = {
            'title': 'Название группы',
            'slug': 'Строка для уникального URL-адреса',
            'description': 'Описание',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_verbose_name_post(self):
        """Поля verbose_name в модели Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'author': 'Автор',
            'group': 'Группа',
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """Поля help_text в модели Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа поста'
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
