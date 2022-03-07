from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User

GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
GROUP_DESCRIPTION = 'Тестовое описание'
POST_TEXT = 'Тестовый текст поста'
USERNAME = 'auth'
USERNAME_NOT_AUTHOR = 'NotAuthor'

INDEX = reverse('posts:index')
GROUP_LIST = reverse('posts:group_list', args=[GROUP_SLUG])
PROFILE = reverse('posts:profile', args=[USERNAME])
UNEXISTING_PAGE = '/unexisting_page/'
CREATE = reverse('posts:post_create')
LOGIN = reverse('users:login')


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.not_author = User.objects.create_user(username=USERNAME_NOT_AUTHOR)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
        )
        cls.POST_DETAIL = reverse('posts:post_detail', args=[cls.post.pk])
        cls.POST_EDIT = reverse('posts:post_edit', args=[cls.post.pk])
        cls.CREATE_REDIRECT_GUEST = LOGIN + '?next=' + CREATE
        cls.EDIT_REDIRECT_GUEST = LOGIN + '?next=' + cls.POST_EDIT

    def setUp(self):
        # гость
        self.guest = Client()
        # авторизованный автор
        self.author = Client()
        self.author.force_login(self.user)
        # обычный авторизованный
        self.another = Client()
        self.another.force_login(self.not_author)

    def test_url_exists(self):
        '''Проверка доступа страниц'''
        urls = [
            [INDEX, self.guest, 200],
            [GROUP_LIST, self.guest, 200],
            [PROFILE, self.guest, 200],
            [self.POST_DETAIL, self.guest, 200],
            [UNEXISTING_PAGE, self.guest, 404],
            [CREATE, self.author, 200],
            [self.POST_EDIT, self.author, 200],
            [CREATE, self.guest, 302],
            [self.POST_EDIT, self.guest, 302],
            [self.POST_EDIT, self.another, 302]
        ]
        for url, client, status_code in urls:
            with self.subTest(url=url, client=client):
                self.assertEqual(client.get(url).status_code, status_code)

    def test_url_redirects(self):
        '''Проверка перенаправления страниц'''
        urls = [
            [CREATE, self.guest, self.CREATE_REDIRECT_GUEST],
            [self.POST_EDIT, self.guest, self.EDIT_REDIRECT_GUEST],
            [self.POST_EDIT, self.another, self.POST_DETAIL]
        ]
        for url, client, finnaly_url in urls:
            with self.subTest(url=url, client=client, finnaly_url=finnaly_url):
                self.assertRedirects(client.get(url), finnaly_url)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            INDEX: 'posts/index.html',
            GROUP_LIST: 'posts/group_list.html',
            PROFILE: 'posts/profile.html',
            self.POST_DETAIL: 'posts/post_detail.html',
            self.POST_EDIT: 'posts/create_post.html',
            CREATE: 'posts/create_post.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.author.get(address), template)
