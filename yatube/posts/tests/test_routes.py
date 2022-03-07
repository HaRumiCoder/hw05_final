from django.test import TestCase
from django.urls import reverse

SLUG = 'test-slug'
USERNAME = 'auth'
POST_PK = 1


class RoutesTests(TestCase):
    def test_routes(self):
        urls = [
            ['/', 'index', []],
            [f'/group/{SLUG}/', 'group_list', [SLUG]],
            [f'/profile/{USERNAME}/', 'profile', [USERNAME]],
            [f'/posts/{POST_PK}/', 'post_detail', [POST_PK]],
            [f'/posts/{POST_PK}/edit/', 'post_edit', [POST_PK]],
            ['/create/', 'post_create', []]

        ]
        for url, name, args in urls:
            with self.subTest(url=url):
                self.assertEqual(reverse(f'posts:{name}', args=args), url)
