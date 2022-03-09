from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User, Follow

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
FOLLOW = reverse('posts:follow_index')
PROFILE_FOLLOW = reverse('posts:profile_follow', args=[USERNAME])
PROFILE_UNFOLLOW = reverse('posts:profile_unfollow', args=[USERNAME])


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
        cls.FOLLOW_REDIRECT_GUEST = LOGIN + '?next=' + PROFILE_FOLLOW
        cls.UNFOLLOW_REDIRECT_GUEST = LOGIN + '?next=' + PROFILE_UNFOLLOW
        cls.FOLLOW_INDEX_REDIRECT_GUEST = LOGIN + '?next=' + FOLLOW
        cls.COMMENT = reverse('posts:add_comment', args=[cls.post.pk])
        cls.COMMENT_REDIRECT_GUEST = LOGIN + '?next=' + cls.COMMENT
        # гость
        cls.guest = Client()
        # авторизованный автор
        cls.author = Client()
        cls.author.force_login(cls.user)
        # обычный авторизованный
        cls.another = Client()
        cls.another.force_login(cls.not_author)

    def test_url_exists(self):
        '''Проверка доступа страниц.'''
        self.follow = Follow.objects.create(
            user=self.not_author,
            author=self.user
        )
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
            [self.POST_EDIT, self.another, 302],
            [FOLLOW, self.author, 200],
            [FOLLOW, self.guest, 302],
            [PROFILE_FOLLOW, self.author, 200],
            [PROFILE_FOLLOW, self.guest, 302],
            [PROFILE_UNFOLLOW, self.author, 404],
            [PROFILE_UNFOLLOW, self.another, 302],
            [PROFILE_UNFOLLOW, self.guest, 302],
            [self.COMMENT, self.guest, 302],
            [self.COMMENT, self.author, 302]
        ]
        for url, client, status_code in urls:
            with self.subTest(url=url, client=client):
                self.assertEqual(client.get(url).status_code, status_code)
        self.follow.delete()

    def test_url_redirects(self):
        '''Проверка перенаправления страниц.'''
        urls = [
            [CREATE, self.guest, self.CREATE_REDIRECT_GUEST],
            [self.POST_EDIT, self.guest, self.EDIT_REDIRECT_GUEST],
            [self.POST_EDIT, self.another, self.POST_DETAIL],
            [self.COMMENT, self.author, self.POST_DETAIL],
            [self.COMMENT, self.guest, self.COMMENT_REDIRECT_GUEST],
            [PROFILE_FOLLOW, self.another, PROFILE],
            [PROFILE_FOLLOW, self.guest, self.FOLLOW_REDIRECT_GUEST],
            [PROFILE_UNFOLLOW, self.another, PROFILE],
            [PROFILE_UNFOLLOW, self.guest, self.UNFOLLOW_REDIRECT_GUEST],
            [FOLLOW, self.guest, self.FOLLOW_INDEX_REDIRECT_GUEST]
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
            CREATE: 'posts/create_post.html',
            FOLLOW: 'posts/follow.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.author.get(address), template)
