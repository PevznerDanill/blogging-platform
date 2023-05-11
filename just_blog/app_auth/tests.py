from django.test import TestCase
from django.shortcuts import reverse
from string import ascii_letters
from random import choices, random, randint
from django.contrib.auth.models import User
from app_auth.models import Profile
from PIL import Image as PilImage
import os
from datetime import date, timedelta


class GetStartedViewTestCase(TestCase):

    def setUp(self) -> None:
        self.url = reverse('app_auth:get_started')
        self.username = ''.join(choices(ascii_letters, k=8))
        self.password = ''.join(choices(ascii_letters, k=8))

    def test_get_started(self):
        post_response = self.client.post(
            self.url,
            {
             "username": self.username,
             "password1": self.password,
             "password2": self.password,
            }
        )

        self.assertEqual(post_response.status_code, 302)
        self.assertIn('profile-update/1/', post_response.url)
        self.assertTrue(
            User.objects.filter(username=self.username).exists()
        )
        self.assertTrue(
            Profile.objects.filter(user__username=self.username).exists()
        )

        self.client.logout()

    def test_bad_get_started(self):
        User.objects.create_user(username=self.username, password=self.password)
        bad_response = self.client.post(
            self.url,
            {
                "username": self.username,
                "password1": self.password,
                "password2": self.password,
            }
        )

        self.assertContains(bad_response, 'errorlist')


class UpdateViewTestCase(TestCase):
    def get_age(self, random_date):
        today = date.today()
        birthdate = random_date
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        username = ''.join(choices(ascii_letters, k=8))
        password = ''.join(choices(ascii_letters, k=8))
        cls.user = User.objects.create_user(username=username, password=password)
        new_profile = Profile(user=cls.user)
        new_profile.save()
        cls.profile = new_profile

        cls.bad_user = User.objects.create_user(
            username=''.join(choices(ascii_letters, k=8)),
            password=password
        )
        bad_profile = Profile(user=cls.bad_user)
        bad_profile.save()
        cls.bad_profile = bad_profile

        image = PilImage.new('RGB', (100, 100))
        cls.path_to_test_image = os.path.join(os.curdir, 'test-image.jpg')
        image.save(cls.path_to_test_image)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.user.delete()
        cls.bad_user.delete()
        cls.profile.delete()
        cls.bad_profile.delete()
        os.remove(cls.path_to_test_image)

    def setUp(self) -> None:
        self.url = reverse('app_auth:profile_update', kwargs={'pk': self.profile.pk})
        random_range = randint(1, 100)
        today = date.today()
        many_years_ago = today - timedelta(days=365*random_range)
        random_date = today - (today - many_years_ago) * random()
        self.age = self.get_age(random_date)
        self.data = {
            "first_name": ''.join(choices(ascii_letters, k=8)),
            "last_name": ''.join(choices(ascii_letters, k=8)),
            "email": 'email@email.com',
            "bio": ''.join(choices(ascii_letters, k=50)),
            "age_day": str(random_date.day),
            "age_month": str(random_date.month),
            "age_year": str(random_date.year),
        }

    def test_update_profile(self):
        self.client.force_login(user=self.user)
        post_response = self.client.post(self.url, self.data)
        self.assertRedirects(
            post_response, reverse('app_auth:profile_detail', kwargs={'pk': self.profile.pk})
        )
        self.user.refresh_from_db()
        self.profile.refresh_from_db()

        for key, value in self.data.items():
            if hasattr(self.user, key):
                self.assertEqual(getattr(self.user, key), value)
            elif hasattr(self.profile, key):
                self.assertEqual(getattr(self.profile, key), value)
        self.assertEqual(self.profile.get_age(), self.age)
        self.client.logout()

    def test_upload_avatar(self):
        self.client.force_login(user=self.user)
        with open(self.path_to_test_image, 'rb') as file:
            self.client.post(self.url, {'avatar': file})
        self.profile.refresh_from_db(fields=['avatar'])
        self.assertIsNotNone(self.profile.avatar)
        self.client.logout()

    def test_forbidden_update(self):
        self.client.force_login(user=self.bad_user)
        forbidden_post = self.client.post(
            self.url,
            {"email": 'new_email@email.com'}
        )
        self.assertEqual(forbidden_post.status_code, 403)
        self.client.logout()

    def test_unauthorized_update(self):
        unauthorized_post = self.client.post(
            self.url,
            {"bio": "test new bio"}
        )
        self.assertEqual(unauthorized_post.status_code, 302)
        self.assertRedirects(unauthorized_post, reverse('app_auth:login') + '?next=/users/profile-update/1/')


class MyLoginViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        username = ''.join(choices(ascii_letters, k=8))
        password = ''.join(choices(ascii_letters, k=8))
        cls.user = User.objects.create_user(username=username, password=password)
        new_profile = Profile(user=cls.user)
        new_profile.save()
        cls.profile = new_profile
        cls.data = {
            "username": username,
            "password": password,
        }

    def setUp(self) -> None:
        self.url = reverse('app_auth:login')

    def test_login(self):
        response = self.client.post(
            self.url, self.data
        )
        self.assertRedirects(
            response,
            reverse('app_auth:profile_detail', kwargs={'pk': self.profile.pk})
        )
        self.client.logout()

    def test_login_wrong_credentials(self):
        response = self.client.post(
            self.url,
            {
                "username": self.data['username'],
                "password": self.data['password'] + 'nono'
            }
        )
        self.assertContains(response, 'errorlist')


class MyLogoutViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        username = ''.join(choices(ascii_letters, k=8))
        password = ''.join(choices(ascii_letters, k=8))
        cls.user = User.objects.create_user(username=username, password=password)
        new_profile = Profile(user=cls.user)
        new_profile.save()
        cls.profile = new_profile

    def setUp(self) -> None:
        self.url = reverse('app_auth:logout')

    def test_logout(self):
        self.client.force_login(user=self.user)
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('app_main:index'))

        unauthorized_response = self.client.get(
            reverse('app_auth:profile_detail', kwargs={'pk': self.profile.pk})
        )
        self.assertRedirects(
            unauthorized_response,
            reverse('app_auth:login') + f'?next=/users/profile-details/{self.profile.pk}/'
        )
        self.client.logout()


class ProfileDetailViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        username = ''.join(choices(ascii_letters, k=8))
        password = ''.join(choices(ascii_letters, k=8))
        cls.user = User.objects.create_user(username=username, password=password)
        new_profile = Profile(user=cls.user)
        new_profile.save()
        cls.profile = new_profile

        cls.bad_user = User.objects.create_user(
            username=username + '09abc',
            password=password
        )
        Profile.objects.create(user=cls.bad_user)

    def setUp(self) -> None:
        self.url = reverse('app_auth:profile_detail', kwargs={'pk': self.profile.pk})

    def test_profile_details(self):
        self.client.force_login(user=self.user)
        response = self.client.get(self.url)
        self.assertContains(response, self.user.username)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_profile_details_forbidden(self):
        self.client.force_login(user=self.bad_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()


class ProfilePublicViewTestCase(TestCase):
    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/posts.json',
        'app_blog/fixtures/blogs.json',
    ]

    def setUp(self) -> None:
        self.random_profile = Profile.objects.order_by('?').first()
        self.url = reverse('app_auth:profile_public', kwargs={'pk': self.random_profile.pk})

    def test_profile_public(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.random_profile.user.username)





















