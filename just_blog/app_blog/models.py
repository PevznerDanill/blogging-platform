from django.db import models
from django.utils.translation import gettext_lazy as _
from app_auth.models import Profile
import datetime
from django.utils.timezone import make_aware
from typing import Union
from django.shortcuts import reverse


class Blog(models.Model):
    """
    A model describing a Blog. Has a One-to-Many relationship with Profile.
    """
    class Meta:
        verbose_name_plural = _('blogs')
        verbose_name = _('blog')

    title = models.CharField(max_length=128, verbose_name=_('title'))
    description = models.CharField(max_length=256, verbose_name=_('description'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, verbose_name=_('profile'), related_name='blogs')

    def __str__(self) -> str:
        """
        Returns the title and the id of the blog.
        """
        return f'{self.title}#{self.pk}'


class Post(models.Model):
    """
    A model describing a Post. Has a One-to-Many relationship with Blog
    and Profile.
    """
    title = models.CharField(max_length=128, verbose_name=_('title'))
    tag = models.CharField(max_length=70, verbose_name=_('tag'))
    content = models.TextField(verbose_name=_('content'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('created at'))
    is_published = models.BooleanField(default=False, verbose_name=_('is published'))
    published_at = models.DateTimeField(verbose_name=_('published at'), null=True, blank=True)
    blog = models.ForeignKey(to=Blog, on_delete=models.CASCADE, related_name='posts', verbose_name=_('blog'))
    profile = models.ForeignKey(to=Profile, on_delete=models.CASCADE, related_name='posts', verbose_name=_('profile'))

    def __str__(self) -> str:
        """
        Returns the title of the post.
        """
        return self.title

    def short_title(self) -> Union[models.CharField, str]:
        """
        Returns the title with the length limit of 80 characters. If longer, returns
        a cut version.
        """
        if len(self.title) > 80:
            return f'{self.title[:80]}...'
        return self.title

    def publish(self) -> None:
        """
        Sets the is_publish value to True and sets the published_at value to the current moment.
        """
        self.is_published = True
        self.published_at = make_aware(datetime.datetime.now())
        self.save(force_update=['is_published', 'published_at'])

    def archive(self) -> None:
        """
        Sets the is_publish value to False and sets the published_at value to None.
        """
        self.is_published = False
        self.published_at = None
        self.save(force_update=['is_published', 'published_at'])

    def short_content(self) -> Union[models.TextField, str]:
        """
        If the content is more than 100 characters long, shortens it to this limit.
        """
        if len(self.content) > 100:
            return f'{self.content[:100]}... '
        return self.content

    def get_tag(self) -> str:
        """
        Adds # symbols to the tags and if then deletes the consecutive repetitions of them.
        """
        tag_parts = self.tag.split()
        tag = '#' + '#'.join(tag_parts)
        cleaned_tag = tag.replace('##', '#')
        return cleaned_tag

    def get_absolute_url(self) -> str:
        """
        Generates absolute url for the post's page.
        """
        return reverse('app_blog:post_detail', kwargs={'pk': self.pk})


class Image(models.Model):
    """
    A model to describe a Image.
    """
    title = models.CharField(max_length=20, verbose_name=_('title'))
    image = models.ImageField(upload_to='images/', verbose_name=_('image'))
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images', verbose_name=_('post'))

    class Meta:
        verbose_name = _('image')
        verbose_name_plural = _('images')


