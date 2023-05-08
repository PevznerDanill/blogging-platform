from django.contrib.syndication.views import Feed
from django.db.models import QuerySet
from django.shortcuts import reverse
from django.utils.feedgenerator import Atom1Feed
from app_blog.models import Post
from django.db.models import F
import re
from typing import Dict, Union
from django.contrib.sites.requests import RequestSite

class LatestPostsFeed(Feed):
    """
    A feed that shows the last five published posts.
    """
    title = 'Posts'
    link = '/siteposts/'
    description = 'The latest published posts'

    feed_type = Atom1Feed

    def items(self) -> QuerySet:
        """
        Retrieves five latest published Post instances.
        """
        return Post.objects.select_related('profile').annotate(profile_username=F('profile__user__username')).filter(is_published=True).order_by('-published_at')[:5]

    def item_title(self, item: Post) -> str:
        """
        Takes title field from the retrieved Post instance and deletes the last "." symbol.
        """
        return re.sub(r'\.\B', '', item.title)

    def item_description(self, item: Post) -> str:
        """
        Calls short_content() method of the retrieved current Post instance.
        """
        return item.short_content()

    def item_link(self, item: Post) -> str:
        """
        Uses the pk of the retrieved Post instance to generate a link to its page.
        """
        return reverse('app_blog:post_detail', kwargs={'pk': item.pk})

    def item_author_name(self, item: Post) -> str:
        """
        Returns the profile field (the Profile model has an __str__ method that returns the field user.username)
        of the retrieved Post instance.
        """
        return item.profile

    def get_context_data(self, **kwargs) -> Dict[str, Union[Post, RequestSite, QuerySet]]:
        """
        Adds 'latest_posts' key to the context with the passed items as a value.
        """
        context = super().get_context_data(**kwargs)
        context['latest_posts'] = self.items()
        return context
