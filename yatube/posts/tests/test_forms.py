import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.models import Post, Group, User, Comment

USERNAME_NOT_AUTHOR = 'NotAuthor'
USERNAME = 'user'
CREATE = reverse('posts:post_create')
PROFILE = reverse('posts:profile', args=[USERNAME])
LOGIN = reverse('users:login')
POST_TEXT = 'Текстовый текст'
NEW_POST_TEXT = 'Новый тестовый тект'
EDIT_POST_TEXT = 'Изменённый тестовый текст'
GROUP_TITLE1 = 'Тестовая группа1'
SLUG1 = 'test-slug1'
GROUP_TITLE2 = 'Тестовая группа2'
SLUG2 = 'test-slug2'
GROUP_DESCRIPTION = 'Тестовое описание'
COMMENT_TEXT = 'Тестовый комментарий'
NEW_COMMENT_TEXT = 'Новый тестовый комментарий'
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
UPLOADED_IMAGE2 = SimpleUploadedFile(
    name='small_image2.gif',
    content=SMALL_IMAGE,
    content_type='image/gif'
)
UPLOADED_IMAGE3 = SimpleUploadedFile(
    name='small_image3.gif',
    content=SMALL_IMAGE,
    content_type='image/gif'
)
UNEDITED_TEXT = 'Нередактируемый пост'
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.not_author = User.objects.create_user(username=USERNAME_NOT_AUTHOR)
        cls.group1 = Group.objects.create(
            title=GROUP_TITLE1,
            slug=SLUG1,
            description=GROUP_DESCRIPTION,
        )
        cls.group2 = Group.objects.create(
            title=GROUP_TITLE2,
            slug=SLUG2,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
            group=cls.group1,
            image=UPLOADED_IMAGE
        )
        cls.EDIT = reverse('posts:post_edit', args=[cls.post.pk])
        cls.DETAIL = reverse('posts:post_detail', args=[cls.post.pk])
        cls.ADD_COMMENT = reverse('posts:add_comment', args=[cls.post.pk])
        cls.CREATE_POST_REDIRECT_GUEST = f'{LOGIN}?next={CREATE}'
        cls.COMMENT_REDIRECT_GUEST = f'{LOGIN}?next={cls.ADD_COMMENT}'
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.not_author)

    def setUp(self):
        self.guest = Client()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        '''
        При отправке валидной формы со страницы создания поста
        создаётся новая запись в базе данных.
        '''
        existing_posts = set(Post.objects.all())
        posts_count = Post.objects.count()
        form_data = {
            'text': NEW_POST_TEXT,
            'group': self.group1.pk,
            'image': UPLOADED_IMAGE3
        }
        response = self.authorized_client.post(
            CREATE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, PROFILE)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        posts = set(Post.objects.all()) - existing_posts
        self.assertEqual(len(posts), 1)
        post = posts.pop()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(
            post.image.name.split('/')[-1],
            form_data['image'].name
        )

    def test_guest_can_not_create_post(self):
        '''
        При отправке формы со страницы создания поста
        гость не создаёт новую запись в базе данных.
        '''
        existing_posts = set(Post.objects.all())
        form_data = {
            'text': NEW_POST_TEXT,
            'group': self.group1.pk,
            'image': UPLOADED_IMAGE
        }
        response = self.guest.post(
            CREATE,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.CREATE_POST_REDIRECT_GUEST)
        self.assertEqual(existing_posts, set(Post.objects.all()))

    def test_edit_post(self):
        '''
        При отправке валидной формы со страницы редактирования поста
        происходит изменение поста в базе данных.
        '''
        posts_count = Post.objects.count()
        form_data = {
            'text': EDIT_POST_TEXT,
            'group': self.group2.pk,
            'image': UPLOADED_IMAGE2
        }
        response = self.authorized_client.post(
            self.EDIT,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.DETAIL)
        self.assertEqual(Post.objects.count(), posts_count)
        post = response.context['post']
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.pk, form_data['group'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(
            post.image.name.split('/')[-1],
            form_data['image'].name
        )

    def test_guest_and_another_can_not_edit_post(self):
        '''
        При отправке валидной формы со страницы редактирования поста
        гость и не автор не измененяют пост в базе данных.
        '''
        form_data = {
            'text': EDIT_POST_TEXT,
            'group': self.group2.pk,
            'image': UPLOADED_IMAGE2
        }
        clients = [
            [self.guest, f'{LOGIN}?next={self.EDIT}'],
            [self.another, self.DETAIL]
        ]
        for client, redirect in clients:
            with self.subTest(client=client):
                response = client.post(
                    self.EDIT,
                    data=form_data,
                    follow=True
                )
                self.assertRedirects(response, redirect)
                post = Post.objects.get(pk=self.post.pk)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)

    def test_pages_show_correct_form(self):
        "Проверка формы страниц"
        urls = [
            CREATE,
            self.EDIT
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                form = response.context.get('form')
                self.assertIsInstance(form.fields.get('text'), forms.CharField)
                self.assertIsInstance(form.fields.get('group'), (
                    forms.models.ModelChoiceField))

    def test_guest_can_not_create_comment(self):
        '''
        Проверка того, что гость не может создать комментарий.
        '''
        existing_comments = set(Comment.objects.all())
        form_data = {
            'text': 'Комментарий',
        }
        response = self.guest.post(
            self.ADD_COMMENT,
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(existing_comments, set(Comment.objects.all()))

    def test_create_comment(self):
        '''
        При отправке валидной формы со страницы отправки комментария
        создаётся новый комментарий.
        '''
        existing_comments = set(Comment.objects.all())
        comments_count = Comment.objects.count()
        form_data = {
            'text': NEW_COMMENT_TEXT}
        response = self.authorized_client.post(
            self.ADD_COMMENT,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.DETAIL)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        comments = set(Comment.objects.all()) - existing_comments
        self.assertEqual(len(comments), 1)
        comment = comments.pop()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)
