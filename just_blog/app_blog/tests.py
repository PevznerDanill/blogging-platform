import bs4
from django.test import TestCase
from django.shortcuts import reverse
from app_auth.models import Profile
from app_blog.models import Blog, Post, Image
from django.contrib.auth.models import User
from string import ascii_letters
from random import choice, choices
from bs4 import BeautifulSoup
import re
from django.db.models import Q
from PIL import Image as PilImage
import os
import csv
from contextlib import ExitStack


class UserBlogListViewTestCase(TestCase):
    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/posts.json',
        'app_blog/fixtures/blogs.json',
    ]

    def setUp(self) -> None:
        profiles_with_blogs = Profile.objects.select_related('user').\
            prefetch_related('blogs', 'posts').filter(blogs__isnull=False)
        self.random_profile = choice(profiles_with_blogs)
        self.url = reverse('app_blog:user_blog_list', kwargs={'pk': self.random_profile.pk})

    def test_user_blog_list_content(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'lxml')
        main_title = soup.find('h1', {'class': "blogs__title title"}).text
        username = main_title[:main_title.index(':')]
        displayed_blogs = soup.find_all('li', {'class': "blog__card flex"})

        self.assertEqual(username, self.random_profile.user.username)
        self.assertEqual(
            len(displayed_blogs),
            self.random_profile.blogs.count()
        )

    def test_user_blog_list_template(self):
        response = self.client.get(self.url)
        template_name = 'app_blog/user_blog_list.html'
        self.assertTemplateUsed(response, template_name)


class BlogCreateViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        username = ''.join(choices(ascii_letters, k=8))
        password = ''.join(choices(ascii_letters, k=8))
        cls.user = User.objects.create_user(username=username, password=password)
        Profile.objects.create(user=cls.user)

    def setUp(self) -> None:
        self.url = reverse('app_blog:blog_new')
        self.blog_data = {
            'description': 'test blog description',
            'title': 'test blog title'
        }

    def test_blog_create_view_content(self):
        self.client.force_login(user=self.user)
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, 200)
        self.assertTemplateUsed(get_response, 'app_blog/blog_new.html')
        self.client.logout()

    def test_blog_create(self):
        self.client.force_login(user=self.user)
        post_response = self.client.post(self.url, self.blog_data)

        new_blog = Blog.objects.filter(title=self.blog_data.get('title'))
        self.assertTrue(new_blog.exists())

        self.assertRedirects(
            post_response,
            reverse('app_blog:blog_detail', kwargs={'pk': new_blog[0].pk})
        )
        self.client.logout()

    def test_blog_create_unauthorized(self):
        unauthorized_response = self.client.post(self.url, self.blog_data)
        self.assertRedirects(
            unauthorized_response,
            reverse('app_auth:login') + f'?next={self.url}'
        )


