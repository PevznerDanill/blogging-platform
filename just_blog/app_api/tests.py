from random import choices
from string import ascii_letters
import json
from PIL import Image as PilImage
from rest_framework.test import APITestCase
from django.shortcuts import reverse
from rest_framework import status
from django.contrib.auth.models import User
from app_auth.models import Profile
from app_blog.models import Blog, Post, Image
import os
from django.core.files import File
from django.forms import model_to_dict


class CreateUserAPITestCase(APITestCase):

    def setUp(self) -> None:
        self.url = reverse('user-list')
        self.data = {'username': 'some-new-user', 'password': 'robot1234', 'email': 'some@email.com'}

    def test_create_user(self):
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.data.pop('password')
        self.data['id'] = 1
        self.assertJSONEqual(response.content, self.data)
        self.assertEqual(User.objects.get(pk=1).username, self.data.get('username'))


class GetTokenAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        username = ''.join(choices(ascii_letters, k=5))
        password = ''.join(choices(ascii_letters, k=9))
        cls.user = User.objects.create_user(username=username, password=password)
        cls.url = reverse('login')
        cls.data = {'username': username, 'password': password}

    def test_get_token(self):
        response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = json.loads(response.content)
        self.assertIn('auth_token', response_data)


class ActivateTokenAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        username = ''.join(choices(ascii_letters, k=5))
        password = ''.join(choices(ascii_letters, k=9))
        cls.user = User.objects.create_user(username=username, password=password)
        cls.login_url = reverse('login')
        cls.login_data = {'username': username, 'password': password}

        cls.url_to_user_list = reverse('user-list')

    def setUp(self) -> None:
        token_response = self.client.post(self.login_url, self.login_data, format='json')
        token = 'Token {token}'.format(
            token=json.loads(token_response.content).get('auth_token')
        )
        self.client.credentials(HTTP_AUTHORIZATION=token)

    def test_token_activation(self):
        response = self.client.get(self.url_to_user_list)
        response_to_python = json.loads(response.content)
        self.assertTrue(len(response_to_python.get('results')) == 1)
        self.assertEqual(
            response_to_python.get('results')[0].get('username'),
            User.objects.first().username)


class ProfileListAPITestCase(APITestCase):

    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/posts.json',
        'app_blog/fixtures/blogs.json',
    ]

    def setUp(self) -> None:
        self.url = reverse('app_api:profile_list')

    def test_profile_list_api(self):
        response = self.client.get(self.url)
        response_to_python = json.loads(response.content)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        total_objects = 0

        while True:
            new_url = response_to_python.get('next')
            objects_per_page = len(response_to_python.get('results'))
            total_objects += objects_per_page
            if new_url:
                response = self.client.get(new_url)
                response_to_python = json.loads(response.content)
            else:
                break

        self.assertEqual(total_objects, Profile.objects.count())


