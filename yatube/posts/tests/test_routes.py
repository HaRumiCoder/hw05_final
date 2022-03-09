from django.test import TestCase
from django.urls import reverse

from posts.urls import app_name

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
            ['/create/', 'post_create', []],
            [f'/posts/{POST_PK}/comment/', 'add_comment', [POST_PK]],
            ['/follow/', 'follow_index', []],
            [f'/profile/{USERNAME}/follow/', 'profile_follow', [USERNAME]],
            [f'/profile/{USERNAME}/unfollow/', 'profile_unfollow', [USERNAME]]
        ]
        for url, name, args in urls:
            with self.subTest(url=url):
                self.assertEqual(reverse(f'{app_name}:{name}', args=args), url)