class BlogDetailViewTestCase(TestCase):

    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/blogs.json',
        'app_blog/fixtures/posts.json',
    ]

    def setUp(self) -> None:
        blogs = Blog.objects.select_related('profile').prefetch_related('posts').all()
        self.random_blog = choice(blogs)
        self.url = reverse('app_blog:blog_detail', kwargs={'pk': self.random_blog.pk})

        self.user = self.random_blog.profile.user

        self.unsafe_links = set()
        self.unsafe_links.add(reverse('app_blog:blog_edit', kwargs={'pk': self.random_blog.pk}))
        self.unsafe_links.add(reverse('app_blog:post_new', kwargs={'pk': self.random_blog.pk}))
        self.unsafe_links.add(reverse('app_blog:blog_delete', kwargs={'pk': self.random_blog.pk}))

    def test_blog_detail_unauthorized(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        soup = bs4.BeautifulSoup(response.content, 'lxml')
        posts_displayed = len(soup.find_all('li', {'class': 'blog__card flex'}))
        pub_posts = Post.objects.filter(Q(blog=self.random_blog) & Q(is_published=True)).count()
        self.assertEqual(posts_displayed, pub_posts)

        for link in self.unsafe_links:
            self.assertNotContains(response, link)

    def test_blog_detail(self):
        self.client.force_login(user=self.user)
        response = self.client.get(self.url)

        for link in self.unsafe_links:
            self.assertContains(response, link)


class BlogDeleteViewTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        username = ''.join(choices(ascii_letters, k=8))
        password = ''.join(choices(ascii_letters, k=8))
        cls.user = User.objects.create_user(username=username, password=password)
        profile = Profile(user=cls.user)
        profile.save()
        cls.profile = profile

        title = ''.join(choices(ascii_letters, k=128))
        description = ''.join(choices(ascii_letters, k=256))

        blog = Blog(profile=profile, title=title, description=description)
        blog.save()
        cls.blog = blog

        cls.bad_user = User.objects.create_user(username=f'{username}bad', password=password)
        Profile.objects.create(user=cls.bad_user)

    def setUp(self) -> None:
        self.url = reverse('app_blog:blog_delete', kwargs={'pk': self.blog.pk})

    def test_blog_delete_forbidden(self):
        self.client.force_login(user=self.bad_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

    def test_blog_delete_unauthorized(self):
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse('app_auth:login') + f'?next={self.url}'
        )

    def test_blog_delete_get(self):
        self.client.force_login(user=self.user)
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.context.get('profile'), self.profile)
        soup = bs4.BeautifulSoup(get_response.content, 'lxml')
        title = soup.find('h1', {'class': 'title'}).text
        pattern = f'{self.blog.title}'
        search = re.search(pattern, title)
        self.assertEqual(self.blog.title, search.group())
        self.client.logout()

    def test_blog_delete_post(self):
        self.client.force_login(user=self.user)
        get_response_0 = self.client.get(self.url)
        soup_0 = bs4.BeautifulSoup(get_response_0.content, 'lxml')
        name = 'csrfmiddlewaretoken'
        input_tag_0 = soup_0.find('input', {'name': name})
        input_value = input_tag_0.get('value')
        post_response = self.client.post(self.url, {name: input_value})
        self.assertRedirects(
            post_response,
            reverse('app_blog:user_blog_list', kwargs={'pk': self.profile.pk})
        )
        self.assertFalse(
            Blog.objects.filter(profile=self.profile).exists()
        )
        self.client.logout()


class PostDeleteViewTestCase(TestCase):
    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/blogs.json',
        'app_blog/fixtures/posts.json',
        'app_blog/fixtures/images.json',
    ]

    def setUp(self) -> None:
        self.random_post = choice(Post.objects.select_related('profile').all())
        self.url = reverse('app_blog:post_delete', kwargs={'pk': self.random_post.pk})
        self.bad_profile = choice(
            Profile.objects.prefetch_related('posts').exclude(pk=self.random_post.profile.pk).exclude(user__is_superuser=True)
        )

    def test_post_delete_unauthorized(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse('app_auth:login') + f'?next={self.url}'
        )

    def test_post_delete_forbidden(self):
        self.client.force_login(user=self.bad_profile.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()

    def test_post_delete(self):
        self.client.force_login(user=self.random_post.profile.user)
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.context.get('post'), self.random_post)

        soup = bs4.BeautifulSoup(get_response.content, 'lxml')
        name = 'csrfmiddlewaretoken'
        input_tag = soup.find('input', {'name': name})
        input_value = input_tag.get('value')
        blog_pk = self.random_post.blog.pk
        post_pk = self.random_post.pk

        put_response = self.client.post(self.url, {name: input_value})

        self.assertRedirects(
            put_response,
            reverse('app_blog:blog_detail', kwargs={'pk': blog_pk})
        )

        self.assertFalse(
            Post.objects.filter(pk=post_pk).exists()
        )


class PostCreateViewTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        username = ''.join(choices(ascii_letters, k=8))
        password = ''.join(choices(ascii_letters, k=8))
        cls.user = User.objects.create_user(username=username, password=password)
        profile = Profile(user=cls.user)
        profile.save()
        cls.profile = profile

        title = ''.join(choices(ascii_letters, k=128))
        description = ''.join(choices(ascii_letters, k=256))

        blog = Blog(profile=profile, title=title, description=description)
        blog.save()
        cls.blog = blog

        cls.bad_user = User.objects.create_user(username=f'{username}bad', password=password)
        Profile.objects.create(user=cls.bad_user)

        cls.images = []

        for i in range(3):
            image = PilImage.new('RGB', (100, 100))
            path_to_test_image = os.path.join(os.curdir, f'test-image-{i}.jpg')
            image.save(path_to_test_image)
            cls.images.append(path_to_test_image)

        cls.post_test_data = {
            'title': ''.join(choices(ascii_letters, k=128)),
            'tag': ''.join(choices(ascii_letters, k=70)),
            'content': ''.join(choices(ascii_letters, k=1000)),
        }

        cls.csv_file = 'csv_file.csv'
        with open(cls.csv_file, 'w') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(cls.post_test_data.values())


    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        for path in cls.images:
            os.remove(path)
        os.remove(cls.csv_file)
        cls.bad_user.delete()
        cls.blog.delete()
        cls.profile.delete()
        cls.user.delete()

    def setUp(self) -> None:
        self.url = reverse('app_blog:post_new', kwargs={'pk': self.blog.pk})

    def test_post_create(self):
        self.client.force_login(user=self.user)
        with open(self.images[0], 'rb') as img_0, \
             open(self.images[1], 'rb') as img_1, \
             open(self.images[2], 'rb') as img_2:
            self.post_test_data['images'] = [img_0, img_1, img_2]

            post_response = self.client.post(
                self.url,
                data=self.post_test_data,
            )

        new_post_query = Post.objects.filter(Q(title=self.post_test_data['title']) & Q(images__isnull=False))
        self.assertTrue(new_post_query.exists())

        new_post = new_post_query[0]
        self.assertEqual(new_post.images.count(), 3)

        new_url = reverse('app_blog:post_detail', kwargs={'pk': new_post.pk})
        self.assertRedirects(
            post_response,
            new_url
        )

        self.post_test_data.pop('images')
        self.client.logout()

    def test_post_create_csv(self):

        self.client.force_login(user=self.user)
        with open(self.csv_file, 'r') as file:
            post_response = self.client.post(
                self.url,
                {"file": file}
            )

        new_post_query = Post.objects.filter(
            Q(title=self.post_test_data['title']) & Q(images__isnull=True)
        )
        self.assertTrue(new_post_query.exists())

        new_url = reverse('app_blog:post_detail', kwargs={'pk': new_post_query[0].pk})
        self.assertRedirects(
            post_response,
            new_url
        )

        self.client.logout()

    def test_post_create_invalid_csv(self):
        self.client.force_login(user=self.user)
        with open(self.images[0], 'rb') as image:
            invalid_response = self.client.post(self.url, {'file': image})

        self.assertIsNotNone(invalid_response.context.get('error'))
        self.client.logout()

    def test_post_create_invalid_img(self):
        self.client.force_login(user=self.user)
        with open(self.csv_file, 'r') as file:
            invalid_response = self.client.post(
                self.url,
                {
                    'title': 'some title',
                    'content': 'some content',
                    'tag': 'some tag',
                    'images': file
                }
            )
        self.assertContains(invalid_response, 'errorlist')

        self.assertFalse(
            Post.objects.filter(title='some title').exists()
        )
        self.client.logout()

    def test_post_create_unauthorized(self):
        unauthorized_response = self.client.post(self.url, self.post_test_data)
        self.assertEqual(unauthorized_response.status_code, 302)
        self.assertRedirects(
            unauthorized_response,
            reverse('app_auth:login') + f'?next={self.url}'
        )

    def test_post_create_forbidden(self):
        self.client.force_login(user=self.bad_user)
        forbidden_response = self.client.post(self.url, self.post_test_data)
        self.assertEqual(forbidden_response.status_code, 403)
        self.client.logout()


