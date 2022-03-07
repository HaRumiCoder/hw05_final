import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, User, Comment

CREATE = reverse('posts:post_create')
USERNAME = 'user'
PROFILE = reverse('posts:profile', args=[USERNAME])

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
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
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
            group=cls.group1
        )
        cls.EDIT = reverse('posts:post_edit', args=[cls.post.pk])
        cls.DETAIL = reverse('posts:post_detail', args=[cls.post.pk])
        cls.ADD_COMMENT = reverse('posts:add_comment', args=[cls.post.pk])
        cls.comment = Comment.objects.create(
            text=COMMENT_TEXT,
            author=cls.user,
            post=cls.post
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest = Client()

    def test_create_post(self):
        '''
        При отправке валидной формы со страницы создания поста
        создаётся новая запись в базе данны
        '''
        existing_posts = set(Post.objects.all())
        posts_count = Post.objects.count()
        form_data = {
            'text': NEW_POST_TEXT,
            'group': self.group1.pk,
            'image': UPLOADED_IMAGE
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
        self.assertEqual(post.author, self.user)
        post_image_name = post.image.name
        self.assertEqual(
            post_image_name[post_image_name.find('/') + 1:],
            form_data['image'].name
        )

    def test_edit_post(self):
        '''
        При отправке валидной формы со страницы редактирования поста
        происходит изменение поста в базе данных.
        '''
        posts_count = Post.objects.count()
        form_data = {
            'text': EDIT_POST_TEXT,
            'group': self.group2.pk
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

    def test_create_comment_not_for_guest(self):
        '''
        Проверка того, что гость не может создать комментарий.
        '''
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий',
        }
        response = self.guest.post(
            self.ADD_COMMENT,
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Comment.objects.count(), comments_count)
        # Проверка того, что другие комментарии не поменялись
        response = self.guest.get(self.DETAIL)
        comment = response.context["post"].comments.get(pk=self.comment.pk)
        self.assertEqual(comment.text, self.comment.text)
        self.assertEqual(comment.author, self.comment.author)

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
