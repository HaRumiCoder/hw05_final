from django.test import TestCase

from posts.models import Group, Post, User


GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'Тестовый слаг'
GROUP_DESCRIPTION = 'Тестовое описание'
USERNAME = 'auth'
POST_TEXT = 'Тестовый текст поста'


class PostModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=POST_TEXT,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        str_expected_value = {
            self.post: self.post.text[:15],
            self.group: self.group.title
        }
        for model, expected_value in str_expected_value.items():
            with self.subTest(model=model):
                self.assertEqual(str(model), expected_value)
