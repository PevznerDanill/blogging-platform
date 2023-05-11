from django.test import TestCase
from django.shortcuts import reverse
from app_blog.models import Post
from random import choice
from app_auth.models import Profile


class IndexViewTestCase(TestCase):
    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/blogs.json',
        'app_blog/fixtures/posts.json',
    ]

    def setUp(self) -> None:
        self.url = reverse('app_main:index')
        self.latest_posts = Post.objects.filter(is_published=True).\
        order_by('-published_at')[:5].values_list('title', flat=True)

    def test_index_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('profile'))
        for response_title, db_title in zip(response.context.get('latest_posts').values_list('title', flat=True), self.latest_posts):
            self.assertEqual(response_title, db_title)


class AboutViewTestCase(TestCase):
    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
    ]

    def setUp(self) -> None:
        self.url = reverse('app_main:about')
        self.random_profile = choice(Profile.objects.select_related('user').all())

    def test_about_view_unauthorized(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response=response,
            template_name='app_main/about.html',
        )

    def test_about_view_profile_context(self):
        self.client.force_login(user=self.random_profile.user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.context.get('profile'),
            self.random_profile
        )
        self.client.logout()


class ContactViewTestCase(TestCase):

    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
    ]

    def setUp(self) -> None:
        self.url = reverse('app_main:contacts')
        self.random_profile = choice(Profile.objects.select_related('user').all())

    def test_contacts_view_unauthorized(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response=response,
            template_name='app_main/contact.html',
        )

    def test_contacts_view_profile_context(self):
        self.client.force_login(user=self.random_profile.user)
        response = self.client.get(self.url)
        self.assertEqual(
            response.context.get('profile'),
            self.random_profile
        )
        self.client.logout()