class PostDetailViewTestCase(TestCase):

    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/blogs.json',
        'app_blog/fixtures/posts.json',
        'app_blog/fixtures/images.json',
    ]

    def setUp(self) -> None:
        self.random_post = choice(Post.objects.select_related('profile', 'blog').filter(is_published=True))
        self.url = reverse('app_blog:post_detail', kwargs={'pk': self.random_post.pk})
        self.urls_in_post = {
            reverse('app_blog:post_edit', kwargs={'pk': self.random_post.pk}),
            reverse('app_blog:post_delete', kwargs={'pk': self.random_post.pk}),
            reverse('app_blog:publish_or_archive', kwargs={'pk': self.random_post.pk})
        }

        self.bad_profile = choice(
            Profile.objects.prefetch_related('posts').exclude(pk=self.random_post.profile.pk).exclude(user__is_superuser=True)
        )

    def test_post_detail_unauthorized(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get('profile'))
        response_soup = bs4.BeautifulSoup(response.content, 'lxml')
        title = response_soup.find('h1').text
        self.assertEqual(self.random_post.title, title)

        for url in self.urls_in_post:
            self.assertNotContains(response, url)

    def test_post_detail_forbidden(self):
        self.client.force_login(user=self.bad_profile.user)
        self.random_post.archive()
        forbidden_response = self.client.get(self.url)
        self.assertEqual(forbidden_response.status_code, 403)
        self.client.logout()

    def test_post_detail(self):
        self.client.force_login(user=self.random_post.profile.user)
        response = self.client.get(self.url)
        self.assertEqual(response.context.get('profile'), self.random_post.profile)

        for url in self.urls_in_post:
            self.assertContains(response, url)

        self.client.logout()


class BlogEditViewTestCase(TestCase):
    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/blogs.json',
        'app_blog/fixtures/posts.json',
        'app_blog/fixtures/images.json',
    ]

    def setUp(self) -> None:
        self.random_blog = choice(Blog.objects.select_related('profile').all())
        self.url = reverse('app_blog:blog_edit', kwargs={'pk': self.random_blog.pk})

        self.bad_profile = choice(
            Profile.objects.prefetch_related('blogs').exclude(pk=self.random_blog.profile.pk).exclude(user__is_superuser=True)
        )

        self.data = {
            'title': ''.join(choices(ascii_letters, k=50)),
            'description': ''.join(choices(ascii_letters, k=200))
        }

    def test_blog_edit(self):
        self.client.force_login(user=self.random_blog.profile.user)
        old_title = self.random_blog.title
        wrong_response = self.client.post(self.url, {'title': self.data['title']})
        self.assertContains(wrong_response, 'errorlist')
        response = self.client.post(self.url, self.data)
        self.assertRedirects(response, reverse('app_blog:blog_detail', kwargs={'pk': self.random_blog.pk}))
        self.random_blog.refresh_from_db()
        self.assertFalse(self.random_blog.title == old_title)
        self.client.logout()

    def test_blog_edit_unauthorized(self):
        response = self.client.post(
            self.url,
            self.data
        )
        self.assertRedirects(
            response,
            reverse('app_auth:login') + f'?next={self.url}'
        )

    def test_blog_edit_forbidden(self):
        self.client.force_login(user=self.bad_profile.user)
        old_title = self.random_blog.title
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 403)
        self.random_blog.refresh_from_db()
        self.assertEqual(old_title, self.random_blog.title)


