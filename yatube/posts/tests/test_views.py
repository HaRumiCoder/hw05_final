import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Follow, Post, User
from posts.settings import POST_PER_PAGE

GROUP_TITLE = "Тестовая группа"
GROUP_SLUG = "test-slug"
GROUP_DESCRIPTION = "Тестовое описание"
POST_TEXT = "Тестовый текст поста"
GROUP_SLUG_WITHOUT_POST = "test-slug-without-post"
GROUP_TITLE_WITHOUT_POST = "Тестовая группа без поста"
USERNAME = "user"
FOLLOWER = "follower"
NON_FOLLOWER = "unfollower"

INDEX = reverse("posts:index")
GROUP_LIST = reverse("posts:group_list", args=[GROUP_SLUG])
GROUP_LIST_WITHOUT_POSTS = reverse(
    "posts:group_list",
    args=[GROUP_SLUG_WITHOUT_POST])
PROFILE = reverse("posts:profile", args=[USERNAME])
FOLLOW_INDEX = reverse("posts:follow_index")

SMALL_IMAGE = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
UPLOADED_IMAGE = SimpleUploadedFile(
    name='small_image.gif',
    content=SMALL_IMAGE,
    content_type='image/gif'
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.follower_user = User.objects.create_user(username=FOLLOWER)
        cls.non_follower_user = User.objects.create_user(username=NON_FOLLOWER)
        cls.group = Group.objects.create(
            title=GROUP_TITLE, slug=GROUP_SLUG, description=GROUP_DESCRIPTION,
        )
        cls.group_with_no_post = Group.objects.create(
            title=GROUP_TITLE_WITHOUT_POST,
            slug=GROUP_SLUG_WITHOUT_POST,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
            group=cls.group,
            image=UPLOADED_IMAGE)
        cls.POST_DETAIL = reverse("posts:post_detail", args=[cls.post.pk])
        cls.FOLLOW = reverse("posts:profile_follow", args=[cls.user.username])
        cls.UNFOLLOW = reverse(
            "posts:profile_unfollow", args=[cls.user.username])
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.follower_client = Client()
        cls.follower_client.force_login(cls.follower_user)
        cls.non_follower_client = Client()
        cls.non_follower_client.force_login(cls.non_follower_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_exists_in_context(self):
        """
        Проверка поста на страницах index,
        group_list, profile, post_detail, follow_index
        """
        pages = {INDEX, GROUP_LIST, PROFILE, self.POST_DETAIL, FOLLOW_INDEX}
        Follow.objects.create(
            user=self.follower_user,
            author=self.user
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.follower_client.get(page)
                if page == self.POST_DETAIL:
                    post = response.context["post"]
                else:
                    page_obj = response.context['page_obj']
                    self.assertEqual(len(page_obj), 1)
                    post = page_obj[0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.pk, self.post.pk)
                self.assertEqual(post.image, self.post.image)

    def test_post_not_exists_in_context(self):
        """Пост не существования поста в других страницах."""
        urls = [GROUP_LIST_WITHOUT_POSTS, FOLLOW_INDEX]
        for url in urls:
            with self.subTest(url=url):
                response = self.non_follower_client.get(url)
                self.assertNotIn(self.post, response.context["page_obj"])

    def test_group_show_correct_context(self):
        "Проверка контекста страницы post_detail."
        response = self.authorized_client.get(GROUP_LIST)
        group = response.context["group"]
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)
        self.assertEqual(group.pk, self.group.pk)

    def test_profile_show_correct_context(self):
        "Проверка контекста страницы post_detail."
        response = self.authorized_client.get(PROFILE)
        self.assertEqual(response.context["author"], self.user)

    def test_page_contains_records(self):
        """Проверка количества объектов на странице."""
        POST_PER_PAGE_2 = 3
        POST_COUNT = POST_PER_PAGE + POST_PER_PAGE_2
        Post.objects.bulk_create(
            [
                Post(
                    author=self.user,
                    text=f"Тестовый текст поста {i}",
                    group=self.group
                )
                for i in range(POST_COUNT - Post.objects.all().count())
            ]
        )
        page_and_contains = {
            INDEX: POST_PER_PAGE,
            GROUP_LIST: POST_PER_PAGE,
            PROFILE: POST_PER_PAGE,
            INDEX + "?page=2": POST_PER_PAGE_2,
            GROUP_LIST + "?page=2": POST_PER_PAGE_2,
            PROFILE + "?page=2": POST_PER_PAGE_2,
        }
        for page, contains in page_and_contains.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(len(response.context["page_obj"]), contains)

    def test_index_cache(self):
        '''Проверка кэша на странице index.'''
        response1 = self.authorized_client.get(INDEX)
        Post.objects.all().delete()
        response2 = self.authorized_client.get(INDEX)
        self.assertEqual(response1.content, response2.content)
        cache.clear()
        response3 = self.authorized_client.get(INDEX)
        self.assertNotEqual(response2.content, response3.content)

    def test_following(self):
        '''Проверка подписки на автора.'''
        followes_count = Follow.objects.count()
        self.follower_client.get(self.FOLLOW)
        self.assertEqual(followes_count + 1, Follow.objects.count())
        self.assertTrue(self.follower_user.follower.filter(author=self.user))

    def test_unfollowing(self):
        '''Проверка отписки на автора.'''
        Follow.objects.create(
            user=self.follower_user,
            author=self.user
        )
        followes_count = Follow.objects.count()
        self.follower_client.get(self.UNFOLLOW)
        self.assertEqual(followes_count - 1, Follow.objects.count())
        self.assertFalse(self.follower_user.follower.filter(author=self.user))