class ProfileCreateAPITestCase(APITestCase):
    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
    ]

    @classmethod
    def setUpTestData(cls):
        username = ''.join(choices(ascii_letters, k=5))
        password = ''.join(choices(ascii_letters, k=9))
        cls.user = User.objects.create_user(username=username, password=password)

    def setUp(self) -> None:
        self.url = reverse('app_api:new_profile')

    def test_profile_create(self):
        self.client.force_authenticate(user=self.user)
        current_profiles_num = Profile.objects.count()
        first_response = self.client.post(self.url)
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(current_profiles_num + 1 == Profile.objects.count())

        second_response = self.client.post(self.url)
        self.assertEqual(second_response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_unauthorized_create_profile(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileUpdateAPITestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        username = ''.join(choices(ascii_letters, k=5))
        password = ''.join(choices(ascii_letters, k=9))
        cls.user = User.objects.create_user(username=username, password=password)

        bad_username = username + '0'
        cls.bad_user = User.objects.create_user(username=bad_username, password=password)

        image = PilImage.new('RGB', (100, 100))
        cls.path_to_test_image = os.path.join(os.curdir, 'test-image.jpg')
        image.save(cls.path_to_test_image)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.user.delete()
        cls.bad_user.delete()
        os.remove(cls.path_to_test_image)

    def setUp(self) -> None:
        self.client.force_authenticate(user=self.user)
        new_profile_response = self.client.post(reverse('app_api:new_profile'))
        new_profile_id = json.loads(new_profile_response.content).get('id')
        self.url = reverse('app_api:profile_update', kwargs={'pk': new_profile_id})
        self.test_bio = 'some bio'

        self.test_age = '1992-08-12'

    def test_profile_put(self):
        put_response = self.client.put(self.url, {'bio': self.test_bio}, format='json')
        self.assertEqual(put_response.status_code, status.HTTP_200_OK)
        updated_profile = Profile.objects.get(user=self.user)
        self.assertEqual(updated_profile.bio, self.test_bio)
        self.assertContains(put_response, self.test_bio)

    def test_profile_patch(self):
        patch_response = self.client.patch(self.url, {'age': self.test_age}, format='json')
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertContains(patch_response, self.test_age)

        with open(self.path_to_test_image, 'rb') as file:
            image_upload_patch_response = self.client.patch(self.url, {'avatar': file}, format='multipart')
        self.assertContains(image_upload_patch_response, 'test-image')
        updated_profile = Profile.objects.get(user=self.user)
        self.assertIsNotNone(updated_profile.avatar)
        self.client.logout()

    def test_unauthorized_get(self):
        unauthorized_response = self.client.get(self.url)
        self.assertEqual(unauthorized_response.status_code, status.HTTP_200_OK)
        updated_profile = Profile.objects.get(user=self.user)
        response_to_python = json.loads(unauthorized_response.content)
        bio_from_response = response_to_python.get('bio')
        self.assertEqual(bio_from_response, updated_profile.bio)

    def test_forbidden_update(self):
        self.client.force_authenticate(user=self.bad_user)

        forbidden_put_response = self.client.put(self.url, {'bio': 'some new bio'}, format='json')
        self.assertEqual(forbidden_put_response.status_code, status.HTTP_403_FORBIDDEN)

        forbidden_patch_response = self.client.patch(self.url, {'bio': 'some new bio'}, format='json')
        self.assertEqual(forbidden_patch_response.status_code, status.HTTP_403_FORBIDDEN)


class BlogCreateAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        username = ''.join(choices(ascii_letters, k=5))
        password = ''.join(choices(ascii_letters, k=9))
        cls.user = User.objects.create_user(username=username, password=password)
        cls.profile = Profile(user=cls.user)
        cls.profile.save()

    def setUp(self) -> None:
        self.url = reverse('app_api:new_blog')
        self.data = {'title': 'some title', 'description': 'some description'}

    def test_blog_create(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.data, format='json')
        self.data['id'] = 1
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertJSONEqual(response.content, self.data)
        self.assertTrue(self.profile.blogs.count() == 1)
        self.client.logout()
        self.data.pop('id')

    def test_unauthorized_blog_create(self):
        unauthorized_response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(unauthorized_response.status_code, status.HTTP_401_UNAUTHORIZED)


class BlogDetailAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        username = ''.join(choices(ascii_letters, k=5))
        password = ''.join(choices(ascii_letters, k=9))
        cls.user = User.objects.create_user(username=username, password=password)
        cls.profile = Profile(user=cls.user)
        cls.bad_user = User.objects.create_user(username=f'{username}09', password=f'{password}09')
        Profile.objects.create(user=cls.bad_user)
        cls.profile.save()
        cls.new_blog = Blog(
            profile=cls.profile,
            title='test title',
            description='test description'
        )
        cls.new_blog.save()

    def setUp(self) -> None:
        self.url = reverse('app_api:blog_detail', kwargs={'pk': self.new_blog.pk})
        self.test_title = 'new test title'
        self.test_description = 'new test description'
        self.expected_data = {
            "id": 1,
            "title": "test title",
            "description": "test description",
            "posts": [],
            "profile": {"id": self.profile.pk, "username": self.user.username}
        }

    def test_blog_detail_get(self):
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(get_response.content, self.expected_data)

    def test_blog_detail_update(self):
        self.client.force_authenticate(user=self.user)
        put_response = self.client.put(self.url, {'title': self.test_title}, format='json')
        self.assertEqual(put_response.status_code, status.HTTP_200_OK)
        self.expected_data['title'] = self.test_title
        self.assertJSONEqual(put_response.content, self.expected_data)

        patch_response = self.client.patch(
            self.url,
            {'description': self.test_description},
            format='json'
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.expected_data['description'] = self.test_description
        self.assertJSONEqual(patch_response.content, self.expected_data)
        self.client.logout()

    def test_unauthorized_blog_update(self):
        unauthorized_put_response = self.client.put(
            self.url,
            {'title': self.test_title + '99'},
            format='json'
            )
        self.assertEqual(unauthorized_put_response.status_code, status.HTTP_401_UNAUTHORIZED)

        unauthorized_patch_response = self.client.patch(
            self.url,
            {'title': self.test_title + '99'},
            format='json'
            )
        self.assertEqual(unauthorized_patch_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blog_forbidden_update_delete(self):
        self.client.force_authenticate(user=self.bad_user)
        forbidden_put_response = self.client.put(
            self.url,
            {'title': self.test_title + '99'},
            format='json'
        )
        self.assertEqual(forbidden_put_response.status_code, status.HTTP_403_FORBIDDEN)

        forbidden_patch_response = self.client.patch(
            self.url,
            {'title': self.test_title + '99'},
            format='json'
        )
        self.assertEqual(forbidden_patch_response.status_code, status.HTTP_403_FORBIDDEN)

        forbidden_delete_response = self.client.delete(self.url)
        self.assertEqual(forbidden_delete_response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_blog_update_delete(self):
        self.client.force_authenticate(user=self.user)
        delete_response = self.client.delete(self.url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Blog.objects.filter(pk=self.new_blog.pk).exists())


class BlogListAPITestCase(APITestCase):
    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/posts.json',
        'app_blog/fixtures/blogs.json',
    ]

    def setUp(self) -> None:
        self.url = reverse('app_api:blog_list')

    def test_blog_list(self):
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        first_blog_title = Blog.objects.first().title
        self.assertContains(get_response, first_blog_title)

        response_to_python = json.loads(get_response.content)
        total_objects = 0

        while True:
            new_url = response_to_python.get('next')
            objects_per_page = len(response_to_python.get('results'))
            total_objects += objects_per_page
            if new_url:
                response = self.client.get(new_url)
                response_to_python = json.loads(response.content)
            else:
                break

        self.assertEqual(total_objects, Blog.objects.count())


class PostCreateAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        username = ''.join(choices(ascii_letters, k=5))
        password = ''.join(choices(ascii_letters, k=9))
        cls.user = User.objects.create_user(username=username, password=password)
        profile = Profile(user=cls.user)
        profile.save()

        bad_user = User.objects.create_user(username=f'{username}09', password=f'{password}09')
        bad_profile = Profile(user=bad_user)
        bad_profile.save()

        cls.blog = Blog(
            profile=profile,
            title='test title',
            description='test description'
        )
        cls.blog.save()

        cls.bad_blog = Blog(
            profile=bad_profile,
            title='test bad title',
            description='test bad description'
        )
        cls.bad_blog.save()

    def setUp(self) -> None:
        self.url = reverse('app_api:new_post')
        self.client.force_authenticate(user=self.user)
        self.data = {
            'title': 'test post title',
            'tag': 'test post tag',
            'blog': self.blog.pk,
            'content': 'some post content'
        }

    def test_post_create(self):
        post_response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)
        expected_data = self.data.copy()
        expected_data['id'] = 1
        self.assertJSONEqual(post_response.content, expected_data)
        self.assertTrue(Post.objects.first().title == 'test post title')

    def test_post_create_bad(self):
        self.data['blog'] = self.bad_blog.pk
        bad_post_response = self.client.post(self.url, self.data, format='json')
        self.assertEqual(bad_post_response.status_code, status.HTTP_400_BAD_REQUEST)


class PostUpdateAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        username = ''.join(choices(ascii_letters, k=5))
        password = ''.join(choices(ascii_letters, k=9))
        cls.user = User.objects.create_user(username=username, password=password)
        profile = Profile(user=cls.user)
        profile.save()

        blog = Blog(
            profile=profile,
            title='test blog title',
            description='test blog description'
        )
        blog.save()

        cls.post = Post(
            profile=profile,
            blog=blog,
            title='test post title',
            tag='test post tag',
            content='testing content post'
        )
        cls.post.save()

        cls.bad_user = User.objects.create_user(username=f'{username}09', password=f'{password}09')
        Profile.objects.create(user=cls.bad_user)

    def setUp(self) -> None:
        self.url = reverse('app_api:post_detail', kwargs={'pk': self.post.pk})

    def test_post_update_get_not_publish(self):
        not_published_get_response = self.client.get(self.url)
        self.assertEqual(not_published_get_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_update_get(self):
        self.post.publish()
        published_get_response = self.client.get(self.url)
        self.assertContains(published_get_response, 'testing content post')
        self.assertEqual(published_get_response.status_code, status.HTTP_200_OK)

    def test_post_update_unauthorized_delete(self):
        unauthorized_delete_response = self.client.delete(self.url)
        self.assertEqual(unauthorized_delete_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_update_forbidden_delete(self):
        self.client.force_authenticate(user=self.bad_user)
        forbidden_delete_response = self.client.delete(self.url)
        self.assertEqual(forbidden_delete_response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_post_update(self):
        self.client.force_authenticate(user=self.user)
        self.client.put(self.url, {'is_published': False}, format='json')
        self.assertFalse(Post.objects.get(pk=self.post.pk).created_at is None)
        self.client.patch(self.url, {'is_published': True}, format='json')
        self.assertFalse(Post.objects.get(pk=self.post.pk).created_at is None)


class ImageCreateAPITestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        username = ''.join(choices(ascii_letters, k=5))
        password = ''.join(choices(ascii_letters, k=9))
        cls.user = User.objects.create_user(username=username, password=password)
        profile = Profile(user=cls.user)
        profile.save()

        blog = Blog(
            profile=profile,
            title='test blog title',
            description='test blog description'
        )
        blog.save()

        cls.post = Post(
            profile=profile,
            blog=blog,
            title='test post title',
            tag='test post tag',
            content='testing content post'
        )
        cls.post.save()

        bad_user = User.objects.create_user(username=f'{username}09', password=f'{password}09')
        bad_profile = Profile(user=bad_user)
        bad_profile.save()

        bad_blog = Blog(
            profile=bad_profile,
            title='test bad blog title',
            description='test bad blog description'
        )
        bad_blog.save()

        cls.bad_post = Post(
            profile=bad_profile,
            blog=bad_blog,
            title='test bad post title',
            tag='test bad post tag',
            content='testing bad content post'
        )
        cls.bad_post.save()

        image = PilImage.new('RGB', (100, 100))
        cls.path_to_test_image = os.path.join(os.curdir, 'test-image.jpg')
        image.save(cls.path_to_test_image)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.user.delete()
        cls.post.delete()
        cls.bad_post.delete()
        os.remove(cls.path_to_test_image)

    def setUp(self) -> None:
        self.url = reverse('app_api:new_image')

    def test_image_create_unauthorized(self):
        with open(self.path_to_test_image, 'rb') as image:
            unauthorized_response = self.client.post(
                self.url,
                {'title': 'some title', 'image': image, 'post': self.post.pk},
                format='multipart'
            )
        self.assertEqual(unauthorized_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_image_create(self):
        self.client.force_authenticate(user=self.user)
        with open(self.path_to_test_image, 'rb') as image:
            post_response = self.client.post(
                self.url,
                {'title': 'some title', 'image': image, 'post': self.post.pk},
                format='multipart'
            )
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Image.objects.first().title, 'some title')
        self.client.logout()

    def test_image_create_bad(self):
        self.client.force_authenticate(user=self.user)
        with open(self.path_to_test_image, 'rb') as image:
            bad_post_response = self.client.post(
                self.url,
                {'title': 'some new title', 'image': image, 'post': self.bad_post.pk},
                format='multipart'
            )
        self.assertEqual(bad_post_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.client.logout()

class ImageDetailAPITestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        username = ''.join(choices(ascii_letters, k=5))
        password = ''.join(choices(ascii_letters, k=9))
        cls.user = User.objects.create_user(username=username, password=password)
        profile = Profile(user=cls.user)
        profile.save()

        blog = Blog(
            profile=profile,
            title='test blog title',
            description='test blog description'
        )
        blog.save()

        post = Post(
            profile=profile,
            blog=blog,
            title='test post title',
            tag='test post tag',
            content='testing content post'
        )
        post.save()

        image = PilImage.new('RGB', (100, 100))
        cls.path_to_test_image = os.path.join(os.curdir, 'test-image.jpg')
        image.save(cls.path_to_test_image)

        test_image = PilImage.new('RGB', (100, 100))
        cls.path_to_sec_test_image = os.path.join(os.curdir, 'sec-test-image.jpg')
        test_image.save(cls.path_to_sec_test_image)

        with open(cls.path_to_test_image, 'rb') as file:
            cls.image = Image(
                title='some test title',
                image=File(file),
                post=post
            )

            cls.image.save()

        cls.bad_user = User.objects.create_user(username=f'{username}09', password=f'{password}09')
        Profile.objects.create(user=cls.bad_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.user.delete()
        cls.bad_user.delete()
        cls.image.delete()
        os.remove(cls.path_to_test_image)
        os.remove(cls.path_to_sec_test_image)

    def setUp(self) -> None:
        self.url = reverse('app_api:image_detail', kwargs={'pk': self.image.pk})

    def test_image_detail(self):
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertContains(get_response, 'test-image')

    def test_image_detail_unauthorized_delete(self):
        unauthorized_response = self.client.delete(self.url)
        self.assertEqual(unauthorized_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_image_detail_forbidden_delete(self):
        self.client.force_authenticate(user=self.bad_user)
        forbidden_response = self.client.delete(self.url)
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

    def test_image_detail_put(self):
        self.client.force_authenticate(user=self.user)
        put_response = self.client.put(self.url, {'title': 'testing title'}, format='multipart')
        self.assertEqual(put_response.status_code, status.HTTP_200_OK)
        self.assertEqual(Image.objects.get(pk=self.image.pk).title, 'testing title')
        self.client.logout()

    def test_image_detail_patch(self):
        self.client.force_authenticate(user=self.user)
        with open(self.path_to_sec_test_image, 'rb') as new_image:
            patch_response = self.client.patch(self.url, {'image': new_image}, format='multipart')
        self.assertContains(patch_response, 'sec-test-image')
        self.client.logout()

    def test_image_detail_delete(self):
        self.client.force_authenticate(user=self.user)
        self.client.delete(self.url)
        self.assertFalse(Image.objects.all().exists())
        self.client.logout()


class PostListAPITestCase(APITestCase):

    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/posts.json',
        'app_blog/fixtures/blogs.json',
        'app_blog/fixtures/images.json',
    ]

    def setUp(self) -> None:
        self.url = reverse('app_api:post_list')

    def test_post_list(self):
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        response_to_python = json.loads(get_response.content)
        results = response_to_python.get('results')
        all_published = all(result['is_published'] for result in results)
        self.assertTrue(all_published)

        posts_in_db = Post.objects.filter(is_published=True).count()

        if posts_in_db < 20:
            self.assertEqual(posts_in_db, len(results))

        else:
            total_objects = 0

            while True:
                new_url = response_to_python.get('next')
                objects_per_page = len(response_to_python.get('results'))
                total_objects += objects_per_page
                if new_url:
                    response = self.client.get(new_url)
                    response_to_python = json.loads(response.content)
                else:
                    break

            self.assertEqual(total_objects, posts_in_db.count())
