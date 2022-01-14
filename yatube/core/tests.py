from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        response = self.client.get('/non-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_template_error_page(self):
        response = self.client.get('/non-page/')
        self.assertTemplateUsed(response, ('core/404.html'))