class PostEditViewTestCase(TestCase):
    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/blogs.json',
        'app_blog/fixtures/posts.json',
        'app_blog/fixtures/images.json',
    ]

    def setUp(self) -> None:
        self.random_post = choice(Post.objects.select_related('profile').filter(images__isnull=False))
        self.url = reverse('app_blog:post_edit', kwargs={'pk': self.random_post.pk})
        self.bad_profile = choice(
            Profile.objects.prefetch_related('posts').exclude(pk=self.random_post.profile.pk).exclude(user__is_superuser=True)
        )

        self.paths = [os.path.join(os.curdir, f'test-image-{i}.jpg') for i in range(3)]
        _ = [
            PilImage.new('RGB', (100, 100)).save(path)
            for path in self.paths
        ]

        self.test_data = {
            'title': ''.join(choices(ascii_letters, k=30)),
            'content': ''.join(choices(ascii_letters, k=100)),
            'tag': ''.join(choices(ascii_letters, k=10))
        }

    def tearDown(self) -> None:
        for path in self.paths:
            os.remove(path)

    def test_post_edit(self):
        self.client.force_login(user=self.random_post.profile.user)
        images_to_delete = Image.objects.filter(post=self.random_post).values_list('pk')
        update_data = {str(img[0]): 'on' for img in images_to_delete}
        new_test_data = self.test_data.copy()
        new_test_data.update(update_data)
        with ExitStack() as stack:
            images = [stack.enter_context(open(path, 'rb')) for path in self.paths]
            new_test_data['images'] = images
            response = self.client.post(self.url, new_test_data)

        self.assertRedirects(
            response,
            reverse('app_blog:post_detail', kwargs={'pk': self.random_post.pk})
        )
        self.random_post.refresh_from_db()

        images = Image.objects.filter(post=self.random_post)
        self.assertTrue(images.exists())
        self.assertEqual(images.count(), 3)

        self.assertFalse(
            Image.objects.filter(pk=choice(images_to_delete)[0]).exists()
        )
        self.client.logout()

    def test_post_edit_unauthorized(self):
        response = self.client.post(self.url, self.test_data)
        self.assertRedirects(
            response,
            reverse('app_auth:login') + f'?next={self.url}'
        )

    def test_post_edit_forbidden(self):
        self.client.force_login(user=self.bad_profile.user)
        response = self.client.post(self.url, self.test_data)
        self.assertEqual(response.status_code, 403)
        self.client.logout()


class PublishOrArchiveTestCase(TestCase):
    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/blogs.json',
        'app_blog/fixtures/posts.json',
    ]

    def setUp(self) -> None:
        self.random_post = choice(Post.objects.select_related('profile').all())
        self.url = reverse('app_blog:publish_or_archive', kwargs={'pk': self.random_post.pk})
        self.bad_profile = choice(
            Profile.objects.prefetch_related('posts').exclude(pk=self.random_post.profile.pk).exclude(user__is_superuser=True)
        )

    def test_publish_or_archive(self):
        self.client.force_login(user=self.random_post.profile.user)
        cur_status = self.random_post.is_published
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('app_blog:post_detail', kwargs={'pk': self.random_post.pk}))
        self.random_post.refresh_from_db()
        self.assertNotEqual(cur_status, self.random_post.is_published)
        self.client.logout()

    def test_publish_or_archive_unauthorized(self):
        cur_status = self.random_post.is_published
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            reverse('app_auth:login') + f'?next={self.url}'
        )
        self.random_post.refresh_from_db()
        self.assertEqual(cur_status, self.random_post.is_published)

    def test_publish_or_archive_forbidden(self):
        self.client.force_login(user=self.bad_profile.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()


class LatestPostsViewTestCase(TestCase):
    fixtures = [
        'app_auth/fixtures/users.json',
        'app_auth/fixtures/profiles.json',
        'app_blog/fixtures/blogs.json',
        'app_blog/fixtures/posts.json',
    ]

    def setUp(self) -> None:
        self.url = reverse('app_blog:posts_latest')
        self.publish_posts = Post.objects.filter(is_published=True)

    def test_latest_posts_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.publish_posts.count(), response.context.get('paginator').count)

    def test_latest_posts_view_context_profile(self):
        random_profile = choice(Profile.objects.all())
        self.client.force_login(user=random_profile.user)
        response = self.client.get(self.url)
        self.assertEqual(
            random_profile,
            response.context.get('profile')
        )






